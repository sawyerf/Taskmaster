import socket
import os

from .log import Log

SOCK_FILE = '/tmp/taskmaster.sock'

class ServerManager:
	def __init__(self):
		self.server = self.bind()
		self.sock = None

	def bind(self):
		try:
			os.remove(SOCK_FILE)
		except OSError:
			if os.path.exists(SOCK_FILE):
				raise
		server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		server.bind(SOCK_FILE)
		server.listen()
		return server
	
	def listen(self):
		self.sock, addr = self.server.accept()
		self.sock.setblocking(False)
		Log.Info(f'New Connection')

	def getCommand(self):
		while True:
			try:
				cmd = self.sock.recv(1024)
				if cmd != b'':
					return cmd.decode(errors='ignore')
			except ConnectionResetError:
				Log.Info('Connection end')
				self.sock.close()
				self.sock = None
				return None
			except BlockingIOError:
				continue
			try:
				self.sock.send(b'')
			except BrokenPipeError:
				Log.Info('Connection end')
				self.sock.close()
				self.sock = None
				return None
	
	def respond(self, response):
		try:
			self.sock.send(response + b'\x00\x00\x00\x00\x00')
		except ConnectionResetError or BrokenPipeError:
			Log.Info('Connection end')
			self.sock.close()
			self.sock = None
			return None

	def disconnect(self):
		self.sock.close()
		self.sock = None

class ClientManager:
	def connect(self):
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			self.sock.connect(SOCK_FILE)
		except:
			print('[!] Fail to connect.')
			return False
		return True

	def getResponse(self):
		while True:
			try:
				data = self.sock.recv(1024)
			except BrokenPipeError or ConnectionError:
				return False
			if data != b'':
				print(data.decode(), end='')
			elif not self.send(b''):
				return False
			if b'\x00\x00\x00\x00\x00' in data:	
				return True

	def send(self, data):
		try:
			self.sock.send(data)
			return True
		except BrokenPipeError:
			print('[!] Connection Close')
			return False

	def close(self):
		self.sock.close()