from random import randrange, shuffle, random, uniform, randint
import math
import sys
import numpy as np
import pprint
import statistics
import time

import logging
log = logging.getLogger('toast')

from scheduler import Scheduler


class SchedulerRandom(Scheduler):

    def __init__(self, configFile):

        # Call the parent init
        super().__init__(configFile)


    def createSchedule(self, runCount):

        #Loop and create X number of schedules and take the one that scores best.
        #todo: should we store a running top N?
        start = time.time()
        for i in range(0, runCount):
    
            schedule = self.createScheduleRandom()
            self.markScheduleWarnings(schedule)
            self.scoreSchedule(schedule)
            score = schedule['meta']['score']
            print (f"sched {i}: score = {score}")
            if self.schedule == None or score > self.schedule['meta']['score']:
                self.schedule = schedule
            self.makeOrderAdjustments(schedule['blocks'])

        end = time.time()
        print('Elapsed time: ', round(end-start, 2), ' seconds')


    def createScheduleRandom(self):

        #init a blank schedule object and pre-schedule fixed things
        schedule = self.initSchedule()

        #create blocks from all programs and sort by difficulty/importance
        schedule['blocks'] = self.createProgramBlocks()
        schedule['groups'] = self.createBlockGroups(schedule['blocks'])
        schedule['blocks'] = self.sortBlocks(schedule['blocks'], schedule['groups'])

        #for each block, score every possible slot, sort, and pick one from the best to schedule
        for block in schedule['blocks']:
            #print ('block: ', block['ktn'], block['instr'], block['size'], round(block['order'],1), block['type'])
            self.initBlockSlots(block)
            self.scoreBlockSlots(schedule, block)
            slot = self.pickRandomBlockSlot(block)
            if slot == None: 
                print (f"WARNING: No valid slots found for block id {block['id']}, program {block['ktn']}, instr {block['instr']}")
                continue
            self.assignBlockToSchedule(
                schedule,
                block['tel'], 
                slot['date'], 
                slot['index'],
                block 
            )

        return schedule


    def createBlockGroups(self, blocks):
        '''
        Find all blocks that are same program same or adjacent moon phase and add them to a group.
        '''

        #Per program, find only isolated or adj pair moon indexes
        #TODO: Only doing same moonIndex for now.  Add adjacency check.  NOTE: 3 adjacent phases is not a group.

        groups1 = {}
        for block in blocks:
            if not block['moonIndex']: continue
            key = f"{block['ktn']}-m{block['moonIndex']}"
            if key not in groups1: groups1[key] = []
            groups1[key].append(block)

        groups2 = {}
        for key, group in groups1.items():
            if len(group) == 1:
                group[0]['groupIdx'] = None
                continue
            group2 = []
            for partner in group:
                group2.append(partner['id'])
                partner['groupIdx'] = key
            groups2[key] = group2

        return groups2


    def createProgramBlocks(self):
        '''
        For each program, create all schedulable blocks and add extra info to them for indexing, scoring, etc
        '''
        #todo: for instruments that prefer runs, use 'num' to group together consecutive blocks
        blocks = []
        for ktn, program in self.programs.items():
            for progInstr in program['instruments']:
                for blockData in progInstr['blocks']:

                    #create block object and blindly add in key data from json input
                    block = self.initBlock()
                    for key, data in blockData.items():
                        block[key] = data

                    #assign some other misc vars
                    block['instr']     = progInstr['instr']                    
                    block['tel']       = self.instruments[progInstr['instr']]['tel']
                    block['type']      = program['type'].lower()
                    block['ktn']       = ktn                    
                    block['progInstr'] = progInstr
                    block['num']       = 1

                    #add to list
                    blocks.append(block)

        #add engineering blocks
        #note: engineering data should have schedDate and schedIndex defined
        id = -1
        for eng in self.engineering:
            block = self.initBlock()
            block['id'] = id = id-1
            for key, data in eng.items():
                block[key] = data
            blocks.append(block)

        return blocks


    def sortBlocks(self, blocks, groups):
        '''
        Score and sort blocks based on size, importance, difficulty, etc.
        '''
        for block in blocks:

            block['order'] = 0

            #raw score is size
            #todo: use block['num']?
            #todo: how can we apply exponential?
            block['order'] += (block['size'] * self.config['blockOrderSizeMult']) + self.config['blockOrderSizeScore']

            #adjust if requested date
            if block['reqDate']: 
                block['order'] += self.config['blockOrderReqDateScore']

            #adjust if requested portion
            if block['reqPortion']: 
                block['order'] += self.config['blockOrderReqPortionScore']

            #adjust by moonIndex type
            if block['moonIndex'] != None:
                moonType = self.moonPhases[block['moonIndex']]['type']
                block['order'] += self.config['blockOrderMoonTypeScore'][moonType]
             
            #adjust by moonprefs strictness
            if block['progInstr'] != None:
                moonPrefStrict = self.getMoonPrefStrictness(block['progInstr']['moonPrefs'])
                block['order'] += moonPrefStrict * self.config['blockOrderMoonPrefStrictScore']

            #adjust if cadence
            if block['type'].lower() == 'cadence': 
                block['order'] += self.config['blockOrderCadenceScore']

            #adjust if grouped
            if block['groupIdx']: 
                block['order'] += self.config['blockGroupedScore']

            #see if fixed order multiplier defined
            if block['orderMult']: 
                block['order'] *= block['orderMult']

            #see if order needs adjusting if not scheduled
            if 'id' in block and block['id'] in self.blockOrderLearnAdjusts:
                adjust = self.blockOrderLearnAdjusts[block['id']]
                if adjust > 0: 
                    block['order'] += adjust

            #random fluctuations (plus/minus perc adjust)
            bormRand = uniform(-1*self.config['blockOrderRandomScoreMult'], self.config['blockOrderRandomScoreMult'])
            block['order'] += block['order'] * bormRand

        #sort by order
        blocks = sorted(blocks, key=lambda k: k['order'], reverse=True)

        #random index fluctuations (more effective at moving things stuck with high or low scores)
        num = len(blocks)
        if self.config['blockOrderRandomScoreMult']:
            rng = int(num * self.config['blockOrderRandomScoreMult'])
            for idx in range(0, num):                
                block = blocks.pop(idx)
                newidx = idx + randint(-1*rng, rng)
                if   newidx < 0   : newidx = 0
                elif newidx >= num: newidx = num-1
                blocks.insert(newidx, block)

        #if a block is in a group, find partners and move them up adjacent
        newBlocks = []
        moved = {}
        while len(blocks):
            block = blocks.pop(0)
            newBlocks.append(block)
            if block['groupIdx'] == None: continue
            for pid in groups[block['groupIdx']]:
                if pid == block['id']: continue
                idx = next((idx for idx, item in enumerate(blocks) if item["id"] == pid), False)
                if idx is False: continue
                partner = blocks.pop(idx)
                newBlocks.append(partner)
        blocks = newBlocks

        #apply institutional balancing
        if self.config['blockOrderInstBalance']: 
            blocks = self.balanceBlocksByInstitution(blocks)

        #if any blocks are fixed scheduled, bump those to the top
        num = len(blocks)
        for idx in range(0, num):                
            block = blocks[idx]
            if block['schedDate']: 
                block = blocks.pop(idx)
                blocks.insert(0, block)

        #re-assign final results
        return blocks


    def balanceBlocksByInstitution(self, blocks):

        #arrange blocks by institution first letter
        insts = {}
        for block in blocks:
            ktn = block['ktn']
            letter = 'none'
            if ktn and '_' in ktn:
                sem, progid = ktn.split('_')
                letter = progid[0]
            if letter not in insts: insts[letter] = []
            insts[letter].append(block)

        #get avg length of letter array
        lens = []
        for letter, inst in insts.items():
            lens.append(len(inst))
        avg = math.floor(statistics.mean(lens))

        #get number to pop off array per inst
        numPops = {}
        for letter, inst in insts.items():
            numPops[letter] = 1 + math.floor(len(inst)/avg)
            if letter in self.config['blockOrderInstBalanceAdjusts']:
                adjust = self.config['blockOrderInstBalanceAdjusts'][letter]
                numPops[letter] += adjust

        #loop thru inst letters until done popping off all blocks
        newblocks = []
        ltrIdx = 0
        numEmpty = 0
        letters = list(insts.keys())
        shuffle(letters)
        while numEmpty <= len(letters):
            l = ltrIdx % len(letters)
            letter = letters[l]
            ltrIdx += 1
            inst = insts[letter]
            if len(inst) > 0:
                numEmpty = 0
                for i in range(0, numPops[letter]):
                    if len(inst) > 0:
                        block = insts[letter].pop(0)
                        newblocks.append(block)
                        #keep group blocks together
                        #todo: do we really want to do this? Also, as coded this gives advantage to insts with lots of groups.
                        if block['groupIdx']: i -= 1   
            else:
                numEmpty += 1

        return newblocks


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
        
        #Score each slot (raw score ignores whether slot is available; useful for manual swapping later on)
        for slot in block['slots']:

            slot['score'] = 0

            #PRE-SCHEDULED: check if fixed scheduled date or slot. Skip all others so their score is zero.
            if block['schedDate']:
                if slot['date']  == block['schedDate'] : slot['score'] += 100
                if slot['index'] == block['schedIndex']: slot['score'] += 100
            else:
                slot['score'] = self.scoreBlockSlot(schedule, block, slot['date'], slot['index'])


    def scoreBlockSlot(self, schedule, block, date, index, skipId=None):

        #default score zero is unschedulable
        score = 0

        #check slot unavailable
        if not self.isSlotAvailable(schedule, block['tel'], date, index, block['size'], skipId=skipId):
            return 0

        #check if totally invalid
        if not self.isSlotValid(schedule, block, date, index, verbose=False):
            return 0

        #moon preference factor (progInstr['moonPrefs'])
        #NOTE: unspecified defaults to Neutral
        if block['progInstr']:
            if block['progInstr']['moonPrefLookup']: pref = block['progInstr']['moonPrefLookup'][date]
            else                                   : pref = "N"
