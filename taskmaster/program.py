import subprocess
import shlex
import datetime
import threading

from .signal import signals
from .log import log

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
		'exitcodes': ProgramProperty(list, [0], False),
		'startretries': ProgramProperty(int, 0, False),
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
		if prop.type is list:
			for i in program[prop_name]:
				if type(i) is not int:
					raise Exception(f'{prop_name}: found {type(i)}, int expected')
		self.__setattr__(prop_name, program[prop_name])

	def parse(self, program: dict):
		for property in program.keys():
			if property not in self.PARSER.keys():
				raise Exception(f'{property} : unknown property')
		for prop_name in self.PARSER:
			self.parseUni(program, prop_name)

class Process(subprocess.Popen):
	def __init__(self, name, options):
		self.name = name
		self.options = options
		self.start = False
		self.retry = self.options.startretries
		self.gracefulStop = False

	def myStart(self):
		null = open('/dev/null', 'r')
		self.start = True
		self.gracefulStop = False
		super().__init__(shlex.split(cmd),
			env=self.options.env,
			cwd=self.options.workingdir,
			umask=self.options.umask,
			stdin=null, stdout=null, stderr=null
		)
		self.start_time = datetime.datetime.now()

	def myWait(self, exitcodes):
		returnCode = self.wait()
		print(returnCode)
		if returnCode in exitcodes:
			log.Info(f'{self.name} end successfuly with code {returnCode}')
		else:
			log.Error(f'{self.name} end badly with code {returnCode}')
			if not self.gracefulStop and self.retry > 0:
				log.Info(f'Restart process ({self.name})')
				self.myStart()
				self.retry -= 1

	def myStop(self, stopsignal, stoptime):
		if not self.start:
			log.Warning('Trying to stop a process wich not been start')
			return
		self.send_signal(stopsignal)
		try:
			self.wait(stoptime)
		except subprocess.TimeoutExpired:
			self.kill()
			log.Warning('Hard kill. Graceful stop timeout')

	def get_state(self):
		return "RUNNING"

	def status(self):
		if not self.start:
			return f'{self.name} not start\n'
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
		self.launch()

	def launch(self):
		for index in range(self.numprocs):
			name = self.name
			if index:
				name += f"_{index}"
			process = Process(
				name=name,
				options=self,
			)
			self.process.append(process)
		if self.autostart:
			self.start()

	def start(self):
		for process in self.process:
			process.myStart()
			thr = threading.Thread(target=process.myWait, args=(self.exitcodes,))
			thr.start()
	
	def stop(self):
		for process in self.process:
			process.myStop(signals[self.stopsignal], self.stoptime)

	def restart(self):
		self.stop()
		self.start()
	
	def status(self):
		status = f"{self.name}: \n"
		for process in self.process:
			status += process.status()
		return status