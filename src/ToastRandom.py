from Toast import *
from random import randrange, shuffle, random
import math
import sys


class ToastRandom(Toast):

    def __init__(self, semester):

        # Call the parent init
        super().__init__(semester)


    def createSchedule(self):

        #todo: Loop and create X number of schedules and take the one that scores best.

        #create blocks from all programs
        blocks = self.createProgramBlocks(self.programs)
        blocks = self.randomSortBlocks(blocks)

        #for each block, init slots to try and score each slot
        for block in blocks:
            print ('block: ', block['ktn'], block['instr'], block['size'])
            self.initBlockSlots(block)
            self.scoreBlockSlots(block)
            slot = self.pickRandomBlockSlot(block)
            if slot == None: 
                print (f"No valid slots found for block program {block['ktn']}, instr {block['instr']}")
                continue
            self.assignToSchedule(block['tel'], 
                                  slot['date'], 
                                  slot['index'], 
                                  block['size'], 
                                  block['ktn'],
                                  block['instr'])


    def createProgramBlocks(self, programs):

        #For each program, get all schedulable blocks
        #todo: for instruments that prefer runs, use 'num' to group together consecutive blocks
        #todo: use pointers or indexes to parent program
        blocks = []
        for ktn, program in programs.items():
            for progInstr in program['instruments']:
                for block in progInstr['blocks']:
                    instr = progInstr['instr']
                    block['progInstr'] = progInstr
                    block['instr']     = instr
                    block['ktn']       = ktn
                    block['tel']       = self.instruments[instr]['tel']
                    block['num']       = 1
                    block['runSize']   = block['size'] * block['num']
                    blocks.append(block)
        return blocks


    def randomSortBlocks(self, blocks):

        #psuedo-randomize blocks in groups by order of size from biggest to smallest
        #todo: This might result in large runs having a uniquely big size and always going first.  Might want to prevent that.
        blocksSorted = sorted(blocks, key=lambda k: k['runSize'], reverse=True)
        lastSize = None
        blocksFinal = []
        group = []
        for i, block in enumerate(blocksSorted):
            if (lastSize == None) or (lastSize != block['runSize']) or (i == len(blocksSorted)-1):                
                if i == len(blocksSorted)-1:
                    group.append(block)
                if lastSize != None:
                    shuffle(group)
                    blocksFinal.extend(group)
                    group = []
                lastSize = block['runSize']
            group.append(block)

        return blocksFinal


    def initBlockSlots(self, block):

        #for each sized slot in each date, create a little slot object to track its fitness score
        block['slots'] = []
        for date in self.datesList:
            for pIndex in range(0, self.numSlots):
                slot = {}
                slot['date']  = date
                slot['index'] = pIndex
                slot['instr'] = block['instr']
                slot['ktn']   = block['ktn']
                block['slots'].append(slot)


    def scoreBlockSlots(self, block):
        
        #todo: should we prevent small sizes on the same program from being scheduled on the same night? 

        #For each slot, score it from 0 to 1 based on several factors
        for slot in block['slots']:
            # print (f"scoring slot: {slot}")

            #default score of 0
            slot['score'] = 0

            #check for block length versus size available length
            sizeRemain = 1 - (slot['index'] * self.config['slotPerc'])
            if (block['size'] > sizeRemain):
                # print ("\tTOO LONG")
                slot['score'] = 0
                continue

            #check for telescope shutdowns
            if self.isTelShutdown(block['tel'], slot['date']):
                # print (f"\tTELESCOPE SHUTDOWN: {block['tel']}, {slot['date']}")
                slot['score'] = 0
                continue

            #check for instrument unavailability
            if self.isInstrShutdown(block['instr'], slot['date']):
                # print (f"\tINSTRUMENT UNAVAILABLE: {block['instr']} {slot['date']}")
                slot['score'] = 0
                continue

            #check for assigned
            if not self.isSlotAvailable(block['tel'], slot['date'], slot['index'], block['size']):
                slot['score'] = 0
                # print ("\tOVERLAP")
                continue

            #check for program dates to avoid
            prog = self.programs[block['ktn']]
            if slot['date'] in prog['datesToAvoid']:
                slot['score'] = 0
                # print ("\tBAD PROGRAM DATE")
                continue

            #add moon preference score
            if block['progInstr']['moonPrefLookup']:
                pref = block['progInstr']['moonPrefLookup'][slot['date']]
                slot['score'] += self.config['moonDatePrefScore'][pref]
            else:
                slot['score'] += self.config['moonDatePrefScore']["N"]

            #add moon scheduled score
            if slot['date'] in self.moonIndexDates[block['moonIndex']]:
                slot['score'] += self.config['reqMoonIndexScore']

            #add priority target score
            slot['score'] += self.getTargetScore(slot['date'], block['ktn'], slot['index'], block['size'])

            # print (f"\tscore = {slot['score']}")


    def getTargetScore(self, date, ktn, index, size):

        #todo: find out how well this date time range overlaps with all priority targets' airmass and give score
        return 0


    def pickRandomBlockSlot(self, block):

        #Filter out scores zero or less and order slots by score
        slots = block['slots']
        slotsFiltered = []
        for slot in slots:
            if slot['score'] > 0: slotsFiltered.append(slot)
        slotsSorted = sorted(slotsFiltered, key=lambda k: k['score'], reverse=True)

        # #keep only those values that are within x% of best value and pick randomly from those
        finalSlots = []
        max = slotsSorted[0]['score']
        for slot in slotsSorted:
            perc = slot['score'] / max
            if perc < (1 - self.config['slotScoreTopPerc']): continue
            finalSlots.append(slot)

        #pick weighted random item
        #todo: add variable to apply exponential to weighting
        randItem = Toast.getListItemByWeightedRandom(finalSlots, 'score')
        return randItem










