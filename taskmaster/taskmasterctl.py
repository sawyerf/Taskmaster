from sys	import argv
from .sock	import connect

import re
import time

def parseCommand(cmd):
	reCmd = re.match(r'(?P<cmd>[a-z]*)(?: {1,})(?P<program>[a-zA-Z0-9_]{1,})', cmd)
	if not reCmd:
		print('[!] Wrong command')
		return False
	if reCmd.group('cmd') not in ['stop', 'start', 'status', 'reload', 'restart']:
		print('[!] Command not found')
		return False
	return True

def receiveResponse(sock):
	while True:
		try:
			data = sock.recv(1024)
		except BrokenPipeError or ConnectionError:
			return
		print(data.decode())
		# time.sleep(2)
		if b'\x00\x00\x00\x00\x00' in data:	
			return

def main():
	sock = connect()
	if sock is None:
		exit(1)
	# print(sock.recv(1024))
	if len(argv) == 1:
		while True:
			try:
				cmd = input('taskmaster> ')
				if cmd == "exit":
					break
				if not parseCommand(cmd):
					continue
			except EOFError:
				print()
				break
			sock.send(cmd.encode())
			receiveResponse(sock)
	else:
		cmd = ' '.join(argv[1:])
		if not parseCommand(cmd):
			return
		sock.send(cmd.encode())
		receiveResponse(sock)
	sock.close()