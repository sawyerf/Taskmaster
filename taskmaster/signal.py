import signal

from .log import Log
from .program import Program
import yaml
from .var import Global
from .programParse import parseConfig

def parse_config() -> dict:
	with open(Global.CONFIG_FILE) as stream:
		try:
			config = yaml.safe_load(stream)
			if not config:
				config = {}
			return config
		except yaml.YAMLError as exc:
			Log.Error(f'Error while loading config file')
			return {}

def reload_config(signum, frame):
	Log.Info('Reloading config file')
	config = parse_config()
	listOptions = parseConfig(config) # TODO: gerer si ca fail
	for options in listOptions:
		nameProgram = options.name
		if nameProgram not in Global.program_list:
			Global.program_list[nameProgram] = Program(options)
		else:
			Global.program_list[nameProgram].reload(options)
	# Stop les tasks supprimer
	for program in Global.program_list:
		if program not in config['programs']:
			Global.program_list[program].stop()


def termStop(signum, frame):
	Log.Info('Receive SIGTERM')
	for program in Global.program_list:
		Global.program_list[program].stop()
	exit(0)

def setSignal():
	signal.signal(signal.SIGHUP, reload_config)
	signal.signal(signal.SIGTERM, termStop)
