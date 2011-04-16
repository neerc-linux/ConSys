''' A generic scheduler for asynchronous processing.
@author: Nikita Ofitserov
'''

from __future__ import unicode_literals

import logging
import threading
from time import sleep

from consys.common import configuration

__all__ = ['schedule']

config = configuration.register_section('scheduler', 
    {
        'thread-pool-size': 'integer(min=1, default=5)',
    })

log = logging.getLogger(__name__)

def schedule(self, task, args=()):
    '''Schedules the call and returns a future'''
    future = Future()
    log.debug('Scheduling task {0}...'.format(future))
    self.pool.queueTask(task, args, future.callback)
    return future
        
class Future:
    def __init__(self):
        self.event = threading.Condition(threading.Lock())
        self.ready = False 
        self.retval = None
    
    def callback(self, retval):
        self.event.acquire()
        try:
            log.debug('Task {0} completed'.format(self))
            self.retval = retval
            self.ready = True
            self.event.notify_all()
        finally:
            self.event.release()
            
    def get_result(self):
        self.event.acquire()
        try:
            while not self.ready: 
                self.event.wait()
            return self.retval
        finally:
            self.event.release()
                    
class ThreadPool:
    '''Flexible thread pool class.  Creates a pool of threads, then
    accepts tasks that will be dispatched to the next available
    thread.'''
    
    def __init__(self, numThreads):
        '''Initialize the thread pool with numThreads workers.'''
        
        self.__threads = []
        self.__resizeLock = threading.Condition(threading.Lock())
        self.__taskLock = threading.Condition(threading.Lock())
        self.__tasks = []
        self.__isJoining = False
        self.setThreadCount(numThreads)

    def setThreadCount(self, newNumThreads):
        ''' External method to set the current pool size.  Acquires
        the resizing lock, then calls the internal version to do real
        work.'''
        
        # Can't change the thread count if we're shutting down the pool!
        if self.__isJoining:
            return False
        
        self.__resizeLock.acquire()
        try:
            self.__setThreadCountNolock(newNumThreads)
        finally:
            self.__resizeLock.release()
        return True

    def __setThreadCountNolock(self, newNumThreads):
        '''Set the current pool size, spawning or terminating threads
        if necessary.  Internal use only; assumes the resizing lock is
        held.'''
        
        # If we need to grow the pool, do so
        while newNumThreads > len(self.__threads):
            newThread = ThreadPoolThread(self)
            self.__threads.append(newThread)
            newThread.start()
        # If we need to shrink the pool, do so
        while newNumThreads < len(self.__threads):
            self.__threads[0].goAway()
            del self.__threads[0]

    def getThreadCount(self):
        '''Return the number of threads in the pool.'''
        
        self.__resizeLock.acquire()
        try:
            return len(self.__threads)
        finally:
            self.__resizeLock.release()

    def queueTask(self, task, args=(), taskCallback=None):
        '''Insert a task into the queue.  task must be callable;
        taskCallback can be None.'''
        
        if self.__isJoining == True:
            return False
        if not callable(task):
            return False
        
        self.__taskLock.acquire()
        try:
            self.__tasks.append((task, args, taskCallback))
            return True
        finally:
            self.__taskLock.release()

    def getNextTask(self):
        ''' Retrieve the next task from the task queue.  For use
        only by ThreadPoolThread objects contained in the pool.'''
        
        self.__taskLock.acquire()
        try:
            if self.__tasks == []:
                return (None, None, None)
            else:
                return self.__tasks.pop(0)
        finally:
            self.__taskLock.release()
    
    def joinAll(self, waitForTasks = True, waitForThreads = True):

        ''' Clear the task queue and terminate all pooled threads,
        optionally allowing the tasks and threads to finish.'''
        
        # Mark the pool as joining to prevent any more task queueing
        self.__isJoining = True

        # Wait for tasks to finish
        if waitForTasks:
            while self.__tasks != []:
                sleep(.1)

        # Tell all the threads to quit
        self.__resizeLock.acquire()
        try:
            self.__setThreadCountNolock(0)
            self.__isJoining = True

            # Wait until all threads have exited
            if waitForThreads:
                for t in self.__threads:
                    t.join()
                    del t

            # Reset the pool for potential reuse
            self.__isJoining = False
        finally:
            self.__resizeLock.release()

        
class ThreadPoolThread(threading.Thread):
    ''' A pooled thread class. '''
    
    threadSleepTime = 0.1

    def __init__(self, pool):
        ''' Initialize the thread and remember the pool. '''
        
        threading.Thread.__init__(self)
        self.__pool = pool
        self.__isDying = False
        
    def run(self):
        ''' Until told to quit, retrieve the next task and execute
        it, calling the callback if any.  '''
        
        while self.__isDying == False:
            cmd, args, callback = self.__pool.getNextTask()
            # If there's nothing to do, just sleep a bit
            if cmd is None:
                sleep(ThreadPoolThread.threadSleepTime)
            elif callback is None:
                cmd(*args)
            else:
                callback(cmd(*args))
    
    def goAway(self):
        ''' Exit the run loop next time through.'''
        
        self.__isDying = True

pool = ThreadPool(config['thread-pool-size'])
