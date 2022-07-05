import os
import signal

from .program import Program
from .var import PID_FILE

class Controller:
    def __init__(self, program_list: dict):
        self.program_list = program_list
    
    def status(self, arg: str) -> str:
        response = ""
        if arg == "all":
            for program in self.program_list:
                response += self.program_list[program].status()
        elif arg not in self.program_list.keys():
            response = "Invalid program name.\n"
        else:
            response = self.program_list[arg].status()
        return response
    
    def start(self, arg: str) -> str:
        response = ""
        if arg == "all":
            for program in self.program_list:
                self.program_list[program].start()
                response += f"{program} started"
        elif arg not in self.program_list.keys():
            response = "Invalid program name.\n"
        else:
            self.program_list[arg].start()
            response = f"{arg} started"
        return response
    
    def stop(self, arg: str) -> str:
        response = ""
        if arg == "taskmaster":
            with open(PID_FILE, 'r') as pid_file:
                pid = int(pid_file.read())
            os.kill(int(pid), signal.SIGTERM)
            response = "Taskmaster daemon stopped\n"
        elif arg in ["all", "main"]:
            for program in self.program_list:
                self.program_list[program].stop()
                response += f"{program} stopped\n"
        elif arg not in self.program_list.keys():
            response = "Invalid program name.\n"
        else:
            self.program_list[arg].stop()
            response = f"{arg} stopped\n"
        return response

    def restart(self, arg: str) -> str:
        response = ""
        if arg == "all":
            for program in self.program_list:
                self.program_list[program].restart()
                response += f"{program} restarted"
        elif arg not in self.program_list.keys():
            response = "Invalid program name.\n"
        else:
            self.program_list[arg].restart()
            response = f"{arg} restarted"
        return response

    def reload(self, arg: str):
        response = ""
        if arg == "all":
            with open(PID_FILE, 'r') as pid_file:
                pid = int(pid_file.read())
            os.kill(int(pid), signal.SIGHUP)
            response = "Config file reloaded.\n"
        elif arg not in self.program_list.keys():
            response = "Invalid program name.\n"
        # else:
        #     self.program_list[arg].reload()
        #     response = f"{arg} reloaded\n"
        return response
