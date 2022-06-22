from email.policy import default
import subprocess
from .signal import signals
import os
import datetime

class ProgramProperty:
	def __init__(self, type, default, required=False):
		self.type = type
		self.default = default
		self.required = required

class ProgramParse:
	PARSER={
		'cmd': ProgramProperty(str, None, True),
		'numprocs': ProgramProperty(int, 1, False),
		'stopsignal': ProgramProperty(str, 'TERM', False),
	}

	def parseUni(self, program: dict, prop_name):
		prop = self.PARSER.get(prop_name)
		if prop_name not in program.keys():
			if prop.required:
				raise Exception(f'{prop_name} is required and missing')
			else:
				self.__setattr__(prop_name, default)
		if prop.type is not type(program[prop_name]):
			raise Exception(f'{prop_name}: found {type(program[prop_name])}, {prop.type} expected')
		self.__setattr__(prop_name, program[prop_name])

	def parse(self, program: dict):
		for property in program.keys():
			if property not in self.PARSER.keys():
				raise Exception(f'{property} : unknown property')
		for prop_name in self.PARSER:
			self.parseUni(program, prop_name)

class Program(ProgramParse):
	def __init__(self, program: dict) -> None:
		self.parse(program)
		self.process = []
		self.start()

	def start(self):
		null = open('/dev/null', 'r')
		for index in range(self.numprocs):
			self.process.append(subprocess.Popen(self.cmd, stdin=null, stdout=null, stderr=null))
	
	def stop(self):
		for proc in self.process:
			proc.send_signal(signals[self.stopsignal])
			print('lol', proc.pid)
		self.process = []

	def restart(self):
		self.stop()
		self.start()
	
	def status(self):
		pass