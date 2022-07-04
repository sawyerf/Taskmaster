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
from .files import PID_FILE
from .files import LOCK_FILE

def parse_config() -> dict:
	with open(config_file_name) as stream:
		try:
			config = yaml.safe_load(stream)
			return config
		except yaml.YAMLError as exc:
			Log.Error(f'Error while loading config file')

def reload_config(signum, frame):
	Log.Info('Reloading config file')
	config = parse_config()
	if 'programs' in config.keys():
		if not config['programs']:
			Log.Warning('No program found, exiting...')
			return 1
		for program in config['programs']:
			if program == "taskmasterd":
				Log.Error("Invalid program name : taskmasterd")
			if not config['programs'][program]:
				Log.Error(f'Error in configuration file, program {program} should not be empty')
				return 1
			if program not in program_list:
				program_list[program] = Program(config['programs'][program], program)
			else:
				program_list[program].reload(config['programs'][program])

def already_running():
	try:
		with open(PID_FILE) as f:
			pid = int(next(f))
		os.kill(pid, 0)
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
			# os.dup2(null.fileno(), sys.stdin.fileno())
			# os.dup2(null.fileno(), sys.stdout.fileno())
			# os.dup2(null.fileno(), sys.stderr.fileno())
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

def main():
	global program_list
	program_list = dict()

	if already_running():
		exit(1)
	Log.Info(f'Start {sys.argv}')
	parser = argparse.ArgumentParser(description='Taskmaster daemon')
	parser.add_argument('-c', '--config', type=argparse.FileType('r', encoding='utf-8'), required=True, help='Defines the configuration file to read')
	args = parser.parse_args()
	global config_file_name
	config_file_name = '/'.join([os.getcwd(), args.config.name])
	config = parse_config()
	if not config:
		Log.Warning('Config file empty, exiting...')
		return 1

	daemonize()
	if 'programs' in config.keys():
		if not config['programs']:
			Log.Warning('No program found, exiting...')
			return 1
		for program in config['programs']:
			if program == "taskmasterd":
				Log.Error("Invalid program name : taskmasterd")
			if not config['programs'][program]:
				Log.Error(f'Error in configuration file, program {program} should not be empty')
				return 1
			program_list[program] = Program(config['programs'][program], program)
	signal.signal(signal.SIGHUP, reload_config)

	server = ServerManager()
	controller = Controller(program_list)
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
