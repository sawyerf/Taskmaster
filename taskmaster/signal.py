import signal

from .log import Log
from .program import Program
import yaml
from .var import Global

def parse_config() -> dict:
	with open(Global.CONFIG_FILE) as stream:
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
			if not config['programs'][program]:
				Log.Error(f'Error in configuration file, program {program} should not be empty')
				return 1
			if program not in Global.program_list:
				Global.program_list[program] = Program(config['programs'][program], program)
			else:
				Global.program_list[program].reload(config['programs'][program])

def termStop(signum, frame):
	Log.Info('Receive SIGTERM')
	for program in Global.program_list:
		Global.program_list[program].stop()
	exit(0)

def setSignal():
	signal.signal(signal.SIGHUP, reload_config)
	signal.signal(signal.SIGTERM, termStop)
