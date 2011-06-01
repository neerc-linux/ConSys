"""
Automata-related code
@author: Nikita Ofitserov
"""
import logging

_log = logging.getLogger(__name__)

class SimpleAutomaton(object):
    def __init__(self):
        self._state = self._start_state
        
    def event(self, event):
        key = (self._state, event)
        if not key in self._transitions:
            raise NameError('No transition from "{0}" on '
                            'event "{1}" exists'.format(self._state, event))
        newState, methods = self._transitions[key]
        _log.info('Transition "{0}" -> "{1}" on event '
                  '"{2}"'.format(self._state, newState, event))
        for method in methods:
            getattr(self, method)()
        self._state = newState
        
