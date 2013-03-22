shell
=====

provides functions to execute a single shell command, or a group of shell
commands concurrently

----------------------------------
shell.command(command, [timeout])
----------------------------------
Executes a single command with a timeout. Takes two arguments, the command to
excecute and an optional timeout in seconds. Default timeout is 30 seconds.

result = shell.command('whoami', 5)

result will be a namedtuple containing the command string, tokens, retval and
output. Output is a list of lines stripped of leading/trailing blank lines and
horizontal whitespace. On timeout, retval is -15 and output is empty.

print result.command
print result.tokens
print result.retval
print result.output

-----------------------------------------
shell.multi_command(commands, [timeout])
-----------------------------------------
Executes multiple commands concurrently. Takes two arguments, a list of commands
to execute and and an optional individual command timeout in seconds. Default
timeout is 30 seconds.

results = shell.command(['ping -c5 -i1 google.com', 'whoami'], 5)

results will be a list of namedtuples, as in shell.command. Results are ordered
to match the given list of commands.

for result in results:
  print result.command
  print result.tokens
  print result.retval
  print result.output