#todo: testing this hard X rule out
            if pref == 'X':
                return 0
            score += self.config['moonDatePrefScore'][pref]

        #moon scheduled factor (block['moonIndex'])
        if block['moonIndex'] != None:
            if date in self.moonIndexDates[block['moonIndex']]:
                score += self.config['reqMoonIndexScore']

        #requested date factor (block['reqDate'])
        if block['reqDate'] and block['reqDate'] == date:
            score += self.config['reqDateIndexScore']

        #requested date portion (block['reqPortion'])
        if self.isReqPortionMatch(block['reqPortion'], index, block['size']):
            score += self.config['reqPortionIndexScore']

        #score added if we hit dateOptions
        priority = self.getDateOptionMatchPriority(block, date)
        if priority: score += self.config['reqDateOptionsScore'] * 1/priority

        #consider if split night, same instrument better than split different instrument
        if self.isScheduledInstrMatch(block['instr'], schedule, block['tel'], date):
            score += self.config['scheduledInstrMatchScore']

        #consider previous and next night, same instrument is better (ie less reconfigs)
        numExact, numBase, numEmpty, numLoc = self.getNumAdjacentInstrDates(block['instr'], schedule, block['tel'], date)
        score += numExact * self.config['adjExactInstrScore']
        score += numBase  * self.config['adjBaseInstrScore']
        score += numEmpty * self.config['adjEmptyInstrScore']
        score += numLoc   * self.config['adjLocInstrScore']

        #consider previous and next night, same group is better (ie create runs)
        numAdjProg, numAdjGroup = self.getNumAdjacentPrograms(block['ktn'], block['groupIdx'], schedule, None, date)
        score += numAdjProg  * self.config['adjProgramScore']
        score += numAdjGroup * self.config['adjGroupScore']

        #penalty for same program same night
        numSamePrograms = self.getNumSameProgramsOnDate(block['ktn'], schedule, None, date)
        score += numSamePrograms * self.config['sameProgramPenalty']

        #score added for slot if it fills beginning or end slots
        #todo: more should be added if it fits perfectly to complete night
        if self.config['slotPerc'] < block['size'] < 1.0:
            if (index == 0) or (index*self.config['slotPerc'] + block['size'] == 1.0):
                score += self.config['outerSlotScore']

        #score added if other slots are filled already on this date
        numBlocks = self.getNumBlocksScheduledOnDate(schedule, block['tel'], date)
        if numBlocks > 0: score += self.config['avoidEmptyDatesScore']

        #todo: add priority target score
        #score += self.getTargetScore(date, block['ktn'], index, block['size'])

        #random fluctuations (plus/minus perc adjust)
        bormRand = uniform(-1*self.config['slotScoreRandomMult'], self.config['slotScoreRandomMult'])
        score += score * bormRand

        return score


    def getTargetScore(self, date, ktn, index, size):

        #todo: find out how well this date time range overlaps with all priority targets' airmass and give score
        #note: use lst@midnight 
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

