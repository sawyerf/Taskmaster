import re
import time
from sys	import argv

from .sock	import ClientManager

def parseCommand(cmd):
	reCmd = re.match(r'(?P<cmd>[a-z]*)(?: {1,})(?P<program>[a-zA-Z0-9_]{1,})', cmd)
	if not reCmd:
		print('[!] Wrong command')
		return False
	if reCmd.group('cmd') not in ['stop', 'start', 'status', 'reload', 'restart']:
		print('[!] Command not found')
		return False
	return True

def main():
	client = ClientManager()
	if not client.connect():
		exit(1)
	if len(argv) == 1:
		while True:
			try:
				cmd = input('\33[1;31mtaskmaster> \033[00m')
				if cmd == "exit":
					break
				if not parseCommand(cmd):
					continue
			except EOFError:
				print()
				break
			if not client.send(cmd.encode()) or \
				not client.getResponse():
				break
	else:
		cmd = ' '.join(argv[1:])
		if not parseCommand(cmd):
			return
		client.send(cmd.encode())
		client.getResponse()
	client.close()