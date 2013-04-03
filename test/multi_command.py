#!/usr/bin/python

from sys import path
path.append('../')
from shell import multi_command

i = 0
print
print 'Execute three commands with varying results:'
print '--------------------------------------------'
results = multi_command(['ls -l', '/usr/bin/blurple -f opt',
                         'ping -c5 -i1 -W1 -q google.com'], 2)
for result in results:
  print 'result%s.command: %s' % (i, result.command)
  print 'result%s.retval : %s' % (i, result.retval)
  print 'result%s.output : %s' % (i, result.output)
  print
  i = i + 1