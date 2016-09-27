"""Functions for executing one shell command and multiple, concurrent shell commands.

Repository:
    https://github.com/microlinux/python-shell

Author:
    Todd Mueller <firstname@firstnamelastname.com>

License:
    This program is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation, version 3. See https://www.gnu.org/licenses/.

"""

import collections
import multiprocessing
import shlex
import subprocess
import threading
import time
import traceback

CommandResult = collections.namedtuple('CommandResult', ['cmd', 'pid', 'retval', 'runtime', 'stdout', 'stderr'])
"""Namedtuple representing the result of a shell command.

Fields:
    cmd (str): command executed
    pid (int): process id
    retval (int): return value
    runtime (int): runtime in msecs
    stdout (str): stdout buffer, horizontal/vertical whitespace stripped
    stderr (str): stderr buffer, horizontal/vertical whitespace stripped

"""

def stripper(string):
    """Sexily strips horizontal and vertical whitespace from a string.

    Args:
        string (str): string to strip

    Returns:
        str: stripped string

    """

    lines = map(str.strip, string.splitlines())

    while lines and not lines[-1]:
        lines.pop()

    while lines and not lines[0]:
        lines.pop(0)

    return '\n'.join(lines)

def command(cmd, timeout=10, stdin=None):
    """Executes one shell command and returns the result.

    Args:
        cmd (str): command to execute
        timeout (int): timeout in seconds (10)
        stdin (str): input (None)

    Returns:
        CommandResult: result of command

    """

    kill = lambda this_proc: this_proc.kill()
    pid = None
    retval = None
    runtime = None
    stderr = None
    stdout = None

    try:
        start = time.time() * 1000.0
        proc = subprocess.Popen(shlex.split(cmd),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                close_fds=True,
                                shell=False)

        timer = threading.Timer(timeout, kill, [proc])

        timer.start()
        stdout, stderr = map(stripper, proc.communicate(input=stdin))
        timer.cancel()

        runtime = int((time.time() * 1000.0) - start)
    except OSError:
        retval = 127
        stderr = 'command not found'
    except:
        retval = 255
        stderr = traceback.format_exc()
    finally:
        if retval == None:
            if proc.returncode == -9:
                retval = 254
                stderr = 'command timed out'
            else:
                retval = proc.returncode

            pid = proc.pid

    return CommandResult(cmd, pid, retval, runtime, stdout, stderr)

def command_wrapper(args):
    """Wrapper used my multi_command to pass command arguments as a list."""

    return command(*args)

def multi_command(cmds, timeout=10, stdins=None, workers=4):
    """Executes multiple shell commands concurrently and returns the results.

    If stdins is given, its length must match that of cmds. If commands do
    not require input, their corresponding stdin field must be None.

    Args:
        cmds (list): commands to execute
        timeout (int): timeout in seconds per command (10)
        workers (int): max concurrency (4)
        stdins (list): inputs (None)

    Returns:
        CommandResult generator: results of commands in given order

    """

    num_cmds = len(cmds)

    if stdins != None:
        if len(stdins) != num_cmds:
            raise RuntimeError("stdins length doesn't match cmds length")

    if workers > num_cmds:
        workers = num_cmds

    for i in xrange(num_cmds):
        try:
            stdin = stdins[i]
        except:
            stdin = None

        cmds[i] = (cmds[i], timeout, stdin)

    pool = multiprocessing.Pool(processes=workers)
    results = pool.imap(command_wrapper, cmds)

    pool.close()
    pool.join()

    return results

def test(single_cmds=['ls -l', 'uptime', 'blargh'],
         multi_cmds=['ls -l', 'uptime', 'ping -c3 -i1 -W1 google.com']):
    """Demonstrates command and multi_command functionality.

    Args:
        single_cmds (list): commands to run one at a time
        multi_cmds (list): commands to run concurrently

    """

    print
    print '-----------------------'
    print 'Running single commands'
    print '-----------------------'

    for cmd in single_cmds:
        result = command(cmd)
        print
        print 'cmd: %s' % result.cmd
        print 'pid: %s' % result.pid
        print 'ret: %s' % result.retval
        print 'run: %s' % result.runtime
        print 'out:'
        print result.stdout
        print 'err:'
        print result.stderr

    print
    print '-------------------------'
    print 'Running multiple commands'
    print '-------------------------'

    for result in multi_command(multi_cmds):
        print
        print 'cmd: %s' % result.cmd
        print 'pid: %s' % result.pid
        print 'ret: %s' % result.retval
        print 'run: %s' % result.runtime
        print 'out:'
        print result.stdout
        print 'err:'
        print result.stderr
