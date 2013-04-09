""" shell

version 1.2-20130408
https://github.com/microlinux/python-shell

Module for easily executing shell commands and retreiving their results in a
normalized manner.

See https://github.com/microlinux/python-shell/blob/master/README.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, version 3.

"""
from collections import namedtuple
from itertools import imap
from multiprocessing import Pool
from shlex import split
from subprocess import PIPE, Popen, STDOUT
from threading import Timer
from time import time
from traceback import format_exc

""" shell.strip_command_output()

Strips horizontal and vertical whitespace from a list of lines. Returns
the result as a list.

@param  <list>  [str] lines

@return <list>  [str] lines

"""
def strip_command_output(lines):
  if len(lines) > 0:
    for i in range(len(lines)):
      lines[i] = lines[i].strip()

    while lines and not lines[-1]:
      lines.pop()

    while lines and not lines[0]:
      lines.pop(0)

  return lines

""" shell.parse_command_result()

Parses a command result into a namedtuple. Returns the namedtuple.

@param  <list>  [str] command, [int] pid, [int] retval, [float] runtime,
                [list] output

@return <namedtuple>  [str] command, [int] pid, [int] retval,
                      [float] runtime, [list] output

"""
def parse_command_result(result):
  return namedtuple('ResultTuple', ['command', 'pid', 'retval', 'runtime',
                    'output'])._make([result[0], result[1], result[2],
                    result[3], result[4]])

""" shell.command_worker()

Executes a command with a timeout. Returns the result as a list.

@param  <list>  [str] command, [int|float] secs before timeout

@return <list>  [str] command, [int] pid, [int] retval,
                [float] runtime/secs, [list] output

"""
def command_worker(command):
  kill = lambda this_proc: this_proc.kill()
  output = []
  pid = None
  retval = None
  runtime = None
  start = time()

  try:
    proc = Popen(split('%s' % str(command[0])), stdout=PIPE, stderr=STDOUT)
    timer = Timer(command[1], kill, [proc])

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

    return [command[0], pid, retval, runtime, strip_command_output(output)]

""" shell.command()

Executes a command with a timeout. Returns the result as a namedtuple.

@param  <str>       command
@param  <int|float> secs before timeout (10)

@return <namedtuple>  [str] command, [int] pid, [int] retval,
                      [float] runtime, [list] output

"""
def command(command, timeout=10):
  if not isinstance(command, str):
    raise TypeError('command is not a string')
  elif not isinstance(timeout, int) and not isinstance(timeout, float):
    raise TypeError('timeout is not an integer or float')

  return parse_command_result(command_worker([command, timeout]))

""" shell.multi_command()

Executes multiple commands concurrently with individual timeouts in a pool
of workers. Returns ordered results as a namedtuple generator.

@param  <list>      [str] commands
@param  <int|float> secs before individual timeout (10)
@param  <int>       max workers (4)

@return <generator> <namedtuple> [str] command, [int] pid, [int] retval,
                                 [float] runtime, [list] output

"""
def multi_command(commands, timeout=10, workers=4):
  if not isinstance(commands, list):
    raise TypeError('commands is not a list')

  for i in range(len(commands)):
    if not isinstance(commands[i], str):
      raise TypeError('commands[%s] is not a string' % i)

  if not isinstance(timeout, int) and not isinstance(timeout, float):
    raise TypeError('timeout is not an integer or float')
  elif not isinstance(workers, int):
    raise TypeError('workers is not an integer')

  count = len(commands)

  if workers > count:
    workers = count

  for i in range(count):
    commands[i] = [commands[i], timeout]

  pool = Pool(processes=workers)
  results = pool.imap(command_worker, commands)

  pool.close()
  pool.join()

  return imap(parse_command_result, results)