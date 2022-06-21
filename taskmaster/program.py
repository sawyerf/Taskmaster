from email.policy import default
import subprocess

class ProgramProperty:
    def __init__(self, type, default, required=False):
        self.type = type
        self.default = default
        self.required = required

class Program:
    def __init__(self, program: dict) -> None:
        self.parse(program)
        self.process = []
        self.start()

    def parse(self, program: dict) -> None:
        program_description = {
            'command': ProgramProperty(str, None, True),
            'numprocs': ProgramProperty(int, 1, False),
            'stopsignal': ProgramProperty(str, 'TERM', False),
        }
        for property in program.keys():
            if property not in program_description.keys():
                raise Exception(property + ': unknown property')
        for prop_name in program_description:
            prop = program_description.get(prop_name)
            if prop_name not in program.keys():
                if prop.required:
                    raise Exception(prop_name + ' is required and missing')
                else:
                    self.__setattr__(prop_name, default)
            if prop.type is not type(program[prop_name]):
                raise Exception(prop_name + ': found ' + str(type(program[prop_name])) + ', ' + str(prop.type) + ' expected')
            self.__setattr__(prop_name, program[prop_name])

    def start(self):
        null = open('/dev/null', 'r')
        for index in range(self.numprocs):
            self.process.append(subprocess.Popen(self.command, stdin=null, stdout=null, stderr=null))
    
    def stop(self):
        for proc in self.process:
            os.kill(proc, signal.TERM) # add self.stopsignal
        self.process = []

    def restart(self):
        self.stop()
        self.start()
    
    def status(self):
        pass