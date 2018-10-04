import re
import sys

# Function removes whitespace and comments
def removeWhitespace(line):
    new_line = line.strip()
    
    if len(new_line) == 0:
        return ""
    
    for index, char in enumerate(new_line):
        if char == "/":
            new_line = new_line[:index]
        
        # in case line started with a comment
        if len(new_line) == 1:
            new_line = ""
    
    return new_line

# Function checks type of instruction
def instruction_type(line):
    if line[0] == "@":
        return "A"
    elif line[0] == "(":
        return "Label"
    else:
        return "C"

# Parser class to identify type of command and split it accordingly
class Parser:
    
    def __init__(self):
        self.symbol_table = {
            "R0" : "0",
            "R1" : "1",
            "R2" : "2",
            "R3" : "3",
            "R4" : "4",
            "R5" : "5",
            "R6" : "6",
            "R7" : "7",
            "R8" : "8",
            "R9" : "9",
            "R10" : "10",
            "R11" : "11",
            "R12" : "12",
            "R13" : "13",
            "R14" : "14",
            "R15" : "15",
            "SCREEN" : "16384",
            "KBD" : "24576",
            "SP" : "0",
            "LCL" : "1",
            "ARG" : "2",
            "THIS" : "3",
            "THAT" : "4"
        }

        self.cmd_type = ""
        self.command = ""
        self.destination = ""
        self.computation = ""
        self.jump = ""
    
    def read_line(self, line):
        self.line = line
        self.cmd_type = instruction_type(line)

    # Prepares attributes for cmd_mapper
    def prepare(self):
        if self.cmd_type == "A":
            self.command = self.line[1:]
        elif self.cmd_type == "C":
            self.destination, self.computation, self.jump = self.parse_c_command(self.line)
    
    # Parses C command and returns its parts separately
    def parse_c_command(self, line):
        if "=" in line:
            destination = re.compile(r".*(?==)").match(line).group()
            computation = re.compile(r"((?<=\w=).*(?=;\w{3}))|((?<=\w=).*$)").search(line).group()

            if ";" in line: 
                jump = re.compile(r"(?<=;)\w{3}").search(line).group()
            else:
                jump = ""
            
        else:
            destination = ""
            computation = re.compile(r".*(?=;)").search(line).group()
            jump = re.compile(r"(?<=;)\w{3}").search(line).group()

        return destination, computation, jump

    def parse_label(self, line, line_number):
        label = re.compile(r'(?<=\()\w*(?=\))').search(line).group()
        
        if label not in self.symbol_table.keys():
            self.symbol_table[label] = line_number

    # Function to reset field after line has been processed    
    def reset(self):
        self.cmd_type = ""
        self.command = ""
        self.destination = ""
        self.computation = ""
        self.jump = ""


# After Parser splits the command, Cmd_mapper converts each one into
# binary based on the mapping table
class Cmd_mapper:

    def __init__(self):
        self.comp_table = {
            "0":"0101010",
            "1":"0111111",
            "-1":"0111010",
            "D":"0001100",
            "A":"0110000",
            "!D":"0001101",
            "!A":"0110001",
            "-D":"0001111",
            "-A":"0110011",
            "D+1":"0011111",
            "A+1":"0110111",
            "D-1":"0001110",
            "A-1":"0110010",
            "D+A":"0000010",
            "D-A":"0010011",
            "A-D":"0000111",
            "D&A":"0000000",
            "D|A":"0010101",
            "M":"1110000",
            "!M":"1110001",
            "-M":"1110011",
            "M+1":"1110111",
            "M-1":"1110010",
            "D+M":"1000010",
            "D-M":"1010011",
            "M-D":"1000111",
            "D&M":"1000000",
            "D|M":"1010101"
        }

        self.dest_table = {
            "":"000",
            "M":"001",
            "D":"010",
            "MD":"011",
            "A":"100",
            "AM":"101",
            "AD":"110",
            "AMD":"111"
        }
    
        self.jump_table = {
            "":"000",
            "JGT":"001",
            "JEQ":"010",
            "JGE":"011",
            "JLT":"100",
            "JNE":"101",
            "JLE":"110",
            "JMP":"111"
        } 

    def translate(self, **kwargs):
        if len(kwargs) == 1:
            return "0" + format(int(kwargs['command']), '015b')
        elif len(kwargs) == 3:
            computation = self.comp_table[kwargs['computation']]
            destination = self.dest_table[kwargs['destination']]
            jump = self.jump_table[kwargs['jump']]

            return "111" + computation + destination + jump

# Main loop

# Keep appending translations to empty string
final_file = ""

# Open file to read
file_name = sys.argv[1]

# prep cmd_mapper
mapper = Cmd_mapper()

# read in file so it only gets read once
instructions = open(file_name, "r").readlines()

# initialize parser
parser = Parser()

# First sweep through the file for label detection

for line in instructions.splitlines():
    line = removeWhitespace(line)
    parser.read_line(line)

    if parser.cmd_type != "Label":
        parser.reset()
        continue
    
    parser.parse_label(line)
    parser.reset()

# Second sweep through the file for variable detection

with open(file_name, "r") as f:
    for line in f.readlines():
        line = removeWhitespace(line)

        if line == "":
            continue

        parser.prepare()

        if parser.cmd_type == "A":
           final_file += (mapper.translate(command = parser.command)) 
           final_file += ("\n")
        else:
            final_file += (mapper.translate(destination = parser.destination,
                             computation = parser.computation,
                             jump = parser.jump))
            final_file += ("\n")

write_destination = re.compile(r'.*(?=\.)').search(file_name).group()

with open(write_destination + ".hack", "w") as f:
    f.write(final_file)