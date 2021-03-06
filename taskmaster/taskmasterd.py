import os
import argparse
import yaml
import re
import sys
import signal

from .program import Program
from .sock	import ServerManager
from .log	import Log
from .controller import Controller
from .log import Log
from .var import PID_FILE, LOCK_FILE, Global
from .signal import setSignal, parse_config
from .programParse import parseConfig

def already_running():
	try:
		with open(PID_FILE) as f:
			pid = int(next(f))
		os.kill(pid, 0)
		Log.Warning('A taskmater deamon is already running')
		return True
	except:
		return False

def daemonize():
	r, w = os.pipe()
	pid = os.fork()
	if pid != 0:
		os.close(w)
		r = os.fdopen(r)
		r.read()
		exit()
	else:
		os.close(r)
		w = os.fdopen(w, 'w')
		os.setsid()
		pid = os.fork()
		if pid != 0:
			exit()
		else:
			null = open('/dev/null', 'r+')
			os.dup2(null.fileno(), sys.stdin.fileno())
			os.dup2(null.fileno(), sys.stdout.fileno())
			os.dup2(null.fileno(), sys.stderr.fileno())
			os.umask(0)
			os.chdir('/')
			with open(PID_FILE, 'w+') as stream:
				stream.write(str(os.getpid()))
			w.write("Parent can leave")
			w.close()
	return

def parseCommand(cmd):
	reCmd = re.match(r'(?P<cmd>[a-z]*)(?: {1,})(?P<arg>[a-zA-Z0-9_]{1,})', cmd)
	if not reCmd:
		return None
	if reCmd.group('cmd') not in ['stop', 'start', 'status', 'reload', 'restart']:
		return None
	return reCmd

def startServer():
	server = ServerManager()
	controller = Controller(Global.program_list)
	while True:
		server.listen()
		while True:
			cmd = server.getCommand()
			if not cmd:
				break
			reCmd = parseCommand(cmd)
			if not reCmd:
				server.respond(b'')
				continue
			command = reCmd.group('cmd')
			arg = reCmd.group('arg')
			response = getattr(controller, command)(arg)
			server.respond(response.encode())
			if (command == 'stop' and arg == 'main'):
				Log.Info('Stop main program.')
				exit(0)

def runPrograms(listOptions):
	for options in listOptions:
		Global.program_list[options.name] = Program(options)

def main():
	if already_running():
		exit(1)
	Log.Info(f'Start {sys.argv}')
	parser = argparse.ArgumentParser(description='Taskmaster daemon')
	parser.add_argument('-c', '--config', type=argparse.FileType('r', encoding='utf-8'), required=True, help='Defines the configuration file to read')
	args = parser.parse_args()

	Global.CONFIG_FILE = args.config.name
	if not re.match(r'^/', args.config.name):
		Global.CONFIG_FILE = '/'.join([os.getcwd(), args.config.name])
	config = parse_config()
	if not config:
		Log.Warning('Config file empty, exiting...')
		return 1
	try:
		listOptions = parseConfig(config)
	except Exception as e:
		Log.Error('Fail to parse: ', e)
		exit(1)

	daemonize()
	setSignal()
	runPrograms(listOptions)
	startServer()