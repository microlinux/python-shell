#!/usr/bin/python

from sys import path
path.append('..')
from shell import multi_command

commands = []
i = 0

print
print 'Execute three commands with varying results'
print '-------------------------------------------'
results = multi_command(['ls -l', '/usr/bin/blurple -f opt',
                         'ping -c5 -i1 -W1 -q google.com'], 2)
for result in results:
  print 'result%s.command: %s' % (i, result.command)
  print 'result%s.retval : %s' % (i, result.retval)
  print 'result%s.output : %s' % (i, result.output)
  print
  i = i + 1
	
hosts = open('hosts.csv', 'r')
for host in hosts:
	commands.append('ping -c3 -i1 -W1 -q %s' % host.strip())
hosts.close()

print 'Execute 100 pings with 100 workers'
print '----------------------------------'
results = multi_command(commands, 5, 100)
for result in results:
	print result.command
	print result.retval
	print result.output
print