from email.policy import default
import subprocess

class ProgramProperty:
    def __init__(self, type, default, required=False):
        self.type = type
        self.default = default
        self.required = required

class Program:

    def __init__(self, program: dict) -> None:
        try: 
            self.parse(program)
        except Exception as exc:
            raise exc
        self.launch()

    def parse(self, program: dict) -> None:
        program_description = {
            'command': ProgramProperty(str, None, True),
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

    def launch(self):
        null = open('/dev/null', 'r')
        self.process = subprocess.Popen(self.command, stdin=null, stdout=null, stderr=null)
