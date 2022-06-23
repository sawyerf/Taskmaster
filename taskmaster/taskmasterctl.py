from sys	import argv
from .sock	import connect

import re

def parseCommand(cmd):
	reCmd = re.match(r'(?P<cmd>[a-z]*)(?: {1,})(?P<program>[a-zA-Z0-9_]{1,})', cmd)
	if not reCmd:
		print('[!] Wrong command')
		return False
	if reCmd.group('cmd') not in ['stop', 'start', 'status', 'reload']:
		print('[!] Command not found')
		return False
	return True

def main():
	sock = connect()
	if sock is None:
		exit(1)
	# print(sock.recv(1024))
	if len(argv) == 1:
		while True:
			try:
				cmd = input('taskmaster> ')
				if not parseCommand(cmd):
					continue
			except EOFError:
				print()
				break
			sock.send(cmd.encode())
	else:
		cmd = ' '.join(argv[1:])
		if not parseCommand(cmd):
			return
		sock.send(cmd.encode())
		while True:
			try:
				data = sock.recv(1024)
			except BrokenPipeError or ConnectionError:
				break
			# If Connection stop during this loop it make a infinite loop
			print(data.decode())
			if b'\x00\x00\x00\x00\x00' in data:	
				break
	sock.close()