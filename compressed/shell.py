from collections import namedtuple
from itertools import imap
from multiprocessing import Pool
from shlex import split
from subprocess import PIPE, Popen, STDOUT
def strip_output(output):
  for i in range(0, len(output)):
   output[i] = output[i].strip()
  while output and not output[-1]:
    output.pop()
  while output and not output[0]:
    output.pop(0)
  return output
def parse_result(result):
  return namedtuple("ResultTuple", ['command', 'retval', 'output'])._make([result[0], result[1], result[2]])
def worker(job):
  retval = None
  output = []
  try:
    proc = Popen(split('/usr/bin/timeout %s %s' % (job[1], str(job[0]))), stdout=PIPE, stderr=STDOUT, close_fds=True)
    proc.wait()
  except OSError:
    retval = 255
    output = ['/usr/bin/timeout not found or not executable']
  except Exception, e:
    retval = 256
    output = '%s' % e
    output = strip_output(output.split('\n'))
  finally:
    if retval != 255 and retval != 256:
      if proc.returncode == 124:
        retval = 124;
        output = ['command timed out']
      elif proc.returncode == 127:
        retval = 127
        output = ['command not found or not executable']
      else:
        retval = proc.returncode
        try:
          output = strip_output(proc.communicate()[0].split('\n'))
        except Exception, e:
          retval = 257
          output = '%s' % e
          output = strip_output(output.split('\n'))
          pass
    return [job[0], retval, output]
def command(command, timeout=10):
  assert type(command) is str, 'command is not a string'
  assert type(timeout) is int, 'timeout is not an integer'
  result = worker([command, timeout])
  return parse_result(result)
def multi_command(commands, timeout=10, workers=4):
  assert type(commands) is list, 'commands is not a list'
  for i in range(len(commands)):
    assert type(commands[i]) is str, 'commands[%s] is not a string' % i
  assert type(timeout) is int, 'timeout is not an integer'
  assert type(workers) is int, 'workers is not an integer'
  count = len(commands)
  result_tuples = []
  if workers > count:
    workers = count
  for i in range(count):
    commands[i] = [commands[i], timeout]
  pool = Pool(processes=workers)
  results = pool.imap(worker, commands)
  pool.close()
  pool.join()
  return imap(parse_result, results