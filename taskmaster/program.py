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
	'''
	Parse Yaml configuration
	'''
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
		'starttime': ProgramProperty(int, -1, False),
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
	'''
	Manage Process	
	'''
	def __init__(self, name, options):
		self.name = name
		self.options = options
		self.start = False
		self.retry = self.options.startretries
		self.gracefulStop = False

	def myStart(self):
		if self.start and self.poll() is None:
			log.Warning(f'{self.name}: Trying to start a process that already running')
			return f'{self.name}: Trying to start a process that already running\n'
		null = open('/dev/null', 'r')
		self.start = True
		self.gracefulStop = False
		super().__init__(shlex.split(self.options.cmd),
			env=self.options.env,
			cwd=self.options.workingdir,
			umask=self.options.umask,
			stdin=null, stdout=null, stderr=null
		)
		self.start_time = datetime.datetime.now()
		thr = threading.Thread(target=self.myWait, args=(self.options.exitcodes,))
		thr.start()
		return f'{self.name}: Started\n'


	def myWait(self, exitcodes):
		returnCode = self.wait()
		diffTime = datetime.datetime.now() - self.start_time
		if self.options.starttime >= diffTime.total_seconds():
			log.Error(f'{self.name}: End badly, fail at {diffTime}')
		elif returnCode in exitcodes:
			log.Info(f'{self.name}: End successfuly with code {returnCode}')
		else:
			log.Error(f'{self.name}: End badly with code {returnCode}')
			if not self.gracefulStop and self.retry > 0:
				log.Info(f'Restart process ({self.name})')
				self.myStart()
				self.retry -= 1

	def myStop(self, stopsignal, stoptime):
		if not self.start:
			log.Warning(f'{self.name}: Trying to stop a process wich not been start')
			return f'{self.name}: Trying to stop a process wich not been start\n'
		if type(self.poll()) is int:
			return f'{self.name}: Not running\n'
		log.Info(f'{self.name}: Graceful Stop')
		self.send_signal(stopsignal)
		try:
			self.wait(stoptime)
		except subprocess.TimeoutExpired:
			self.kill()
			log.Warning(f'{self.name}: Hard kill. Graceful stop timeout')
			return f'{self.name}: Hard kill. Graceful stop timeout\n'
		return f'{self.name}: Stopped\n'

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
	'''
	Manage list of process
	'''
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
		ret = ''
		for process in self.process:
			ret += process.myStart()
		return ret

	def stop(self):
		ret = ''
		for process in self.process:
			ret += process.myStop(signals[self.stopsignal], self.stoptime)
		return ret

	def restart(self):
		ret = self.stop()
		ret += self.start()
		return ret
	
	def status(self):
		status = f"{self.name}: \n"
		for process in self.process:
			status += process.status()
		return status