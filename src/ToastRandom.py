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

        #init a blank schedule object
        schedule = self.initSchedule()
        self.scheduleEngineering(schedule)

        #create blocks from all programs and sort by difficulty/importance
        self.createProgramBlocks()
        self.sortBlocks()

        #for each block, score every possible slot, sort, and pick one from the best to schedule
        for block in self.blocks:
            #print ('block: ', block['ktn'], block['instr'], block['size'], block['order'], block['type'])
            self.initBlockSlots(block)
            self.scoreBlockSlots(schedule, block)
            slot = self.pickRandomBlockSlot(block)
            if slot == None: 
                print (f"WARNING: No valid slots found for block program {block['ktn']}, instr {block['instr']}")
                continue
            self.assignBlockToSchedule(
                schedule,
                block['tel'], 
                slot['date'], 
                slot['index'],
                block 
            )

        return schedule


    def createProgramBlocks(self):
        '''
        For each program, get all schedulable blocks and add extra info to them for indexing, scoring, etc
        '''
        #todo: for instruments that prefer runs, use 'num' to group together consecutive blocks
        self.blocks = []
        for ktn, program in self.programs.items():
            for progInstr in program['instruments']:
                for block in progInstr['blocks']:
                    instr = progInstr['instr']                    
                    block['progInstr']  = progInstr
                    block['instr']      = instr
                    block['ktn']        = ktn
                    block['tel']        = self.instruments[instr]['tel']
                    block['type']       = program['type'].lower()
                    block['num']        = 1
                    block['schedIndex'] = None
                    block['schedDate']  = None
                    self.blocks.append(block)


    def sortBlocks(self):
        '''
        Score and sort blocks based on size, importance, difficulty, etc.
        '''
        for block in self.blocks:

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

            #adjust if admin directive
            if 'adminBlockOrderMult' in block['progInstr']:
                block['order'] *= block['progInstr']['adminBlockOrderMult']

        #final sort by order
        blocksSorted = sorted(self.blocks, key=lambda k: k['order'], reverse=True)
        self.blocks = blocksSorted


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
                slot['score'] = 0
                continue

            #check for telescope shutdowns
            if self.isTelShutdown(block['tel'], slot['date']):
                slot['score'] = 0
                continue

            #check for instrument unavailability
            if self.isInstrShutdown(block['instr'], slot['date']):
                slot['score'] = 0
                continue

            #check for assigned
            if not self.isSlotAvailable(schedule, block['tel'], slot['date'], slot['index'], block['size']):
                slot['score'] = 0
                continue

            #check for program dates to avoid
            prog = self.programs[block['ktn']]
            if slot['date'] in prog['datesToAvoid']:
                slot['score'] = 0
                continue

            #check for instr incompatibility
            if not self.checkInstrCompat(block['instr'], schedule, block['tel'], slot['date']):
                slot['score'] = 0
                continue

            #check for adjacent reconfig incompatibilities
            if not self.checkReconfigCompat(block['instr'], schedule, block['tel'], slot['date']):
                slot['score'] = 0
                continue

            #=========== SLOT SCORING ===============

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

            #consider previous and next night, same instrument is better (ie less reconfigs)
            numAdjExact, numAdjBase = self.getNumAdjacentInstrDates(block['instr'], schedule, block['tel'], slot['date'])
            slot['score'] += numAdjExact * self.config['adjExactInstrScore']
            slot['score'] += numAdjBase  * self.config['adjBaseInstrScore']

            #score added for slot if it fills beginning or end slots
            #todo: more should be added if it fits perfectly to complete night
            if self.config['slotPerc'] < block['size'] < 1.0:
                if (slot['index'] == 0) or (slot['index']*self.config['slotPerc'] + block['size'] == 1.0):
                    slot['score'] += self.config['outerSlotScore']

            #score added if other slots are filled already on this date
            numBlocks = self.getNumBlocksScheduledOnDate(schedule, block['tel'], slot['date'])
            if numBlocks > 0: slot['score'] += self.config['avoidEmptyDatesScore']


            #todo: add priority target score
            #slot['score'] += self.getTargetScore(slot['date'], block['ktn'], slot['index'], block['size'])

            #todo: add random fluctuations here or keep pickRandomBlockSlot thing?

            assert slot['score'] > 0, f'ERROR: Slot score must be positive: {block}, {slot}'
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
        print ('score1: ', score)
        score += self.getInstrSwitchScore(schedule)
        print ('score2: ', score)
        score += self.getReconfigScore(schedule)
        print ('score3: ', score)
        score += self.getMoonPrefScore(schedule)
        print ('score4: ', score)
        score += self.getMoonIndexScore(schedule)
        print ('score5: ', score)
        score += self.getReqDateScore(schedule)
        print ('score6: ', score)
        score += self.getReqPortionScore(schedule)
        print ('score7: ', score)

        # todo: score based on priority RA/DEC targets are visible during date/portion

        # todo: can a block get a size greater or less than requested?

        # check for unassigned blocks
        score += self.getUnassignedBlockScore(schedule)
        print ('score8: ', score)

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
                for block in night['slots']:
                    if block == None: continue
                    if lastInstr != None and lastInstr != block['instr']:
                        count += 1
                    lastInstr = block['instr']
        score = count * self.config['schedInstrSwitchPenalty']
        return score


    def getReconfigScore(self, schedule):
        '''
        Penalized score based on how many times we switch instruments the next night, ie reconfigs.
        NOTE: Only certain instrument changes require reconfig as defined in config['instrSplitIncompat']
        '''
        #todo: This is not quite accurate.  We really need to define instrument positions and track state changes
        #for instance MOSFIRE switch to LRIS days later is still a reconfig.
        count = 0
        prevInstrs = []
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                curInstrs = self.getDistinctNightInstrs(night['slots'])
                for curInstr in curInstrs:
                    if curInstr not in self.config['instrSplitIncompat']: continue
                    for prevInstr in prevInstrs:
                        prevInstrBase = self.getInstrBase(prevInstr)
                        if prevInstr in self.config['instrSplitIncompat'][curInstr]:
                            print (f': test: reconfig on {date}: {prevInstr} to {curInstr}')
                            count += 1
                        elif prevInstrBase in self.config['instrSplitIncompat'][curInstr]:
                            print (f': test2: reconfig on {date}: {prevInstrBase} to {curInstr}')
                            count += 1
                prevInstrs = curInstrs
        score = count * self.config['schedReconfigPenalty']
        return score


    def getMoonPrefScore(self, schedule):
        '''
        Sched score based on which moon pref we obtained for block.
        '''
        score = 0
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                for block in night['slots']:
                    if block == None: continue
                    if not block['progInstr']: continue
                    if not block['progInstr']['moonPrefLookup']: continue
                    pref = block['progInstr']['moonPrefLookup'][date]
                    score += self.config['schedMoonPrefScore'][pref]
        return score


    def getMoonIndexScore(self, schedule):
        '''
        Score based on whether we hit requested moonIndex
        '''
        score = 0
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                for block in night['slots']:
                    if block == None: continue
                    if 'moonIndex' not in block: continue
                    if date in self.moonIndexDates[block['moonIndex']]:
                        score += self.config['schedMoonIndexScore']
        return score


    def getReqDateScore(self, schedule):
        '''
        Penalty score based on whether or not we hit requested date
        '''
        score = 0
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                for block in night['slots']:
                    if block == None: continue
                    if 'reqDate' not in block: continue
                    if not block['reqDate']: continue
                    if date != block['reqDate']:
                        score += self.config['schedReqDatePenalty']
        return score


    def getReqPortionScore(self, schedule):
        '''
        Penalty score based on whether or not we hit requested portion
        '''
        score = 0
        for telkey, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                for block in night['slots']:
                    if block == None: continue
                    if 'reqPortion' not in block: continue
                    if not block['reqPortion']: continue
                    if not self.isReqPortionMatch(block['reqPortion'], block['schedIndex']):
                        score += self.config['schedReqPortionPenalty']
        return score


    def getUnassignedBlockScore(self, schedule):
        '''
        Penalty score for orphaned blocks
        '''
        score = 0
        for block in self.blocks:
            if 'schedDate' not in block or not block['schedDate']:
                score += self.config['schedOrphanBlockPenalty']
        return score


