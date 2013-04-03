""" 1.1_BETA-20130402 """
""" https://github.com/microlinux/python-shell """
from collections import namedtuple
from itertools import imap
from multiprocessing import Pool
from shlex import split
from subprocess import PIPE, Popen, STDOUT
from threading import Timer
from time import time
from traceback import format_exc
def strip_output(output):
  if len(output) > 0:
    for i in range(len(output)):
      output[i] = output[i].strip()
    while output and not output[-1]:
      output.pop()
    while output and not output[0]:
      output.pop(0)
  return output
def parse_result(result):
  return namedtuple("ResultTuple", ['command', 'pid', 'retval', 'runtime',
                    'output'])._make([result[0], result[1], result[2],
                    result[3], result[4]])
def worker(job):
  output = []
  pid = None
  retval = None
  runtime = None
  try:
    kill = lambda this_proc: this_proc.kill()
    start = time()
    proc = Popen(split('%s' % str(job[0])), stdout=PIPE, stderr=STDOUT)
    timer = Timer(job[1], kill, [proc])
    timer.start()
    output = proc.communicate()[0].splitlines()
    timer.cancel()
    runtime = round(time() - start, 3)
  except OSError:
    retval = 127
    output = ['command not found']
  except Exception, e:
    retval = 257
    output = format_exc().splitlines()
  finally:
    if retval == None:
      if proc.returncode == -9:
        output = ['command timed out']
      pid = proc.pid
      retval = proc.returncode
    return [job[0], pid, retval, runtime, strip_output(output)]
def command(command, timeout=10):
  assert type(command) is str, 'command is not a string'
  assert type(timeout) is int, 'timeout is not an integer'
  return parse_result(worker([command, timeout]))
def multi_command(commands, timeout=10, workers=4):
  assert type(commands) is list, 'commands is not a list'
  for i in range(len(commands)):
    assert type(commands[i]) is str, 'commands[%s] is not a string' % i
  assert type(timeout) is int, 'timeout is not an integer'
  assert type(workers) is int, 'workers is not an integer'
  count = len(commands)
  if workers > count:
    workers = count
  for i in range(count):
    commands[i] = [commands[i], timeout]
  pool = Pool(processes=workers)
  results = pool.imap(worker, commands)
  pool.close()
  pool.join()
  return imap(parse_result, results)