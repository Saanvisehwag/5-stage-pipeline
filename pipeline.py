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


    def decode(self, instruction, clock):
        global noOfRegInst
        global noOfMemInst

        global flagBeq
        if (flagBeq == 1):
            l.write("\nclock - "+str(clock)+"\n")
            for i in range(len(self.reg)):
                l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

            l.write("\n \n PC - "+str(self.pc)+"\n")
            l.write(" decode instruction - " +
                    str(instruction)+"\n \n")
            l.write(" decode is not stalled " + "\n \n")
            clock = clock+1
            nextInstClock["D"] = clock
            return
        
        opcode = instruction[-7:]
        global lastDest
        global lastInst
        global flagRAW
        global flagMem
        global counter
            
        if (opcode == "0100011"):
            noOfMemInst = noOfMemInst + 1
            rs2 = instruction[-25:-20]
            rs1 = instruction[-20:-15]
            offset = instruction[0:7] + instruction[-12:-7]

            counter = 0
            if(len(lastDest) == 1 and (rs1 == lastDest[0] or rs2 == lastDest[0]) and lastInst[0] == "0000011"):
                flagRAW = self.memory_delay+1
                flagMem = 0
                for i in range(self.memory_delay+1):
                    if(clock < nextInstClock["M"] - 1):
                        counter = counter + 1
                        self.wrapper_decode(instruction, clock)
                        clock = clock+1
                        flagRAW = counter

                    elif(clock == nextInstClock["M"] - 1 and counter != 0):
                        self.wrapper_decode(instruction, clock)
                        counter = counter + 1
                        clock = clock+1
                        flagRAW = counter
                        break

                    elif(clock == nextInstClock["M"] - 1 and counter == 0):
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

                    else:
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

            elif(flagMem == 2):
                for i in range(self.memory_delay):
                    self.wrapper_decode(instruction, clock)
                    clock = clock+1
                flagMem = flagMem - 1

            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1
            
            lastDest.append(-1)
            lastInst.append(-1)

            nextInstClock["D"] = clock
            self.execute_1(opcode, instruction, rs1=rs1,
                           rs2=rs2, offset=offset, clock=max(clock, nextInstClock["E"]))
            # SW

        elif (opcode == "0010011"):
            noOfRegInst = noOfRegInst + 1
            rs1 = instruction[-20:-15]
            rd = instruction[-12:-7]
            imm = instruction[-32:-20]

            counter = 0
            if(len(lastDest) == 1 and (rs1 == lastDest[0]) and lastInst[0] == "0000011"):
                flagRAW = self.memory_delay+1
                flagMem = 0
                for i in range(self.memory_delay+1):
                    if(clock < nextInstClock["M"] - 1):
                        counter = counter + 1
                        self.wrapper_decode(instruction, clock)
                        clock = clock+1
                        flagRAW = counter
                        
                    elif(clock == nextInstClock["M"] - 1 and counter != 0):
                        self.wrapper_decode(instruction, clock)
                        counter = counter + 1
                        clock = clock+1
                        flagRAW = counter
                        break

                    elif(clock == nextInstClock["M"] - 1 and counter == 0):
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

                    else:
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

            elif(flagMem == 2):
                for i in range(self.memory_delay):
                    self.wrapper_decode(instruction, clock)
                    clock = clock+1
                flagMem = flagMem - 1

            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1

            lastDest.append(rd)
            lastInst.append(opcode)

            nextInstClock["D"] = clock
            self.execute_2(opcode, instruction, rs1,
                           rd=rd, imm=imm, clock=max(clock, nextInstClock["E"]))

            # addi
        elif(opcode == "1111111"):
            noOfMemInst = noOfMemInst + 1
            rs2 = instruction[-12:-7]
            rs1 = instruction[-20:-15]
            imm = instruction[-32:-20]

            counter = 0
            if(len(lastDest) == 1 and (rs1 == lastDest[0] or rs2 == lastDest[0]) and lastInst[0] == "0000011"):
                flagRAW = self.memory_delay+1
                flagMem = 0
                for i in range(self.memory_delay+1):
                    if(clock < nextInstClock["M"] - 1):
                        counter = counter + 1
                        self.wrapper_decode(instruction, clock)
                        clock = clock+1
                        flagRAW = counter

                    elif(clock == nextInstClock["M"] - 1 and counter != 0):
                        self.wrapper_decode(instruction, clock)
                        counter = counter + 1
                        clock = clock+1
                        flagRAW = counter
                        break

                    elif(clock == nextInstClock["M"] - 1 and counter == 0):
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

                    else:
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

            elif(flagMem == 2):
                for i in range(self.memory_delay):
                    self.wrapper_decode(instruction, clock)
                    clock = clock+1
                flagMem = flagMem - 1
            
            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1
            
            lastDest.append(-1)
            lastInst.append(-1)

            nextInstClock["D"] = clock
            self.execute_6(opcode, instruction, rs1,
                           rs2=rs2, imm=imm, clock=max(clock, nextInstClock["E"]))

        elif(opcode == "0000000"):
            noOfMemInst = noOfMemInst + 1

            if(flagMem == 2):
                for i in range(self.memory_delay):
                    self.wrapper_decode(instruction, clock)
                    clock = clock+1
                flagMem = flagMem - 1
            
            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1

            lastDest.append(-1)
            lastInst.append(-1)

            nextInstClock["D"] = clock
            self.execute_7(opcode, instruction, clock=max(clock, nextInstClock["E"]))

        elif (opcode == "0000011"):
            noOfMemInst = noOfMemInst + 1
            rs1 = instruction[-20:-15]
            rd = instruction[-12:-7]
            offset = instruction[-32:-20]
            
            if(flagMem == 2):
                for i in range(self.memory_delay):
                    self.wrapper_decode(instruction, clock)
                    clock = clock+1
                flagMem = flagMem - 1
            
            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1

            lastDest.append(rd)
            lastInst.append(opcode)

            nextInstClock["D"] = clock
            self.execute_3(opcode, instruction, rs1,
                           rd, offset, clock=max(clock, nextInstClock["E"]))

            # LW

        elif (opcode == "1100011"):
            noOfRegInst = noOfRegInst + 1
            rs2 = instruction[-25:-20]
            rs1 = instruction[-20:-15]
            offset = instruction[0] + instruction[-8] + instruction[1:7] + instruction[-12:-8]

            counter = 0
            if(len(lastDest) == 1 and (rs1 == lastDest[0] or rs2 == lastDest[0]) and lastInst[0] == "0000011"):
                flagRAW = self.memory_delay+1
                flagMem = 0
                for i in range(self.memory_delay+1):
                    if(clock < nextInstClock["M"] - 1):
                        counter = counter + 1
                        self.wrapper_decode(instruction, clock)
                        clock = clock+1
                        flagRAW = counter

                    elif(clock == nextInstClock["M"] - 1 and counter != 0):
                        self.wrapper_decode(instruction, clock)
                        counter = counter + 1
                        clock = clock+1
                        flagRAW = counter
                        break

                    elif(clock == nextInstClock["M"] - 1 and counter == 0):
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

                    else:
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

            elif(flagMem == 2):
                for i in range(self.memory_delay):
                    self.wrapper_decode(instruction, clock)
                    clock = clock+1
                flagMem = flagMem - 1

            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1
            
            lastDest.append(-1)
            lastInst.append(-1)

            nextInstClock["D"] = clock
            self.execute_4(opcode, instruction, rs1,
                           rs2, offset, clock=max(clock, nextInstClock["E"]))

            # BEQ

        elif (opcode == "0110011"):
            noOfRegInst = noOfRegInst + 1
            rs1 = instruction[-20:-15]
            rd = instruction[-12:-7]
            rs2 = instruction[-25:-20]
            diff1 = instruction[0:5]
            diff2 = instruction[-15:-12]

            counter = 0
            if(len(lastDest) == 1 and (rs1 == lastDest[0] or rs2 == lastDest[0]) and lastInst[0] == "0000011"):
                flagRAW = self.memory_delay+1
                flagMem = 0
                for i in range(self.memory_delay+1):
                    if(clock < nextInstClock["M"] - 1):
                        counter = counter + 1
                        self.wrapper_decode(instruction, clock)
                        clock = clock+1
                        flagRAW = counter

                    elif(clock == nextInstClock["M"] - 1 and counter != 0):
                        self.wrapper_decode(instruction, clock)
                        counter = counter + 1
                        clock = clock+1
                        flagRAW = counter
                        break

                    elif(clock == nextInstClock["M"] - 1 and counter == 0):
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

                    else:
                        l.write("\nclock - "+str(clock)+"\n")
                        for i in range(len(self.reg)):
                            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                        l.write("\n \n PC - "+str(self.pc)+"\n")
                        l.write(" decode instruction - " +
                                str(instruction)+"\n \n")
                        l.write(" decode is not stalled " + "\n \n")
                        clock = clock+1
                        flagRAW = 0
                        break

            elif(flagMem == 2):
                    for i in range(self.memory_delay):
                        self.wrapper_decode(instruction, clock)
                        clock = clock+1
                    flagMem = flagMem - 1

            else:
                l.write("\nclock - "+str(clock)+"\n")
                for i in range(len(self.reg)):
                    l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

                l.write("\n \n PC - "+str(self.pc)+"\n")
                l.write(" decode instruction - " +
                        str(instruction)+"\n \n")
                l.write(" decode is not stalled " + "\n \n")
                clock = clock+1

            lastDest.append(rd)
            lastInst.append(opcode)

            if (diff1 == "00000" and diff2 == "000"):
                nextInstClock["D"] = clock
                self.execute_5(opcode, instruction, rs1, rs2, rd,
                               "add", self.reg, clock=max(clock, nextInstClock["E"]))

            elif (diff1 == "01000" and diff2 == "000"):
                nextInstClock["D"] = clock
                self.execute_5(opcode, instruction, rs1, rs2, rd,
                               "sub", self.reg, clock=max(clock, nextInstClock["E"]))

            elif (diff1 == "00000" and diff2 == "110"):
                nextInstClock["D"] = clock
                self.execute_5(opcode, instruction, rs1, rs2, rd,
                               "or", self.reg, clock=max(clock, nextInstClock["E"]))

            elif (diff1 == "00000" and diff2 == "111"):
                nextInstClock["D"] = clock
                self.execute_5(opcode, instruction, rs1, rs2, rd,
                               "and", self.reg, clock=max(clock, nextInstClock["E"]))

            elif (diff1 == "01000" and diff2 == "101"):
                nextInstClock["D"] = clock
                self.execute_5(opcode, instruction, rs1, rs2, rd,
                               "sra", self.reg, clock=max(clock, nextInstClock["E"]))

            elif (diff1 == "00000" and diff2 == "101"):
                nextInstClock["D"] = clock
                self.execute_5(opcode, instruction, rs1, rs2, rd,
                               "srl", self.reg, clock=max(clock, nextInstClock["E"]))

    def wrapper_decode(self, instruction, clock):
        l.write("\nclock - "+str(clock)+"\n")
        for i in range(len(self.reg)):
            l.write("reg "+str(i)+" : "+str(self.reg[i])+", ")

        l.write("\n \n PC - "+str(self.pc)+" \n")
        l.write(" decode instruction - " + str(instruction)+"\n \n")
        l.write(" decode is stalled " + "\n \n")
        self.dataStallCounter = self.dataStallCounter + 1
