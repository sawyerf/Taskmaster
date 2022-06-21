import socket
import os

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
		print(f'[*] New Connection')

	def getCommand(self):
		while True:
			try:
				cmd = self.sock.recv(1024)
				if cmd != b'':
					return cmd.decode(errors='ignore')
			except ConnectionResetError:
				print('[*] Connection end')
				self.sock.close()
				self.sock = None
				return None
			except BlockingIOError:
				continue
			try:
				self.sock.send(b'')
			except BrokenPipeError:
				print('[*] Connection end')
				self.sock.close()
				self.sock = None
				return None


def connect():
	sock =  socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	try:
		sock.connect(SOCK_FILE)
	except:
		print('[!] Fail to connect.')
		return None
	return sock