# from email.policy import default
import subprocess
import shlex
import os
import datetime
import threading
import time

from .signal import signals

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
		'env': ProgramProperty(dict, {}, False),
		'workingdir': ProgramProperty(str, None, False),
		'autostart': ProgramProperty(bool, True, False),
		'umask': ProgramProperty(int, -1, False),
		'stoptime': ProgramProperty(int, 1, False),
		# 'exitcodes': ProgramProperty(int, [0], False),
	}

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
		self.launch()

	def launch(self):
		if self.autostart:
			self.start()

	def wait(self, process):
		returnCode = process.wait()
		print(returnCode)
		# if returnCode in self.exitcodes:
		# 	pass # Success
		# else:
		# 	pass # Fail

	def start(self):
		null = open('/dev/null', 'r')
		for index in range(self.numprocs):
			sub = subprocess.Popen(shlex.split(self.cmd),
				env=self.env,
				cwd=self.workingdir,
				umask=self.umask,
				stdin=null, stdout=null, stderr=null
			)
			thr = threading.Thread(target=self.wait, args=(sub,))
			thr.start()
			self.process.append(sub)
	
	def stop(self):
		for proc in self.process:
			proc.send_signal(signals[self.stopsignal])
			try:
				proc.wait(self.stoptime)
			except subprocess.TimeoutExpired:
				proc.kill()
				print('Force kill')
			# print('lol', proc.pid)
		self.process = []

	def restart(self):
		self.stop()
		self.start()
	
	def status(self):
		pass