#!/usr/bin/python

from sys import path
path.append('..')
from shell import command

print
print 'Execute a command that succeeds'
print '-------------------------------'
result = command('ls -l', 2)
print 'result.command: %s' % result.command
print 'result.retval : %s' % result.retval
print 'result.runtime : %s' % result.runtime
print 'result.output : %s' % result.output
print
print 'Execute a command that doesn\'t exist'
print '------------------------------------'
result = command('/usr/bin/blurple -f opt', 2)
print 'result.command: %s' % result.command
print 'result.retval : %s' % result.retval
print 'result.runtime : %s' % result.runtime
print 'result.output : %s' % result.output
print
print 'Execute a command that times out'
print '--------------------------------'
result = command('ping -c5 -i1 -W1 -q google.com', 2)
print 'result.command: %s' % result.command
print 'result.retval : %s' % result.retval
print 'result.runtime : %s' % result.runtime
print 'result.output : %s' % result.output
print