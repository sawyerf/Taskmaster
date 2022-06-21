import os
import sys
import argparse
import yaml

from .program import Program
from .sock	import ServerManager

PID_FILE = '/tmp/taskmaster.pid'

def parse_config(config_file: argparse.FileType) -> dict:
	with open(config_file.name) as stream:
		try:
			config = yaml.safe_load(stream)
			return config
		except yaml.YAMLError as exc:
			print(exc)

def daemonize():
	r, w = os.pipe()
	pid = os.fork()
	if pid != 0:
		os.close(w)
		r = os.fdopen(r)
		r.read()
		sys.exit(0)
	else:
		os.close(r)
		w = os.fdopen(w, 'w')
		os.setsid()
		pid = os.fork()
		if pid != 0:
			exit()
		else:
			null = open('/dev/null', 'r+')
			os.dup2(sys.stdin.fileno(), null.fileno())
			os.dup2(sys.stdout.fileno(), null.fileno())
			os.dup2(sys.stderr.fileno(), null.fileno())
			os.umask(0)
			os.chdir('/')
			with open(PID_FILE, 'w+') as stream:
				stream.write(str(os.getpid()))
			w.write("Parent can leave")
			w.close()
	return

def main():
	program_list = []

	parser = argparse.ArgumentParser(description='Taskmaster daemon')
	parser.add_argument('-c', '--config', type=argparse.FileType('r', encoding='utf-8'), required=True, help='Defines the configuration file to read')
	args = parser.parse_args()
	config = parse_config(args.config)
	daemonize()
	if not config:
		return 1
	if 'programs' in config.keys():
		if not config['programs']:
			return 1
		for program in config['programs']:
			if not config['programs'][program]:
				print('Program', program, 'should not be empty')
				return 1
			try:
				program_list.append(Program(config['programs'][program]))
			except Exception as exc:
				print(program + ':', exc)
	server = ServerManager()
	while True:
		server.listen()
		while True:
			cmd = server.getCommand()
			if not cmd:
				break
			print(cmd)
