from collections import namedtuple
from multiprocessing import Process, Queue
from shlex import split
from subprocess import PIPE, Popen, STDOUT
from threading import Timer
from time import sleep

"""
@desc	strip leading/trailing blank lines and horizontal whitespace from a list
			of lines, helpful for mechanized processing

@param	<list>	lines

@return	<list>	formatted list
"""
def format_output(output):
	num_lines = len(output)
	begin = 0
	end = 0

	if num_lines > 0:
		# find index of first non-blank line
		for i in range(0, num_lines):
			if output[i].strip():
				begin = i
				break

		# find index of last non-blank line
		for i in range(num_lines - 1, -1, -1):
			if output[i].strip():
				end = i + 1
				break

		# slice off leading/trailing blank lines
		output = output[begin:end];

		# strip horizontal whitespace
		for i in range(0, len(output)):
			output[i] = output[i].strip()

	return output

"""
@desc	dual purpose command forker; if given a queue, place result into it as a 
			list, else return a namedtuple (see below, list follows same order)
			
			command	<str>		command to execute
			tokens	<list>	tokenized command
			retval 	<int>		command retval (-15 on timeout)
			output	<list>	output parsed by format_output() (empty on timeout)

@param	<str>						command to execute
@param	<int>						timeout in seconds (default: 30)
@param	Process.Queue		optional queue to place result in
@param	<int>						required only if queue is given, index in list of
												commands given to multi_command

@return	NamedTuple|None namedtuple of result or None, depending if queue was 
												given
"""
def command(command, timeout=30, queue=None, index=None):
	tokens = split(command)

	# fork command
	proc = Popen(tokens, stdout=PIPE, stderr=STDOUT, close_fds=True)

	# setup and start timer
	kill = lambda p: p.terminate()
	timer = Timer(timeout, kill, [proc])
	timer.start()

	# get output
	output = proc.communicate()[0].split('\n')

	# cancel timer, command finished before timeout
	timer.cancel()

	output = format_output(output)

	# determine out how function is being used and take appropriate action with
	# the result
	if queue:
		queue.put([index, [command, tokens, proc.returncode, output]])
		return None
	else:
		return namedtuple("ResultTuple", ['command', 'tokens', 'retval', 'output'])._make([command, tokens, proc.returncode, output])

"""
@desc	forks mutilple shell commands concurrently and returns a list of results
			as namedtuples in the same order as the commands were given

@param	<list>	commands to execute
@param	<int>		individual command timeout in seconds (default: 30)

@return	<list> command results
"""
def multi_command(commands, timeout=30):
	num_cmds = len(commands)
	queue = Queue()
	procs = []
	
	# pre-create result list indexes since we may need to access them out-of-order
	# when populating it
	results = [None] * num_cmds

	# fork and start commands
	for i in range(0, num_cmds):
		# since commands can complete out of order, pass the index of the command
		# from the given list so we can re-order results to match
		procs.append(Process(target=command, args=(commands[i], timeout, queue, i)))
		procs[i].start()

	# get results
	for i in range(0, num_cmds):
		result = queue.get()
		results[int(result[0])] = namedtuple("ResultTuple", ['command', 'tokens', 'retval', 'output'])._make([result[1][0], result[1][1], result[1][2],result[1][3]])
		
	# signals main process that subprocesses are finished
	for i in range(0, num_cmds):
		procs[i].join();

	return results