import subprocess
import shlex
import datetime
import threading
import pwd
import os

from .var import SIGNALS
from .log	import Log

def getFd(arg: str):
	if arg == 'discard':
		arg = '/dev/null'
	return open(arg, 'w+')

def privilege_deescalate(user_uid, user_gid):
	os.setgid(user_gid)
	os.setuid(user_uid)
	
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
		self.status = ''

	def myStart(self):
		if self.start and self.poll() is None:
			Log.Warning(f'{self.name}: Trying to start a process that already running')
			return f'{self.name}: Trying to start a process that already running\n'
		self.start = True
		self.gracefulStop = False
		self.status = 'STARTED'
		pw = pwd.getpwnam(self.options.run_as)
		user_uid       = pw.pw_uid
		user_gid       = pw.pw_gid
		super().__init__(shlex.split(self.options.cmd),
			env=self.options.env,
			cwd=self.options.workingdir,
			umask=self.options.umask,
			stdin=getFd('discard'),
			stdout=getFd(self.options.stdout),
			stderr=getFd(self.options.stderr),
			preexec_fn=privilege_deescalate(user_uid, user_gid)
		)
		self.start_time = datetime.datetime.now()
		thr = threading.Thread(target=self.myWait, args=(self.options.exitcodes,))
		thr.start()
		return f'{self.name}: Started\n'


	def myWait(self, exitcodes):
		returnCode = self.wait()
		diffTime = datetime.datetime.now() - self.start_time
		self.run = False
		self.stopTime = datetime.datetime.now()
		if self.gracefulStop:
			self.status = 'STOPPED'
		else:
			self.status = 'FINISHED'
		if returnCode in exitcodes and self.options.starttime < diffTime.total_seconds():
			Log.Info(f'{self.name}: End successfuly with code {returnCode}')
			if self.options.autorestart != 'always':
				return
		else:
			if returnCode not in exitcodes:
				Log.Error(f'{self.name}: End badly with code {returnCode}')
			else:
				Log.Error(f'{self.name}: End badly, fail at {diffTime}')
			if self.options.autorestart not in ['always', 'unexpected']:
				return
		if not self.gracefulStop and self.retry > 0:
			Log.Info(f'Restart process ({self.name})')
			self.myStart()
			self.retry -= 1

	def myStop(self, stopsignal, stoptime):
		if not self.start:
			Log.Warning(f'{self.name}: Trying to stop a process wich not been start')
			return f'{self.name}: Trying to stop a process wich not been start\n'
		if type(self.poll()) is int:
			return f'{self.name}: Not running\n'
		Log.Info(f'{self.name}: Graceful Stop')
		self.gracefulStop = True
		self.send_signal(stopsignal)
		try:
			self.wait(stoptime)
		except subprocess.TimeoutExpired:
			self.kill()
			Log.Warning(f'{self.name}: Hard kill. Graceful stop timeout')
			return f'{self.name}: Hard kill. Graceful stop timeout\n'
		return f'{self.name}: Stopped\n'

	def myStatus(self):
		if self.gracefulStop:
			return f"{self.name:15} STOPPED {self.stopTime.strftime('%B %d %I:%M %p')}\n"
		if self.status == 'FINISHED':
			return f"{self.name:15} FINISHED {self.stopTime.strftime('%B %d %I:%M %p')}\n"
		if not self.start:
			return f'{self.name} not started\n'			
		uptime = datetime.datetime.now() - self.start_time
		hours = uptime.total_seconds() // 3600
		minutes = (uptime.total_seconds() % 3600) // 60
		seconds = int(uptime.total_seconds() % 60)
		return f"{self.name:15} RUNNING pid {self.pid:6}, uptime {hours:02}:{minutes:02}:{seconds:02}\n"

class Program():
	'''
	Manage list of process
	'''
	def __init__(self, options) -> None:
		self.options = options
		self.process = []
		self.launch()

	def launch(self):
		for index in range(self.options.numprocs):
			name = self.options.name
			if index:
				name += f"_{index}"
			process = Process(
				name=name,
				options=self.options,
			)
			self.process.append(process)
		if self.options.autostart:
			self.start()

	def start(self):
		retctl = ''
		for process in self.process:
			ret = process.myStart()
			Log.Info(ret.strip('\n'))		
			retctl += ret
		return retctl

	def stop(self):
		retctl = ''
		for process in self.process:
			ret = process.myStop(SIGNALS[self.options.stopsignal], self.options.stoptime)
			Log.Info(ret.strip('\n'))	
			retctl += ret
		return retctl

	def restart(self):
		ret = self.stop()
		ret += self.start()
		Log.Info(ret)
		return ret
	
	def status(self):
		status = f"{self.options.name}: \n"
		for process in self.process:
			status += process.myStatus()
		status += '\n'
		return status

	def reload(self, newOptions):
		dictOptions = dict(vars(self.options))
		dictNewOptions = dict(vars(newOptions))

		if dictOptions != dictNewOptions:
			self.stop()
			self.options = newOptions
			self.process = []
			self.launch()