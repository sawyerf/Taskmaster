import pwd
import os

from .var import SIGNALS
from .log	import Log

class ProgramProperty:
	def __init__(self, type, default, required=False, mustIn=None):
		self.type = type
		self.default = default
		self.required = required
		self.mustIn = mustIn

class ProgramParse:
	'''
	Parse Yaml configuration
	'''
	PARSER={
		'cmd': ProgramProperty(str, None, True),
		'numprocs': ProgramProperty(int, 1, False),
		'stopsignal': ProgramProperty(str, 'TERM', False, SIGNALS.keys()),
		'env': ProgramProperty(dict, {}, False),
		'workingdir': ProgramProperty(str, None, False),
		'autostart': ProgramProperty(bool, True, False),
		'umask': ProgramProperty(int, -1, False),
		'stoptime': ProgramProperty(int, 1, False),
		'exitcodes': ProgramProperty(list, [0], False),
		'startretries': ProgramProperty(int, 0, False),
		'starttime': ProgramProperty(int, -1, False),
		'autorestart': ProgramProperty(str, 'unexpected', False, ['always', 'never', 'unexpected']),
		'stdout': ProgramProperty(str, 'discard', False),
		'stderr': ProgramProperty(str, 'discard', False),
		'run_as': ProgramProperty(str, os.getlogin(), False, [user.pw_name for user in pwd.getpwall()]),
	}

	def __init__(self, name, program: dict):
		if name in ['main', 'taskmasterd']:
			raise Exception(f'Name of the process `{name}\' not valid')
		self.name = name
		self.parse(program)

	def parseUni(self, program: dict, prop_name):
		prop = self.PARSER.get(prop_name)
		if prop_name not in program.keys():
			if prop.required:
				raise Exception(f'{prop_name} is required and missing')
			else:
				self.__setattr__(prop_name, prop.default)
				return
		if prop.type is not type(program[prop_name]):
			raise Exception(f'{prop_name}: found {type(program[prop_name])}, {prop.type} expected')
		if prop.type is list:
			for i in program[prop_name]:
				if type(i) is not int:
					raise Exception(f'{prop_name}: found {type(i)}, int expected')
		if prop.mustIn is not None and program[prop_name] not in prop.mustIn:
			raise Exception(f'\'{prop_name}\': {program[prop_name]} not in {prop.mustIn}')
		self.__setattr__(prop_name, program[prop_name])

	def parse(self, program: dict):
		for property in program.keys():
			if property not in self.PARSER.keys():
				raise Exception(f'{property} : unknown property')
		for prop_name in self.PARSER:
			self.parseUni(program, prop_name)

def parseConfig(config):
	listOptions = []
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
			listOptions.append(ProgramParse(program, config['programs'][program]))
	return listOptions