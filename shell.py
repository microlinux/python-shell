from collections import namedtuple
from itertools import imap
from multiprocessing import Pool
from shlex import split
from subprocess import PIPE, Popen, STDOUT
from traceback import format_exc

""" Strips whitespace from command output.

Strips horizontal and vertical whitespace from command output and returns a
corresponding list.

@param  <list>  raw output
@return <list>  stripped output

"""
def strip_output(output):
  for i in range(0, len(output)):
    output[i] = output[i].strip()

  while output and not output[-1]:
    output.pop()

  while output and not output[0]:
    output.pop(0)

  return output

""" Parses a command result.

Parses a command result into a namedtuple and returns it.

@param  <list>        command string, retval, output
@return <namedtuple>  command string, retval, output

"""
def parse_result(result):
  return namedtuple("ResultTuple", ['command', 'retval', 'output'])._make(
                    [result[0], result[1], result[2]])

""" Command worker function.

Runs a command passed as a list of arguments. Requires /usr/bin/timeout.
Returns a list containing the command result.

@param  <list>  command string, timeout in seconds
@return <list>  command string, retval, stripped output

"""
def worker(job):
  output = []
  retval = None

  try:
    """ Fork the command, time out after x seconds. """
    proc = Popen(split('/usr/bin/timeout %s %s' % (job[1], str(job[0]))),
                 stdout=PIPE, stderr=STDOUT, close_fds=True)
    proc.wait()
  except OSError:
    """ Special case, /usr/bin/timeout not found. """
    retval = 255
    output = ['/usr/bin/timeout not found or not executable']
  except Exception, e:
    """ Special case, unexpected exception. """
    retval = 256
    output = format_exc().splitlines()
  finally:
    if retval != 255 and retval != 256:
      if proc.returncode == 124:
        """ Special case, command timed out. """
        retval = 124;
        output = ['command timed out']
      elif proc.returncode == 127:
        """ Special case, command not found or executable. """
        retval = 127
        output = ['command not found or not executable']
      else:
        """ Nothing unexpected happened, process result normally. """
        retval = proc.returncode
        try:
          output = proc.communicate()[0].splitlines()
        except Exception, e:
          """ Special case, unexpected exception. """
          retval = 257
          output = format_exc().splitlines()
          pass

    return [job[0], retval, strip_output(output)]

""" Executes a single command.

Runs a command and returns the result as a namedtuple.

@param  <str> command string
@param  <int> timeout in seconds
@return <namedtuple>  command string, retval, stripped output

"""
def command(command, timeout=10):
  assert type(command) is str, 'command is not a string'
  assert type(timeout) is int, 'timeout is not an integer'

  return parse_result(worker([command, timeout]))

""" Executes multiple commands concurrently.

Runs multiple commands concurrently in a pool of the given size. Returns a
generator that returns ordered namedtuples of results.

@param  <list>  command strings
@param  <int>   individual command timeout in seconds
@param  <int>   number of workers in pool
@return <generator> namedtuples - command string, retval, stripped output

"""
def multi_command(commands, timeout=10, workers=4):
  assert type(commands) is list, 'commands is not a list'
  for i in range(len(commands)):
    assert type(commands[i]) is str, 'commands[%s] is not a string' % i
  assert type(timeout) is int, 'timeout is not an integer'
  assert type(workers) is int, 'workers is not an integer'

  count = len(commands)

  """ No sense in having more workers than jobs. """
  if workers > count:
    workers = count

  """
  Pool.imap can only pass one argument to a worker. To get around this, put
  multiple arguments into a list.
  """
  for i in range(count):
    commands[i] = [commands[i], timeout]

  """ Fire up the pool, collect ordered results. """
  pool = Pool(processes=workers)
  results = pool.imap(worker, commands)

  """ Wait for all jobs to finish """
  pool.close()
  pool.join()

  return imap(parse_result, results)

""" Example usage. """
if __name__ == '__main__':
  print '---------------------'
  print 'Execute one command'
  print '---------------------'
  result = command('whoami', 2)
  print 'result.command: %s' % result.command
  print 'result.retval : %s' % result.retval
  print 'result.output : %s' % result.output
  print
  print '----------------------'
  print 'Execute two commands'
  print '----------------------'
  i = 0
  results = multi_command(['whoami', 'ping -c3 -i1 -W1 -q google.com'], 5)
  for result in results:
    print 'result%s.command: %s' % (i, result.command)
    print 'result%s.retval : %s' % (i, result.retval)
    print 'result%s.output : %s' % (i, result.output)
    print
    i = i + 1
  print '----------------------------------'
  print 'Execute one non-existent command'
  print '----------------------------------'
  result = command('/usr/bin/fake_binary_99 -f fake_opt', 2)
  print 'result.command: %s' % result.command
  print 'result.retval : %s' % result.retval
  print 'result.output : %s' % result.output
  print
  print '------------------------------------'
  print 'Execute one command that times out'
  print '------------------------------------'
  result = command('ping -c3 -i1 -W1 -q google.com', 2)
  print 'result.command: %s' % result.command
  print 'result.retval : %s' % result.retval
  print 'result.output : %s' % result.output
  print
  print '---------------------------------------------'
  print 'Execute three commands with varying results'
  print '---------------------------------------------'
  results = multi_command(['ls -l', '/usr/bin/fake_binary_99 -f fake_opt',
                           'ping -c3 -i1 -W1 -q google.com'], 2)
  i = 0
  for result in results:
    print 'result%s.command: %s' % (i, result.command)
    print 'result%s.retval : %s' % (i, result.retval)
    print 'result%s.output : %s' % (i, result.output)
    print
    i = i + 1