#!/usr/bin/env python3

import sys

valid_actions = ['client', 'server']

def choose_by_name(name):
    for a in valid_actions:
        if name[-len(a):] == a:
            return a

if __name__ == '__main__':
    action = choose_by_name(sys.argv[0])
    if not action:
        if len(sys.argv) < 2 or not sys.argv[1] in valid_actions:
            print('Please specify one of {{{}}}.'.format(', '.join(valid_actions)), file=sys.stderr)
            sys.exit(-1)
        else:
            action = sys.argv[1]
    
    try:
        a = __import__(action)
        a.run()
    except ImportError as e:
        print('Sorry, "{}" is not available on this system'.format(action), file=sys.stderr)