from .sock	import ServerManager

def main():
	server = ServerManager()
	while True:
		server.listen()
		while True:
			cmd = server.getCommand()
			if not cmd:
				break
			print(cmd)