#todo: trying just using ordering and random score fluctuation
#        return slotsSorted[0]

        # #keep only those values that are within x% of best value and pick randomly from those
        finalSlots = []
        max = slotsSorted[0]['score']
        for slot in slotsSorted:
            perc = slot['score'] / max
            if perc < (1 - self.config['slotScoreTopPerc']): continue
            finalSlots.append(slot)

        #pick weighted random item
        #todo: add variable to apply exponential to weighting
        randItem = Scheduler.getListItemByWeightedRandom(finalSlots, 'score')
        return randItem


    #######################################################################
    # MARK WARN FUNCTIONS
    #######################################################################

    def markScheduleWarnings(self, schedule):

        #check warnings for all blocks
        for block in schedule['blocks']:

            #not scheduled?
            block['warnSchedDate'] = ''
            if 'schedDate' not in block or not block['schedDate']:
                block['warnSchedDate'] = 1

            #not scheduled on requested date?
            block['warnReqDate'] = ''
            if 'reqDate' in block and block['reqDate']:
                if block['schedDate'] != block['reqDate']:
                    block['warnReqDate'] = block['reqDate']

            #not scheduled on requested date options
            block['warnReqDateOptions'] = ''
            block['warnReqDatePerc'] = 0
            if block['progInstr'] and 'dateOptions' in block['progInstr']:
                opts = block['progInstr']['dateOptions']
                if block['schedDate'] not in opts:
                    block['warnReqDateOptions'] = list(opts)[0][5:]
                    block['warnReqDatePerc'] = 1
                    if len(opts) > 1: block['warnReqDateOptions'] += f'+'
                else:
                    priority = opts[block['schedDate']]
                    if priority > 1:
                        block['warnReqDateOptions'] = f'p{priority}'
                        block['warnReqDatePerc'] = (priority-1)/10

            #not scheduled on requested portion of night
            block['warnReqPortion'] = ''
            if 'reqPortion' in block and block['reqPortion'] and block['schedIndex'] != None:
                if not self.isReqPortionMatch(block['reqPortion'], block['schedIndex'], block['size']):
                    block['warnReqPortion'] = block['reqPortion']

            #not scheduled on requested moon phase index?
            block['warnMoonIndex'] = ''
            if block['moonIndex'] != None and block['schedDate']:
                schedMoonIndex = self.moonDatesIndex[block['schedDate']]
                block['warnMoonIndex'] = block['moonIndex'] if (schedMoonIndex != block['moonIndex']) else ''

            #not scheduled on a preferred date?
