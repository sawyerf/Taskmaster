import subprocess
import shlex
import datetime
import threading

from .signal import signals
from .log	import Log

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

	def parseUni(self, program: dict, prop_name, set_props):
		prop = self.PARSER.get(prop_name)
		if prop_name not in program.keys():
			if prop.required:
				raise Exception(f'{prop_name} is required and missing')
			else:
				if set_props:
					self.__setattr__(prop_name, prop.default)
				return
		if prop.type is not type(program[prop_name]):
			raise Exception(f'{prop_name}: found {type(program[prop_name])}, {prop.type} expected')
		if set_props:
			self.__setattr__(prop_name, program[prop_name])

	def parse(self, program: dict, set_props=True):
		for property in program.keys():
			if property not in self.PARSER.keys():
				raise Exception(f'{property} : unknown property')
		for prop_name in self.PARSER:
			self.parseUni(program, prop_name, set_props)

class Process(subprocess.Popen):
	def __init__(self, cmd, env, workingdir, umask, name):
		null = open('/dev/null', 'r')
		super().__init__(shlex.split(cmd),
			env=env,
			cwd=workingdir,
			umask=umask,
			stdin=null, stdout=null, stderr=null
		)
		self.start_time = datetime.datetime.now()
		self.name = name

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
	def get_state(self):
		return "RUNNING"

	def status(self):
		uptime = datetime.datetime.now() - self.start_time
		hours = uptime.total_seconds() // 3600
		minutes = (uptime.total_seconds() % 3600) // 60
		seconds = int(uptime.total_seconds() % 60)
		return f"{self.name:15}{self.get_state():8} pid {self.pid:6}, uptime {hours:02}:{minutes:02}:{seconds:02}\n"

class Program(ProgramParse):
	def __init__(self, program: dict, name: str) -> None:
		self.parse(program)
		self.process = []
		self.name = name
		self.config = program
		self.launch()

	def launch(self):
		if self.autostart:
			self.start()

	def start(self):
		for index in range(self.numprocs):
			name = self.name
			if index:
				name += f"_{index}"
			process = Process(self.cmd,
				env=self.env,
				workingdir=self.workingdir,
				umask=self.umask,
				name=name
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
		status = f"{self.name}: \n"
		for process in self.process:
			status += process.status()
		return status

	def reload(self, program: dict):
		try:
			self.parse(program, False)
		except:
			Log.Error(f'Error while reloading program {self.name}')
		if self.config != program:
			self.stop()
			self.parse(program)
			self.config = program
			self.process = []
			self.start()