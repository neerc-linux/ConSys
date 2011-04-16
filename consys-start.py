#!/usr/bin/env python2

from __future__ import print_function
from __future__ import unicode_literals

import sys

valid_actions = ['client', 'server']

def choose_by_name(name):
    for a in valid_actions:
        if name.endswith(a):
            return a
    return None

if __name__ == '__main__':
    action = choose_by_name(sys.argv[0])
    if not action:
        if len(sys.argv) < 2 or not sys.argv[1] in valid_actions:
            print('Please specify one of '
                  '{{{0}}}.'.format(', '.join(valid_actions)),
                  file=sys.stderr)
            sys.exit(-1)
        else:
            action = sys.argv[1]
            sys.argv = sys.argv[0:1] + sys.argv[2:]
    
    try:
        # FIXME when migrating to Python 3!
        a = __import__('consys.' + action, fromlist=[b'run'])
        a.run()
    except ImportError as e:
        print('Sorry, \'{0}\' is not available on this system'.format(action),
              file=sys.stderr)
