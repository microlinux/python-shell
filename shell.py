""" 1.1_BETA-20130402 """

from collections import namedtuple
from itertools import imap
from multiprocessing import Pool
from shlex import split
from subprocess import PIPE, Popen, STDOUT
from threading import Timer
from traceback import format_exc

""" Strips whitespace from command output.

Strips horizontal and vertical whitespace from command output. Returns the
result as a list.

@param  <list>  raw output
@return <list>  stripped output

"""
def strip_output(output):
  if len(output) > 0:
    for i in range(len(output)):
      output[i] = output[i].strip()

    while output and not output[-1]:
      output.pop()

    while output and not output[0]:
      output.pop(0)

  return output

""" Parses a command result.

Parses a command result into a namedtuple. Returns the namedtuple.

@param  <list>  command string, retval, output
@return <namedtuple>  command string, retval, output

"""
def parse_result(result):
  return namedtuple("ResultTuple", ['command', 'retval', 'output'])._make(
                    [result[0], result[1], result[2]])

""" Command worker function.

Runs a command passed as a list of arguments. Returns the result as a list.

@param  <list>  command string, timeout in seconds
@return <list>  command string, retval, stripped output

"""
def worker(job):
  output = []
  retval = None

  try:
    """ Setup the kill function used in the timer. """
    kill = lambda this_proc: this_proc.kill()

    """ Fork the command and get output. """
    proc = Popen(split('%s' % str(job[0])), stdout=PIPE, stderr=STDOUT,
                       close_fds=True)
    timer = Timer(job[1], kill, [proc])
    timer.start()
    output = proc.communicate()[0].splitlines()
    timer.cancel()
  except OSError:
    """ Command not found. """
    retval = 127
    output = ['command not found']
  except Exception, e:
    """ Unexpected exception. """
    retval = 257
    output = format_exc().splitlines()
  finally:
    if retval == None:
      if proc.returncode == -9:
        """ Command timed out. """
        retval =  256
        output = ['command timed out']
      else:
        retval = proc.returncode

    return [job[0], retval, strip_output(output)]

""" Executes a command.

Executes a command with a timeout. Returns the result as a namedtuple.

@param  <str> command string
@param  <int> timeout in seconds
@return <namedtuple>  command string, retval, stripped output

"""
def command(command, timeout=10):
  assert type(command) is str, 'command is not a string'
  assert type(timeout) is int, 'timeout is not an integer'

  return parse_result(worker([command, timeout]))

""" Executes commands concurrently.

Executes commands concurrently with individual timeouts in a pool of
workers. Returns ordered results as a namedtuple generator.

@param  <list>  command strings
@param  <int>   individual command timeout in seconds
@param  <int>   number of workers in pool
@return <generator> command string, retval, stripped output

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
  Pool.imap() can only pass one argument to a worker. To get around this,
  put multiple arguments into a list.
  """
  for i in range(count):
    commands[i] = [commands[i], timeout]

  """ Fire up the pool, create a generator with ordered results. """
  pool = Pool(processes=workers)
  results = pool.imap(worker, commands)

  """ Wait for all jobs to finish. """
  pool.close()
  pool.join()

  return imap(parse_result, results)