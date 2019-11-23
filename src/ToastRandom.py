from Toast import *
from random import randrange, shuffle, random, uniform
import math
import sys
import logging


class ToastRandom(Toast):

    def __init__(self, semester, runCount):

        # Call the parent init
        super().__init__(semester)

        #input class vars
        self.runCount = runCount


    def createSchedule(self):

        #todo: Loop and create X number of schedules and take the one that scores best.
        bestScore = 0
        bestSchedule = None
        for i in range(0, self.runCount):
    
            schedule = self.createScheduleRandom()
            self.scoreSchedule(schedule)
            print (f"sched {i}: score = {schedule['meta']['score']}")

            if schedule['meta']['score'] >= bestScore:
                bestScore = schedule['meta']['score']
                bestSchedule = schedule

        #todo: should we store all schedules in an array or keep a running top 10%?
        return bestSchedule


    def createScheduleRandom(self):

        #init a schedule object
        schedule = self.initSchedule()

        #create blocks from all programs
        blocks = self.createProgramBlocks(self.programs)
        blocks = self.sortBlocks(blocks)

        #for each block, init slots to try and score each slot
        for block in blocks:
            #print ('block: ', block['ktn'], block['instr'], block['size'], block['order'])
            self.initBlockSlots(block)
            self.scoreBlockSlots(schedule, block)
            slot = self.pickRandomBlockSlot(block)
            if slot == None: 
                print (f"WARNING: No valid slots found for block program {block['ktn']}, instr {block['instr']}")
                continue
            self.assignToSchedule(
                schedule,
                block['tel'], 
                slot['date'], 
                slot['index'], 
                block['size'], 
                block['ktn'],
                block['instr']
            )

        return schedule


    def createProgramBlocks(self, programs):

        #For each program, get all schedulable blocks
        #todo: for instruments that prefer runs, use 'num' to group together consecutive blocks
        #todo: use pointers or indexes to parent program
        blocks = []
        for ktn, program in programs.items():
            for progInstr in program['instruments']:
                for block in progInstr['blocks']:

                    #add extra info to block data
                    instr = progInstr['instr']                    
                    block['progInstr'] = progInstr
                    block['instr']     = instr
                    block['ktn']       = ktn
                    block['tel']       = self.instruments[instr]['tel']
                    block['type']      = program['type'].lower()
                    block['num']       = 1

                    blocks.append(block)
        return blocks


    def sortBlocks(self, blocks):

        #score order for blocks
        for block in blocks:

            #raw score is size
            block['order'] = block['size'] * block['num']

            #adjust if requested date
            if block['reqDate']: 
                block['order'] += self.config['blockOrderReqDateScore']

            #adjust if requested portion
            if block['reqPortion']: 
                block['order'] += self.config['blockOrderReqPortionScore']

            #adjust if cadence
            if block['type'].lower() == 'cadence': 
                block['order'] *= self.config['blockOrderCadenceMult']

            #adjust by moonIndex type
            moonType = self.moonPhases[block['moonIndex']]['type']
            block['order'] *= self.config['blockOrderMoonTypeMult'][moonType]
             
            #random fluctuations (plus/minus perc adjust)
            bormRand = uniform(-1*self.config['blockOrderRandomMult'], self.config['blockOrderRandomMult'])
            block['order'] += block['order'] * bormRand

        #final sort by order
        blocksSorted = sorted(blocks, key=lambda k: k['order'], reverse=True)
        return blocksSorted


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


    def scoreBlockSlots(self, schedule, block):
        
        #todo: should we prevent small sizes on the same program from being scheduled on the same night? 

        #For each slot, score it from 0 to 1 based on several factors
        for slot in block['slots']:
            # print (f"scoring slot: {slot}")

            #default score of 1
            slot['score'] = 0

            #=========== SKIP CHECKS ===============

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
            if not self.isSlotAvailable(schedule, block['tel'], slot['date'], slot['index'], block['size']):
                slot['score'] = 0
                # print ("\tOVERLAP")
                continue

            #check for program dates to avoid
            prog = self.programs[block['ktn']]
            if slot['date'] in prog['datesToAvoid']:
                slot['score'] = 0
                # print ("\tBAD PROGRAM DATE")
                continue

            #check for instr incompatibility
            if not self.checkInstrCompat(block['instr'], schedule, block['tel'], slot['date']):
                slot['score'] = 0
                continue

            #=========== SCORING ===============

            #moon preference factor (progInstr['moonPrefs'])
            if block['progInstr']['moonPrefLookup']: pref = block['progInstr']['moonPrefLookup'][slot['date']]
            else                                   : pref = "N"
            slot['score'] += self.config['moonDatePrefScore'][pref]

            #moon scheduled factor (block['moonIndex'])
            if slot['date'] in self.moonIndexDates[block['moonIndex']]:
                slot['score'] += self.config['reqMoonIndexScore']

            #requested date factor (block['reqDate'])
            if block['reqDate'] and block['reqDate'] == slot['date']:
                slot['score'] += self.config['reqDateIndexScore']

            #requested date portion (block['reqPortion'])
            if self.isReqPortionMatch(block['reqPortion'], slot['index']):
                slot['score'] += self.config['reqPortionIndexScore']

            #consider if split night, same instrument better than split different instrument
            if self.isScheduledInstrMatch(block['instr'], schedule, block['tel'], slot['date']):
                slot['score'] += self.config['scheduledInstrMatchScore']

            #todo: consider previous and next night, same instrument is better (ie less reconfigs)
            numAdjExact, numAdjBase = self.getNumAdjacentInstrDates(block['instr'], schedule, block['tel'], slot['date'])
            slot['score'] += numAdjExact * self.config['adjExactInstrScore']
            slot['score'] += numAdjBase  * self.config['adjBaseInstrScore']

            #add priority target score
            #todo: not implented
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

        #empty?
        if not slotsSorted:
            return None

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










