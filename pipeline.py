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

    def start(self, clock):
        global dataStallFreq
        dataStallFreq = [0] * len(self.instruction_obj.instruction)

        while (self.pc < len(self.instruction_obj.instruction) - 1):

            global flagInst
            if (self.instruction_delay > 1):
                flagInst = 1

            global jump
            if (jump > 0 and flagBeq == 0):
                self.pc = self.pc + jump - 2
                jump = 0
            
            self.pc = self.pc + 1
            self.dataStallCounter = 0
            clock = nextInstClock["F"]
            self.fetch(self.pc, clock)

    def fetch(self, pc, clock):
        ins = self.instruction_obj.instruction[pc]
        
        global flagRAW
        global flagMem
        global flagInst
        global instMemAccess
        global flagBeq 
        global dataStallFreq

        flagRAW = counter
        if(flagInst == 1 and flagMem == 1 and flagRAW > 0 and flagBeq == 0):
            if(self.memory_delay > self.instruction_delay and self.memory_delay > flagRAW):
                for i in range(self.memory_delay):
                    self.wrapper_fetch(ins, clock)
                    instMemAccess.append(self.pc)
                    clock = clock+1
                flagMem = flagMem - 1
                flagInst = 0
                flagRAW = 0
                nextInstClock["F"] = clock
                self.decode(ins, clock=max(clock, nextInstClock["D"]))

            elif(flagRAW+1 > self.instruction_delay and flagRAW+1 > self.memory_delay):
                for i in range(flagRAW):
                    self.wrapper_fetch(ins, clock)
                    instMemAccess.append(self.pc)
                    clock = clock+1
                flagMem = flagMem - 1
                flagInst = 0
                flagRAW = 0
                nextInstClock["F"] = clock
                self.decode(ins, clock=max(clock, nextInstClock["D"]))

            else:
                for i in range(self.instruction_delay):
                    self.wrapper_fetch(ins, clock)
                    instMemAccess.append(self.pc)
                    clock = clock+1
                flagMem = flagMem - 1
                flagInst = 0
                flagRAW = 0
                nextInstClock["F"] = clock
                self.decode(ins, clock=max(clock, nextInstClock["D"]))

        elif(flagInst == 1 and flagBeq == 0):
            for i in range(self.instruction_delay):
                self.wrapper_fetch(ins, clock)
                instMemAccess.append(self.pc)
                clock = clock+1
            flagInst = 0
            nextInstClock["F"] = clock
            self.decode(ins, clock=max(clock, nextInstClock["D"]))

        elif(flagMem == 1 and flagBeq == 0):
            for i in range(self.memory_delay):
                self.wrapper_fetch(ins, clock)
                instMemAccess.append(self.pc)
                clock = clock+1
            flagMem = flagMem - 1
            nextInstClock["F"] = clock
            self.decode(ins, clock=max(clock, nextInstClock["D"]))

        elif(flagRAW > 0 and flagBeq == 0):
            for i in range(flagRAW):
                self.wrapper_fetch(ins, clock)
                instMemAccess.append(self.pc)
                clock = clock+1
            flagRAW = 0
            nextInstClock["F"] = clock
            self.decode(ins, clock=max(clock, nextInstClock["D"]))

        elif(flagInst == 1 and flagBeq == 2):
            flagBeq = 0
            for i in range(2):
                self.wrapper_fetch(ins, clock)
                instMemAccess.append(self.pc)
                clock = clock+1
            dataStallFreq[self.pc] = self.dataStallCounter
            flagInst = 0
            nextInstClock["F"] = clock
            return

        else:
            l.write("\nclock - "+str(clock)+"\n")
            for i in range(len(self.reg)):
                l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

            l.write("\n \n PC - "+str(self.pc)+"\n")
            l.write(" fetch instruction - " + str(ins)+"\n \n")
            l.write(" fetch is not stalled " + "\n \n")
            instMemAccess.append(self.pc)
            clock = clock+1

            if(flagBeq == 2):
                flagBeq = flagBeq - 1
                nextInstClock["F"] = clock
                self.decode(ins, clock=max(clock, nextInstClock["D"]))
            elif(flagBeq == 1):
                flagBeq = flagBeq - 1
                nextInstClock["F"] = clock
                return
            else:
                nextInstClock["F"] = clock
                self.decode(ins, clock=max(clock, nextInstClock["D"]))

    def wrapper_fetch(self, instruction, clock):
        l.write("\nclock - "+str(clock)+"\n")
        for i in range(len(self.reg)):
            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

        l.write("\n \n PC - "+str(self.pc)+"\n")
        l.write(" fetch instruction - " + str(instruction)+"\n \n")
        l.write(" fetch is stalled " + "\n \n")
        self.dataStallCounter = self.dataStallCounter + 1
