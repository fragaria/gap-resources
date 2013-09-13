#!/usr/bin/env python

'''
simple shortcut for running nosetests via python
replacement for *.bat or *.sh wrappers
'''

import sys
import logging
from os.path import abspath, dirname

import nose

import src

import test_resources


def run_all(argv=None):
    sys.exitfunc = lambda msg = 'Process shutting down...': sys.stderr.write(msg + '\n')

    argv  = (set(argv) | {
        '--where=%s' % dirname(abspath(test_resources.__file__)),
        '--with-gae',
        '--gae-application=%s' % dirname(abspath(src.__file__)),
        '--verbose',
        '--without-sandbox',
        '--no-log-capture'
    }) - {'./run_tests.py'}

    logging.debug('Running tests with arguments: %r' % argv)

    nose.run_exit(
        argv=list(argv),
        defaultTest=abspath(dirname(__file__)),
    )

if __name__ == '__main__':
    run_all(sys.argv)
