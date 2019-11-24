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
        bestScore = None
        bestSchedule = None
        for i in range(0, self.runCount):
    
            schedule = self.createScheduleRandom()
            self.scoreSchedule(schedule)
            print (f"sched {i}: score = {schedule['meta']['score']}")

            if bestScore == None or schedule['meta']['score'] >= bestScore:
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
            print ('block: ', block['ktn'], block['instr'], block['size'], block['order'], block['type'])
            self.initBlockSlots(block)
            self.scoreBlockSlots(schedule, block)
            slot = self.pickRandomBlockSlot(block)
            if slot == None: 
                print (f"WARNING: No valid slots found for block program {block['ktn']}, instr {block['instr']}")
                continue
            block['index'] = slot['index']
            block['date']  = slot['date']
            self.assignBlockToSchedule(
                schedule,
                block['tel'], 
                slot['date'], 
                slot['index'],
                block 
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
        '''
        Sort blocks by those that are more important and/or harder to schedule first.
        '''
        ## todo: bump up order of blocks that have just a few Ps and As
        ## (ignore empty array and all Neutrals)

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

            #adjust by moonIndex type
            moonType = self.moonPhases[block['moonIndex']]['type']
            block['order'] += self.config['blockOrderMoonTypeScore'][moonType]
             
            #adjust by moonprefs strictness
            moonPrefStrict = self.getMoonPrefStrictness(block['progInstr']['moonPrefs'])
            block['order'] += moonPrefStrict * self.config['blockOrderMoonPrefStrictScore']

            #adjust if cadence
            if block['type'].lower() == 'cadence': 
                block['order'] *= self.config['blockOrderCadenceMult']

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
            for index in range(0, self.numSlots):
                slot = {}
                slot['date']  = date
                slot['index'] = index
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


    #######################################################################
    # SCORING FUNCTIONS
    #######################################################################
      
    def scoreSchedule(self, schedule):

        score = 0
        score += self.getInstrSwitchScore(schedule)
        print (score)
        score += self.getReconfigScore(schedule)
        print (score)
        score += self.getMoonPrefScore(schedule)
        print (score)

        # todo: score if we hit reqMoonIndex

        # todo: score if we hit reqDate

        # todo: score if we hit reqPortion

        # todo: alter score based on priority RA/DEC list?

        # todo: can a block get a size greater or less than requested?

        # todo: score based on minimal runs for instruments that want runs

        # todo: should we check for unassigned blocks?

        schedule['meta']['score'] = score


    def getInstrSwitchScore(self, schedule):
        '''
        Penalized score based on how many times we switch instruments during a night, for each night.
        NOTE: This does not count changing instruments the next night, ie reconfigs.
        '''
        count = 0
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                lastInstr = None
                for slot in night['slots']:
                    if slot == None: continue
                    if lastInstr != None and lastInstr != slot['instr']:
                        count += 1
                    lastInstr = slot['instr']
        score = count * self.config['schedInstrSwitchPenalty']
        return score


    def getReconfigScore(self, schedule):
        '''
        Penalized score based on how many times we switch instruments the next night, ie reconfigs.
        NOTE: Only certain instrument changes require reconfig
        '''
        count = 0
        prevInstrs = []
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                curInstrs = self.getDistinctNightInstrs(night['slots'])
                for curInstr in curInstrs:
                    for prevInstr in prevInstrs:
                        if curInstr in self.config['instrIncompatMatrix'][prevInstr]:
                            count += 1
                prevInstrs = curInstrs
        score = count * self.config['schedReconfigPenalty']
        return score


    def getMoonPrefScore(self, schedule):
        '''
        Penalized score based on how many times we switch instruments during a night, for each night.
        NOTE: This does not count changing instruments the next night, ie reconfigs.
        '''
        score = 0
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                for slot in night['slots']:
                    if slot == None: continue
                    if not slot['progInstr']['moonPrefLookup']: continue
                    pref = slot['progInstr']['moonPrefLookup'][date]
                    print (date, slot['ktn'], slot['index'], pref)
                    score += self.config['schedMoonPrefScore'][pref]
        return score




