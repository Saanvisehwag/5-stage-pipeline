# RISC V 5 stage pipeline simulator
import time
from collections import deque
import matplotlib.pyplot as plt

clock = 0
jump = 0
flagBeq = 0
flagInst = 0
flagMem = 0
flagRAW = 0
nextInstClock = {
    "F": 0,
    "D": 0,
    "E": 0,
    "M": 0,
    "W": 0
}
lastDest = deque(maxlen=1)
lastInst = deque(maxlen=1)
l = open("log.txt", "w")
noOfRegInst = 0
noOfMemInst = 0
dataStallFreq = []
instMemAccess = []
dataMemAccess = {}
counter = 0

class Mem:
    def __init__(self):
        self.pc = 0
        self.mem = [0] * 4101  # 4014 in hex => 16400 in dec => 16400/4 = 4100
        self.mem[44] = 44
        self.mem[8] = 20


class CPU:
    def __init__(self, instruction_obj, memory_object, instruction_delay, memory_delay):
        self.instruction_delay = instruction_delay+1
        self.memory_delay = memory_delay+1
        self.instruction_obj = instruction_obj
        self.memory_object = memory_object
        self.pc = -1
        self.log = ""
        self.reg = [0] * 32
        self.reg[0] = 0
        self.reg[1] = 1
        self.reg[2] = 2
        self.reg[3] = 3
        self.reg[4] = 4
        self.reg[5] = 5
        self.reg[6] = 6
        self.reg[7] = 7
        self.reg[8] = 8
        self.reg[9] = 9
        self.reg[13] = 4097
        self.opcode = ""