#todo: this doesn't handle when has 'A' prefs but no 'P' prefs, and assigned is X or N
#todo: create hasPrefsA and hasPrefsP
            block['warnMoonPref'] = ''
            if block['schedDate'] and block['progInstr'] and block['progInstr']['moonPrefLookup']:
                schedPref = block['progInstr']['moonPrefLookup'][block['schedDate']]
                if schedPref not in ('P'): 
                    hasPrefs = True if set(block['progInstr']['moonPrefs']).intersection(set(['P'])) else False
                    if schedPref == 'X' or hasPrefs:
                        block['warnMoonPref'] = schedPref

            #same program scheduled same night
            block['warnSameProgram'] = ''
            num = self.getNumSameProgramsOnDate(block['ktn'], schedule, None, block['schedDate'])
            if num > 1:
                block['warnSameProgram'] = 1

            #part of run group but not adj to run
            block['warnGroup'] = ''
            if block['schedDate'] and block['groupIdx']:
                numAdjProg, numAdjGroup = self.getNumAdjacentPrograms(block['ktn'], block['groupIdx'], schedule, None, block['schedDate'])
                if block['groupIdx'] and numAdjGroup == 0:
                    block['warnGroup'] = 1


        #store list of unscheduled blocks
        schedule['unscheduledBlocks'] = []
        for block in schedule['blocks']:
            if 'schedDate' not in block or not block['schedDate']:
                schedule['unscheduledBlocks'].append(block)


    #######################################################################
    # SCORING FUNCTIONS
    #######################################################################
      
    def scoreSchedule(self, schedule):

        #overall sched score
        score = 0

        #block specific scoring
        # todo: score based blocks on priority RA/DEC targets are visible during date/portion
        # todo: can a block get a size greater or less than requested?
        for block in schedule['blocks']:

            #init all block scores to zero
            block['score'] = 0

            #Penalty score based on whether or not we hit requested date
            if block['warnReqDate']:
                block['score'] += self.config['schedReqDatePenalty']

            #Penalty score based on whether or not we hit requested date option
            if block['warnReqDateOptions']:
                block['score'] += self.config['schedReqDateOptionsPenalty'] * block['warnReqDatePerc']

            #Penalty score based on whether or not we hit requested portion
            if block['warnReqPortion']:
                block['score'] += self.config['schedReqPortionPenalty']

            #Penalty score for orphaned blocks
            if block['warnSchedDate']:
                block['score'] += self.config['schedOrphanBlockPenalty']

            #Penalty score for orphaned blocks
            if block['warnSameProgram']:
                block['score'] += self.config['schedSameProgramPenalty']

            #Penalty score for not scheduling in group
            if block['warnGroup']:
                block['score'] += self.config['schedNotGroupedPenalty']

            #Score based on which moon pref we obtained for block
            if block['progInstr'] and block['progInstr']['moonPrefLookup'] and block['schedDate']:
                date = block['schedDate']
                pref = block['progInstr']['moonPrefLookup'][date]
                block['score'] += self.config['schedMoonPrefScore'][pref]

            #Score based on whether we hit requested moonIndex
            if 'moonIndex' in block and block['moonIndex'] != None and block['schedDate']:
                date = block['schedDate']
                if date in self.moonIndexDates[block['moonIndex']]:
                    block['score'] += self.config['schedMoonIndexScore']

            score += block['score']

        #schedule specific scoring
        #todo: can we make these part of block scoring?
        score += self.getInstrSwitchScore(schedule)
        score += self.getReconfigScore(schedule)

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
                        prevInstrBase = self.instruments[prevInstr]['base'] if prevInstr in self.instruments else None
                        if prevInstr in self.config['instrSplitIncompat'][curInstr]:
                            count += 1
                        elif prevInstrBase in self.config['instrSplitIncompat'][curInstr]:
                            count += 1
                prevInstrs = curInstrs
        score = count * self.config['schedReconfigPenalty']
        return score


    def makeOrderAdjustments(self, blocks):
        '''
        Look for blocks that scored poorly and make a modest adjustment to order score.
        '''

        #get mean and min of block scores
        scores = np.array([k['score'] for k in blocks])
        mean = scores.mean()
        std  = scores.std()
        mini = scores.min()

        #3 levels of adjustment amounts
        mini1 = (mean - mini) / 4 * -1
        mini2 = (mean - mini) / 4 * -2
        mini3 = (mean - mini) / 4 * -3

        #make adjustment based on score
        for block in blocks:
            if 'id' not in block: continue
            bid = block['id']

            adjust = 0
            if   (block['score'] < (mean - std*3)): adjust = 1.0 * self.config['blockOrderProblemLearnScore']
            elif (block['score'] < (mean - std*2)): adjust = 0.5 * self.config['blockOrderProblemLearnScore']
            elif (block['score'] < (mean - std*1)): adjust = 0.2 * self.config['blockOrderProblemLearnScore']
            elif (block['score'] < (mean - std*0)): adjust = 0.1 * self.config['blockOrderProblemLearnScore']

            if bid not in self.blockOrderLearnAdjusts: 
                self.blockOrderLearnAdjusts[bid] = 0

            #increase or decay
            if adjust > 0: self.blockOrderLearnAdjusts[bid] += adjust
            else         : self.blockOrderLearnAdjusts[bid] *= 0.80

            #clip
            maxi = self.config['blockOrderProblemLearnMax']
            self.blockOrderLearnAdjusts[bid] = np.clip(self.blockOrderLearnAdjusts[bid], 0, maxi)


    def printOrderAdjusts(self, schedule, tel=None):

        data = []
        for block in schedule['blocks']:
            if tel and block['tel'] != tel: continue
            if 'id' not in block: continue
            if block['id'] not in self.blockOrderLearnAdjusts: continue
            adjust = self.blockOrderLearnAdjusts[block['id']]
            data.append({'block':block, 'adjust':adjust})

        for d in sorted(data, key = lambda i: i['adjust']):
            block = d['block']
            print (f"{round(d['adjust'], 1)}\t{block['id']}\t{block['ktn']}\t{block['instr']}\t")


    def printGroups(self, schedule, tel=None):

        for key, group in schedule['groups'].items():
            print (f"{key}: ", group)


    def showBlockOrders(self, schedule, tel=None):

        print ("Showing order that blocks were scheduled with order score:")
        print ("(NOTE: Order may not reflect score order if config blockOrderRandomScoreMult was used)")
        print(f"id\tscore\tsize\ttype\n-------------------------------------")
        for block in schedule['blocks']:
            print (f"{block['id']}\t{block['order']:.2f}\t{block['size']}\t{block['type']}")


    def showBlockSlotScores(self, schedule, blockId, topN):
        print ("Not implemented yet")
#todo: do a slot['postscore'] that considers current state of schedule (some scoring functions won't work as assumed!)

        # #NOTE: rawscore used as list driver 
        # #find block
        # block, slots, slotIdx = self.findScheduleBlockById(schedule, blockId)
        # if not block:
        #     print (f"ERROR: block id {blockId} not found!")
        #     return False

        # #Filter out scores zero or less and order slots by score
        # slots = block['slots']
        # slotsSorted = sorted(slots, key=lambda k: k['rawscore'], reverse=True)

        # max = slotsSorted[0]['rawscore']
        # print(f"\n(* = not within {self.config['slotScoreTopPerc']} slotScoreTopPerc)")
        # print(f"date\t\tindex\tscore\tused")
        # for i, slot in enumerate(slotsSorted):
        #     if topN and i >= topN: continue
        #     avail = 'x' if slot['score'] <= 0 else ''
        #     print (f"{slot['date']}\t{slot['index']}\t{slot['rawscore']}\t{avail}")


