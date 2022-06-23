from .program import Program

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
            response = self.program_list[arg].start()
        return response
    
    def stop(self, arg: str) -> str:
        response = ""
        if arg == "all":
            for program in self.program_list:
                self.program_list[program].stop()
                response += f"{program} stopped"
        elif arg not in self.program_list.keys():
            response = "Invalid program name.\n"
        else:
            response = self.program_list[arg].stop()
        return response
        