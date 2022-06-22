# from email.policy import default
import subprocess
import shlex
import os
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

class Process(subprocess.Popen):
	def __init__(self, cmd, env, workingdir, umask):
		null = open('/dev/null', 'r')
		super().__init__(shlex.split(cmd),
			env=env,
			cwd=workingdir,
			umask=umask,
			stdin=null, stdout=null, stderr=null
		)

	def myWait(self):
		returnCode = self.wait()
		print(returnCode)
		# if returnCode in self.exitcodes:
		# 	pass # Success
		# else:
		# 	pass # Fail

	def myStop(self, stopsignal, stoptime):
		self.send_signal(stopsignal)
		try:
			self.wait(stoptime)
		except subprocess.TimeoutExpired:
			self.kill()
			print('Force kill')

class Program(ProgramParse):
	def __init__(self, program: dict) -> None:
		self.parse(program)
		self.process = []
		self.launch()

	def launch(self):
		if self.autostart:
			self.start()

	def start(self):
		for index in range(self.numprocs):
			process = Process(self.cmd,
				env=self.env,
				workingdir=self.workingdir,
				umask=self.umask,
			)
			# print(process.pid)
			thr = threading.Thread(target=process.myWait)
			thr.start()
			self.process.append(process)
	
	def stop(self):
		for process in self.process:
			process.myStop(signals[self.stopsignal], self.stoptime)
		self.process = []

	def restart(self):
		self.stop()
		self.start()
	
	def status(self):
		pass