import os
import sys
import yaml
import json
import argparse
import pandas as pd
from random import randrange, shuffle, random
from datetime import datetime as dt, timedelta
import pathlib
import time
import math
import re

import logging
log = logging.getLogger('toast')



class Scheduler(object):

    def __init__(self, semester):

        self.semester = semester

        #member class vars
        self.config = None
        self.schedule = None


    def start(self):

        self.loadConfig()

        #calc start and end date
        self.startDate, self.endDate = self.getSemesterDates(self.semester)

        #get needed input data
        self.datesList      = self.createDatesList(self.startDate, self.endDate)
        self.telescopes     = self.getTelescopes()
        self.instruments    = self.getInstruments()
        self.moonPhases     = self.getMoonPhases()
        self.nightPhases    = self.getNightPhases()
        self.instrShutdowns = self.getInstrumentShutdowns()
        self.engineering    = self.getEngineering()
        self.programs       = self.getPrograms(self.semester)

        #perform data conversion optimizations
        self.createMoonDatesIndex()
        self.createMoonIndexDates()
        self.createMoonPrefLookups()
        self.createInstrBaseNames()

        #todo: check if the total proposed hours exceeds semester hours

        #do it
        self.schedule = self.createSchedule()
        self.promptMenu()
        #self.printSchedule(self.schedule)


    def promptMenu(self):

#todo: call this base menu from child and add in child functions there
        menu = "\n"
        menu += "----------------------------------------------------------------\n"
        menu += "|                    MENU                                       |\n"
        menu += "----------------------------------------------------------------|\n"
        menu += "|  show [tel] [start day] [stop day]   Show schedule            |\n"
        menu += "|  stats                               Show stats               |\n"
        menu += "|  conflicts                           Check conflicts          |\n"
        menu += "|  blockorders  [tel]                  Show block orders        |\n"
        menu += "|  orderadjusts [tel]                  Show block order adjusts |\n"
        menu += "|  slotscores [blockId] [topN]         Show topN slot scores    |\n"
        menu += "|  move       [blockId] [date] [index] Move block               |\n"
        menu += "|  remove     [blockId]                Remove block             |\n"
        menu += "|  swap       [blockId1] [blockId2]    Swap two blocks          |\n"
        menu += "|  export [filename]                   Export to csv            |\n"
        menu += "|  q                                   Quit (or Control-C)      |\n"
        menu += "-----------------------------------------------------------------\n"
        menu += "> "

        quit = None
        autoHelp = True
        while quit is None:
            prompt = menu if autoHelp else "\n> "
            autoHelp = False
            cmds = input(prompt).split()       
            if not cmds: continue
            cmd = cmds[0]     
            if   cmd == 'q':  
                quit = True
            elif cmd == 'show':  
                tel   = cmds[1] if len(cmds) > 1 else None
                start = cmds[2] if len(cmds) > 2 else None
                end   = cmds[3] if len(cmds) > 3 else None
                self.printSchedule(self.schedule, tel=tel, start=start, end=end)
            elif cmd == 'stats':  
                self.printStats(self.schedule)
            elif cmd == 'export':  
                outFilepath = cmds[1] if len(cmds) > 1 else None
                self.exportSchedule(self.schedule, outFilepath)
            elif cmd == 'conflicts':  
                self.checkConflicts()
            elif cmd == 'orderadjusts':  
                tel   = cmds[1] if len(cmds) > 1 else None
                self.printOrderAdjusts(self.schedule, tel)
            elif cmd == 'blockorders':  
                tel   = cmds[1] if len(cmds) > 1 else None
                self.showBlockOrders(self.schedule, tel)
            elif cmd == 'move':  
                bid   = int(cmds[1]) if len(cmds) > 1 else None
                date  = cmds[2]      if len(cmds) > 2 else None
                index = int(cmds[3]) if len(cmds) > 3 else None
                self.moveScheduleBlock(self.schedule, bid, date, index)
            elif cmd == 'remove':  
                bid   = int(cmds[1]) if len(cmds) > 1 else None
                self.removeScheduleBlock(self.schedule, bid)
            elif cmd == 'swap':  
                bid1 = int(cmds[1]) if len(cmds) > 1 else None
                bid2 = int(cmds[2]) if len(cmds) > 2 else None
                self.swapScheduleBlocks(self.schedule, bid1, bid2)
            elif cmd == 'slotscores':  
                bid   = int(cmds[1]) if len(cmds) > 1 else None
                topn  = int(cmds[2]) if len(cmds) > 2 else None
                self.showBlockSlotScores(self.schedule, bid, topn)
            else:
                log.error(f'Unrecognized command: {cmd}')
                autoHelp = True


    def loadConfig(self):

        #load config
        configFile = 'config.yaml'
        assert os.path.isfile(configFile), f"ERROR: config file '{configFile}'' does not exist.  Exiting."
        with open(configFile) as f: self.config = yaml.safe_load(f)        

        #do some basic calcs from config
        self.numSlots = int(1 / self.config['slotPerc'])

    

    #######################################################################
    # ABSTRACT METHODS
    #######################################################################
    def createSchedule(self) : raise NotImplementedError("Abstract method not implemented!")



    #######################################################################
    # INPUT DATA FUNCTIONS
    #######################################################################

    def getTelescopes(self):

        data = None
        if 'telescopesFile' in self.config: 
            fp = self.config['telescopesFile']
            assert os.path.isfile(fp), f"ERROR: getTelescopes: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = yaml.safe_load(f)        
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getTelescopes: DB retrieve not implemented!"

        #convert to dict indexed by primary key
        data = self.convertDictArrayToDict(data, 'tel')
        return data


    def getInstruments(self):

        data = None
        if 'instrumentsFile' in self.config: 
            fp = self.config['instrumentsFile']
            assert os.path.isfile(fp), f"ERROR: getInstruments: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = yaml.safe_load(f)        
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getInstruments: DB retrieve not implemented!"

        #convert to dict indexed by primary key
        data = self.convertDictArrayToDict(data, 'instr')
        return data


    def getEngineering(self):

        data = None
        if 'engineeringFile' in self.config: 
            fp = self.config['engineeringFile']
            assert os.path.isfile(fp), f"ERROR: getEngineering: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = yaml.safe_load(f)        
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getEngineering: DB retrieve not implemented!"
        return data


    def getPrograms(self, semester):

        data = None
        if 'programsFile' in self.config: 
            fp = self.config['programsFile']
            assert os.path.isfile(fp), f"ERROR: getPrograms: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = json.load(f)        
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getPrograms: DB retrieve not implemented!"
        return data


    def getInstrumentShutdowns(self):

        data = None
        if self.config['instrShutdownsFile']: 
            fp = self.config['instrShutdownsFile']
            assert os.path.isfile(fp), f"ERROR: getInstrumentShutdowns: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = yaml.safe_load(f)        
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getInstrumentShutdowns: DB retrieve not implemented!"

        #convert to dict indexed by keys
        data = self.convertDateRangeToDictArray(data, 'startDate', 'endDate')
        data = self.convertDictArrayToArrayDict(data, 'instr', 'date')
        return data


    def isInstrShutdown(self, instrStr, date):
        instrs = instrStr.split('+')
        for instr in instrs:
            if instr in self.instrShutdowns: 
                shutdownDates = self.instrShutdowns[instr]
                if date in shutdownDates:
                    return True
        return False


    #######################################################################
    # SCHEDULE FUNCTIONS
    #######################################################################

    def initSchedule(self):

        #create template schedule object for each telescope
        schedule = {}

        schedule['meta'] = {}
        schedule['meta']['score'] = 0

        schedule['blocks'] = []
        schedule['unscheduledBlocks'] = []

        schedule['telescopes'] = {}
        for key, tel in self.telescopes.items():
            schedule['telescopes'][key] = {}
            schedule['telescopes'][key]["nights"] = {}
            for date in self.datesList:
                night = {}
                night['slots'] = []
                for i in range(0, self.numSlots):
                    night['slots'].append(None)
                schedule['telescopes'][key]['nights'][date] = night

        return schedule 


    def initBlock(self):
        block = {
            'id': 0,             # database id
            'size': None,        # fractional size of night (ie 0.25, 0.5, 0.75, 1.0)
            'moonIndex': None,   # index to moon phase date range as defined in config "moonPhaseFile"
            'reqDate': None,     # requested date to schedule
            'reqPortion': None,  # requested portion of night to schedule ("first half", "second quarter")

            'tel': None,         # telescope key (ie "1", "2")
            'ktn': None,         # KTN, aka semid (ie "2019A_N123")
            'type': None,        # "Classical", "Cadence", ???
            'instr': None,       # instrument name

            'progInstr': None,   # pointer to program instrument object

            'schedDate': None,   # actual scheduled date by this program
            'schedIndex': None,  # actual scheduled index position to fraction of the night (ie 0, 1, 2, 3) 

            'num': None,         # special var used for defining runs of blocks.  not used yet

            'order': None,       # calculated block order score for sorting blocks
            'orderMult': None,   # admin multiplier for calculated block order score

            'slots': None,       # temp array of slot data and slot scoring for picking slot in schedule
        }
        return block


    def assignBlockToSchedule(self, schedule, tel, date, index, block):

        #get slot and make sure it is empty
        telsched = schedule['telescopes'][tel]
        night = telsched['nights'][date]
        if night['slots'][index] != None:
            print (f"ERROR: Cannot assign block {block['id']} to slot {index} on date {date}.  Already assigned to block {night['slots'][index]['id']}")
            return False

        #add block to schedule object
        #print (f"Assigning block {block['id']} to slot {index} on date {date}.")
        night['slots'][index] = block

        #mark block with scheduled info
        block['schedDate']  = date
        block['schedIndex'] = index



    def removeScheduleBlock(self, schedule, blockId):

        #find block
        block, slots, slotIdx = self.findScheduleBlockById(schedule, blockId)
        if not block:
            print (f"ERROR: block id {blockId} not found!")
            return False

        #clear
        block['schedDate']  = None
        block['schedIndex'] = None
        if slotIdx != None: slots[slotIdx] = None
        print(f"Removed block {blockId} from scheduled blocks.")

        #re-analyze schedule
        self.markScheduleWarnings(schedule)
        self.scoreSchedule(schedule)


    def moveScheduleBlock(self, schedule, blockId, date, index):

        #find block
        block, slots, slotIdx = self.findScheduleBlockById(schedule, blockId)
        if not block:
            print (f"ERROR: block id {blockId} not found!")
            return False

        #valid move?
        if not self.isSlotValid(schedule, block, date, index, verbose=True):
            return False
        if not self.isSlotAvailable(schedule, block['tel'], date, index, block['size'], verbose=True):
            return False

        #assign
        self.assignBlockToSchedule(schedule, block['tel'], date, index, block)
        print(f"Moved block {blockId} to {date} slot {index}")

        #re-analyze schedule
        self.markScheduleWarnings(schedule)
        self.scoreSchedule(schedule)


    def swapScheduleBlocks(self, schedule, blockId1, blockId2):

#todo: test recent changes
        #make sure both exist
        block1, slots1, slotIdx1 = self.findScheduleBlockById(schedule, blockId1)
        block2, slots2, slotIdx2 = self.findScheduleBlockById(schedule, blockId2)
        if not block1 or not block2:
            if not block1: print (f"ERROR: block id {blockId1} not found!")
            if not block2: print (f"ERROR: block id {blockId2} not found!")
            return False

        #check for valid swap
        if slotIdx2 != None:
            if not self.isSlotValid(schedule, block1, date2, slotIdx2, verbose=True):
                return False
            if not self.isSlotAvailable(schedule, block2['tel'], date2, slotIdx2, block1['size'], verbose=True):
                return False
        if slotIdx1 != None:
            if not self.isSlotValid(schedule, block2, date1, slotIdx1, verbose=True):
                return False
            if not self.isSlotAvailable(schedule, block1['tel'], date1, slotIdx1, block2['size'], verbose=True):
                return False

        #remove them
        self.removeScheduleBlock(schedule, blockId1)
        self.removeScheduleBlock(schedule, blockId2)

        #now move
        if slotIdx2 != None: self.assignBlockToSchedule(schedule, block2['tel'], date2, slotIdx2, block1)
        if slotIdx1 != None: self.assignBlockToSchedule(schedule, block1['tel'], date1, slotIdx1, block2)
        print(f"Swapped block {blockId1} to {date2} slot {slotIdx2}")
        print(f"Swapped block {blockId2} to {date1} slot {slotIdx1}")

        #re-analyze schedule
        self.markScheduleWarnings(schedule)
        self.scoreSchedule(schedule)


    def isSlotValid(self, schedule, block, date, slotIndex, verbose=False):

        #check for block length versus size available length
        sizeRemain = 1 - (slotIndex * self.config['slotPerc'])
        if (block['size'] > sizeRemain): 
            if verbose: print(f"ERROR: block size {block['size']} too big for slot index {slotIndex}")
            return False

        #check for program dates to avoid
        if block['ktn'] in self.programs:
            prog = self.programs[block['ktn']]
            if date in prog['datesToAvoid']:
                if verbose: print(f"ERROR: date {date} is marked as program date to avoid.")
                return False

        #check for instrument unavailability
        if self.isInstrShutdown(block['instr'], date):
            if verbose: print(f"ERROR: date {date} is marked as instrument {block['instr']} shutdown.")
            return False

        #check for instr incompatibility
        if not self.checkInstrCompat(block['instr'], schedule, block['tel'], date):
            if verbose: print(f"ERROR: incompatable instrument {block['instr']} on date {date}")
            return False

        #check for adjacent reconfig incompatibilities
        if not self.checkReconfigCompat(block['instr'], schedule, block['tel'], date):
            if verbose: print(f"ERROR: incompatable reconfig for instrument {block['instr']} on date {date}")
            return False

        return True


    def findScheduleBlockById(self, schedule, blockId):
        #find as scheduled block
        for tel, telsched in schedule['telescopes'].items():
            for date, night in telsched['nights'].items():
                for slotIdx, block in enumerate(night['slots']):
                    if block and block['id'] == blockId:
                        return block, night['slots'], slotIdx
        #find as unscheduled block
        for b in schedule['unscheduledBlocks']:
            if b['id'] == blockId:
                return b, None, None
        #unfound
        return False, False, False


    def getScheduleDateInstrs(self, schedule, tel, date):
        allInstrs = []
        telsched = schedule['telescopes'][tel]
        if date not in telsched['nights']:
            return []
        night = telsched['nights'][date]
        for block in night['slots']:
            if block == None: continue
            instr = block['instr']
            instrs = instr.split('+')
            allInstrs += instrs
        return allInstrs


    def getScheduleDateBlocks(self, schedule, tel, date):
        telsched = schedule['telescopes'][tel]
        if date not in telsched['nights']:
            return []
        night = telsched['nights'][date]
        blocks = []
        for block in night['slots']:
            if block == None: continue
            blocks.append(block)
        return blocks


    def createInstrBaseNames(self):
        '''
        Get first set of all capital letters and numbers from beginning of string and store in instruments dict
        ie: LRISp-ADC = LRIS, HIRESr = HIRES
        '''        
        pattern = '^[A-Z0-9]*'
        for key, instr in self.instruments.items():
            instr['base'] = key
            match = re.search(pattern, key)
            if match and match[0]: 
                instr['base'] = match[0]


    def checkInstrCompat(self, instrStr, schedule, tel, date):
        #todo: This whole thing is inefficient
        instrs = instrStr.split('+')
        schedInstrs = self.getScheduleDateInstrs(schedule, tel, date)
        for instr in instrs:
            if instr not in self.config['instrSplitIncompat']: continue
            for schedInstr in schedInstrs:
                schedInstrBase = self.instruments[schedInstr]['base'] if schedInstr in self.instruments else None
                if schedInstr     in self.config['instrSplitIncompat'][instr]: return False
                if schedInstrBase in self.config['instrSplitIncompat'][instr]: return False
        return True


    def isScheduledInstrMatch(self, instrStr, schedule, tel, date):
        #todo: This whole thing is inefficient
        instrs = instrStr.split('+')
        for instr in instrs:
            schedInstrs = self.getScheduleDateInstrs(schedule, tel, date)
            for schedInstr in schedInstrs:
                if instr == schedInstr:
                    # print ("\tINSTR MATCH: ", instr, schedInstrs)
                    return True
        return False


    def getNumAdjacentInstrDates(self, instrStr, schedule, tel, date):
        #todo: This whole thing is inefficient
        #todo: Should we count more than just +/- one day?
        numExact = 0
        numBase  = 0
        instrs = instrStr.split('+')
        for instr in instrs:
            instrBase = self.instruments[instr]['base'] if instr in self.instruments else None
            for delta in range(-1, 2, 2):
                yesBase  = 0
                yesExact = 0
                adjDate = self.getDeltaDate(date, delta)
                schedInstrs = self.getScheduleDateInstrs(schedule, tel, adjDate)
                for schedInstr in schedInstrs:
                    schedInstrBase = self.instruments[schedInstr]['base'] if schedInstr in self.instruments else None
                    if instrBase == schedInstrBase: yesBase = 1
                    if instr     == schedInstr    : yesExact = 1
                if yesBase:  numBase += 1
                if yesExact: numExact += 1
        return numExact, numBase  


    def getNumAdjacentPrograms(self, ktn, schedule, tel, date):
        '''
        Look for same program on adjacent days.  Return 0, 1, or 2.
        '''
        num  = 0
        for delta in range(-1, 2, 2):
            yes = 0
            adjDate = self.getDeltaDate(date, delta)
            blocks = self.getScheduleDateBlocks(schedule, tel, adjDate)
            for block in blocks:
                if block['ktn'] == ktn: 
                    num += 1
                    break
        return num


    def getNumSameProgramsOnDate(self, ktn, schedule, tel, date):
        '''
        Look for same program, same date
        '''
        num = 0
        blocks = self.getScheduleDateBlocks(schedule, tel, date)
        for block in blocks:
            if block['ktn'] == ktn: num += 1
        return num


    def checkReconfigCompat(self, instrStr, schedule, tel, date):
        '''
        Look for instrument reconfigs that are incompatible.  
        In other words, instruments that cannot follow another instrument the next night.  
        Typically, the assumption is at least one extra day is needed for some reconfigs.
        '''
        #todo: This whole thing is inefficient
        nextDate = self.getDeltaDate(date, 1)
        prevDate = self.getDeltaDate(date, -1)

        instrs = instrStr.split('+')
        for instr in instrs:
            instrBase = self.instruments[instr]['base'] if instr in self.instruments else None

            #look at next day for scheduled instruments that can't follow instr
            schedInstrs = self.getScheduleDateInstrs(schedule, tel, nextDate)
            for schedInstr in schedInstrs:
                schedInstrBase = self.instruments[schedInstr]['base'] if schedInstr in self.instruments else None
                if instr not in self.config['instrReconfigIncompat']: continue
                if schedInstr     in self.config['instrReconfigIncompat'][instr]: return False
                if schedInstrBase in self.config['instrReconfigIncompat'][instr]: return False

            #look at previous day for scheduled instruments that can't have instr follow them
            schedInstrs = self.getScheduleDateInstrs(schedule, tel, prevDate)
            for schedInstr in schedInstrs:
                schedInstrBase = self.instruments[schedInstr]['base'] if schedInstr in self.instruments else None
                if schedInstr not in self.config['instrReconfigIncompat']: continue
                if instr     in self.config['instrReconfigIncompat'][schedInstr]: return False
                if instrBase in self.config['instrReconfigIncompat'][schedInstr]: return False

        return True


    def getDeltaDate(self, dateStr, delta):
        date = dt.strptime(dateStr, "%Y-%m-%d")
        newdate = date + timedelta(days=delta)
        return dt.strftime(newdate, "%Y-%m-%d")        


    def getNumBlocksScheduledOnDate(self, schedule, tel, date):
        count = 0
        telsched = schedule['telescopes'][tel]
        night = telsched['nights'][date]
        for block in night['slots']:
            if block == None: continue                        
            count += 1
        return count
        

    def isSlotAvailable(self, schedule, tel, date, index, size, verbose=False):

        #see if slot requested overlaps any slot assignments
        telsched = schedule['telescopes'][tel]
        night = telsched['nights'][date]
        for block in night['slots']:
            if block == None: continue                        
            vStart = block['schedIndex']
            vEnd = vStart + int(block['size'] / self.config['slotPerc']) - 1
            sStart = index 
            sEnd = sStart + int(size / self.config['slotPerc']) - 1
            if vEnd >= sStart and sEnd >= vStart:
                if verbose: print(f"ERROR: overlapping assignment for size {size} on {date} at slot index {index}")
                return False
        return True


    def isReqPortionMatch(self, reqPortion, slotIndex):
        if   reqPortion == 'first half'     and slotIndex <= 1: return True
        elif reqPortion == 'second half'    and slotIndex >= 2: return True
        elif reqPortion == 'first quarter'  and slotIndex == 0: return True
        elif reqPortion == 'second quarter' and slotIndex == 1: return True
        elif reqPortion == 'third quarter'  and slotIndex == 2: return True
        elif reqPortion == 'fourth quarter' and slotIndex == 3: return True
        else: return False


    def createDatesList(self, startDate, endDate):

        startDate = startDate.replace('-','')
        endDate   = endDate.replace('-','')
        dates = [d.strftime('%Y-%m-%d') for d in pd.date_range(startDate, endDate)]
        return dates


    #######################################################################
    # MOON PHASE FUNCTIONS
    #######################################################################

    def getMoonPhases(self):
        if self.config['moonPhasesFile']: 
            fp = self.config['moonPhasesFile']
            assert os.path.isfile(fp), f"ERROR: getMoonPhases: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = yaml.safe_load(f)        
            return data
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getMoonPhases: DB retrieve not implemented!"


    def createMoonPrefLookups(self):
        '''
        For each progInstr, create a moon pref hash for each date so we don't have to search for date ranges
        during processing.
        '''
        #todo: note: any value not defined is set to neutral (ie blank, "-"). handle this better
        for ktn, program in self.programs.items():
            for progInstr in program['instruments']:
                progInstr['moonPrefLookup'] = {}
                if not progInstr['moonPrefs']: continue
                for index, mp in enumerate(self.moonPhases):
                    dates = self.createDatesList(mp['start'], mp['end'])
                    for date in dates:
                        val = progInstr['moonPrefs'][index]
                        if val not in self.config['moonDatePrefScore']:
                            val = "N"
                        progInstr['moonPrefLookup'][date] = val


    def createMoonIndexDates(self):
        '''
        For each moon phase date range, create a hash of dates in that range for faster lookup
        '''
        self.moonDatesIndex = {}
        for index, mp in enumerate(self.moonPhases):
            dates = self.createDatesList(mp['start'], mp['end'])
            for date in dates:
                self.moonDatesIndex[date] = index


    def createMoonDatesIndex(self):
        '''
        For each moon phase date, create a hash of their moon index for faster lookup
        '''
        self.moonIndexDates = {}
        for index, mp in enumerate(self.moonPhases):
            self.moonIndexDates[index] = {}
            dates = self.createDatesList(mp['start'], mp['end'])
            for date in dates:
                self.moonIndexDates[index][date] = 1


    def getMoonPrefStrictness(self, moonPrefs):
        '''
        How strict is the moonPrefs in terms of number of days we have to work with?
        Returns fraction from 0.0. to 1.0.
        '''
        if not moonPrefs: return 0
        max = 0
        total = 0
        for i, pref in enumerate(moonPrefs):
            numDays = len(self.moonIndexDates[i])
            if   pref == 'P': total += numDays
            elif pref == 'A': total += numDays * 2
            max += numDays * 2
        if total == 0: return 0 #no prefs
        strict = 1 - (total / max)
        strict = math.pow(strict, 2.5) #apply exponential decay
        return strict


    def getNightPhases(self):
        #TODO: NOTE: This data file comes from Keck scheduler (aka Carolyn) which is reformatted from 
        #UCO page: http://ucolick.org/calendar/keckcal2011-20/index.html
        if self.config['nightPhasesFile']: 
            fp = self.config['nightPhasesFile']
            assert os.path.isfile(fp), f"ERROR: getNightPhases: file '{fp}'' does not exist.  Exiting."
            data = pd.read_csv(fp)        
            return data
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getMoonPhases: DB retrieve not implemented!"



    #######################################################################
    # UTILITY FUNCTIONS
    #######################################################################

    def checkConflicts(self):

        #look for blocks with schedDate or moonPref on 'X' moon pref
        print("\n=== Requested Moon Index vs Moon Prefs conflicts ===")
        for ktn, program in self.programs.items():
            for progInstr in program['instruments']:
                for block in progInstr['blocks']:

                    if progInstr['moonPrefs']:

                        if block['reqDate']:
                            pref = progInstr['moonPrefLookup'][block['reqDate']]
                            if pref == 'X':
                                print (f"reqDate {block['reqDate']} is pref 'X': ", ktn, progInstr['instr'], block['id'] )


                        mi = block['moonIndex']
                        pref = progInstr['moonPrefs'][mi]
                        if pref == 'X':
                            print (f"moonIndex '{mi}' is pref 'X': ", ktn, progInstr['instr'], block['id'] )

        #see if any moon periods are over-requested
        for tel, t in self.telescopes.items():
            print(f'\n=== Moon Phase Request %: Telescope {tel} ===')

            for mp in self.moonPhases: 
                mp['reqNights'+tel] = 0
                dates = self.createDatesList(mp['start'], mp['end'])
                mp['totalNights'+tel] = len(dates)

            for ktn, program in self.programs.items():
                for progInstr in program['instruments']:
                    if tel != self.instruments[progInstr['instr']]['tel']: continue
                    for block in progInstr['blocks']:
                        mi = block['moonIndex']
                        self.moonPhases[mi]['reqNights'+tel] += block['size']

            for mi, mp in enumerate(self.moonPhases): 
                mp['reqPerc'+tel] = mp['reqNights'+tel] / mp['totalNights'+tel]
                print (f"{mp['start'].ljust(10)}\t{mp['end'].ljust(10)}\t{mp['type'].ljust(4)}", end='')
                print (f"\t{mp['reqNights'+tel]}", end='')
                print (f"\t{mp['totalNights'+tel]}", end='')
                print (f"\t{round(100*mp['reqPerc'+tel])}%")



    def getListItemByWeightedRandom(theList, key):
        '''
        Returns a random item from list based on weighted random factor of given key values.
        (Assumes a list of dict items)
        '''

        #print ('getListItemByWeightedRandom', theList)

        #get total sum of values we are weighting so we can calc proper rand percs
#todo: Add in ability to weight higher in list even more 
        sum = 0
        for item in theList:
            sum += item[key]

        #pick random number between 0 and sum
        rand = random() * sum

        # return item as soon as we find where random number landed
        runSum = 0
        for i, item in enumerate(theList):
            runSum += item[key]
            if rand <= runSum:
                #print ('weighted random chosen: ', i, ' of ' , len(theList))
                return item

        #should not get here
        return None


    def getDistinctNightInstrs(self, slots):
        instrs = []
        for block in slots:
            if block == None: continue
            if block['instr'] in instrs: continue
            instrs.append(block['instr'])
        return instrs


    def exportSchedule(self, schedule, outFilepath=None, tel=None):
        '''
        Writes out schedule to specific format required by Keck scheduler (cjordan)
        #TODO: Finish this later once we figure out how the new process will work
        '''

        #loop telescopes
        for telkey, telsched in schedule['telescopes'].items():
            if tel and telkey != tel: continue

            #create output file
            timestamp = dt.now().strftime('%Y-%m-%d-%H-%M-%S')
            outFilepath = f'./sched_worksheet_{telkey}_{timestamp}.csv'
            print(f"Writing to {outFilepath}")
            file = open(outFilepath, 'w')

            #loop moon phase dates
            for index, mp in enumerate(self.moonPhases):
                dates = self.createDatesList(mp['start'], mp['end'])

                #section header
                file.write("Date\tDay\tDark%\tMoon@Mid\tLST@mid")
                file.write("\tPI Last\tPI First\tInstrument\tInstitution\tKTN\t#ngt\tPeriod\tDates to Avoid\tCard Date\tCard Portion")
                file.write("\tScheduler Notes\tTarget\tPAX\tSpecial Requests\n")

                #date moon info and blocks
                for date in dates:

                    #moon info
                    file.write(date)
                    file.write("\t" + dt.strptime(date, '%Y-%m-%d').strftime('%a').upper())
                    file.write("\t" + mp['type'])
                    file.write("\t" + '?')
                    file.write("\t" + '?')
                    file.write("\t" + "?")
                    file.write("\n")

                    night = telsched['nights'][date]
                    for i, block in enumerate(night['slots']):
                        if block == None: continue
                        print (f"...writing block {block['id']}")
                        file.write("\t\t\t\t\t")
                        file.write(f"\t{block['schedIndex']}")
                        file.write(f"\t{block['size']}")
                        file.write(f"\t{block['ktn']}")
                        file.write(f"\t{block['instr']}")
                        file.write(f"\t{block['type']}")
                        file.write("\n")

            file.close() 
               


    def printSchedule(self, schedule, tel=None, start=None, end=None, format='txt'):
        '''
        Print out a schedule in text or html.
        
        Sample output:
          Semester: 2019B
          Method  : Random
          Schedule: 
            2019-08-01  K1  [             N123             ]
            2019-08-01  K2  [         N111         ][ C222 ]
            2019-08-02  K2  [     N111     ][     C222     ]
            2019-08-02  K2  [ N123 ][ C123 ][ U123 ][ K123 ]
        '''        
        print (f"Semester: {self.semester}")

        totalUnused = 0.0
        for telkey, telsched in schedule['telescopes'].items():
            if tel and telkey != tel: continue

            schedName = self.telescopes[telkey]['name']
            print (f'\n\n============================')
            print (f' Schedule for {schedName}:')
            print (f'============================')
            print (f'{"Date".ljust(11)}\tIdx\tSize\t{"KTN".ljust(9)}\t{"Instr".ljust(11)}\t{"Type".ljust(11)}\t', end='')
            print (f'{"Id".ljust(5)}\tScDt?\tRqDt?\tRqPt?\tMnIdx?\tMnPrf?\tDup?\tScore')
            prevMoonIndex = None
            for date in self.datesList:
                if start and date < start: continue
                if end   and date > end  : continue

                moonIndex = self.moonDatesIndex[date]
                if moonIndex != prevMoonIndex:
                    print(f"\n---------- Moon Index {moonIndex} ----------", end='')
                prevMoonIndex = moonIndex

                night = telsched['nights'][date]
                print(f"\n[{date}]\t", end='')

                percTotal = 0
                num = 0
                for i, block in enumerate(night['slots']):
                    if block == None: continue
                    bid = block['id'] if 'id' in block else ''
                    if num>0: print ("\n            \t", end='')
                    print(f"{block['schedIndex']}", end='')
                    print(f"\t{block['size']}", end='')
                    print(f"\t{block['ktn']}", end='')
                    print(f"\t{block['instr'].ljust(12)}", end='')
                    print(f"\t{block['type'][:11].ljust(10)}", end='')
                    print(f"\t[{bid}]", end='')
                    print(f"\t{block['warnSchedDate']}", end='')
                    print(f"\t{block['warnReqDate']}", end='')
                    print(f"\t{block['warnReqPortion']}", end='')
                    print(f"\t{block['warnMoonIndex']}", end='')
                    print(f"\t{block['warnMoonPref']}", end='')
                    print(f"\t{block['warnSameProgram']}", end='')
                    print(f"\t{block['score']}", end='')
                    percTotal += block['size']
                    num += 1
                if percTotal < 1.0:
                    unused = 1 - percTotal
                    totalUnused += unused
                    print (f"\n          \t!!! unused = {unused} !!!", end='')
            print ("\n")
            print (f"total unused = {totalUnused}")

        if schedule['unscheduledBlocks']:
            print ("\n********************************************")
            print ("*** WARNING: Unscheduled program blocks! ***")
            print ("********************************************")
            for block in schedule['unscheduledBlocks']:
                print (f"\t{''.ljust(16)}{block['size']}\t{block['ktn']}\t{block['instr'].ljust(12)}\t{block['type'][:11].ljust(10)}\t[{block['id']}]\t")


    def printStats(self, schedule):
        '''
        Print out stats on schedule
        '''        
        print (f"Semester: {self.semester}")
        print (f"Schedule score: {schedule['meta']['score']}")
        for telkey, telsched in schedule['telescopes'].items():

            telName = self.telescopes[telkey]['name']
            totalUnused = 0.0
            for date in self.datesList:

                night = telsched['nights'][date]
                percTotal = 0
                for i, block in enumerate(night['slots']):
                    if block == None: continue
                    percTotal += block['size']
                unused = 1 - percTotal
                totalUnused += unused

            #summary stats
            print (f'Telescope {telName}: Total unused time = {totalUnused} nights')


    def getSemesterDates(self, semester):
        #return '2020-02-01', '2020-02-03'
        year = int(semester[0:4])
        semStart = f'{year}-02-01' if ('A' in semester) else f'{year}-08-01'
        semEnd   = f'{year}-07-31' if ('A' in semester) else f'{year+1}-01-31'
        return semStart, semEnd
    

    def convertDictArrayToDict(self, data, pKey):
        data2 = {}
        for d in data:
            key = d[pKey]
            assert key not in data2, f"ERROR: {pKey} is not unique.  Aborting."
            data2[key] = d
        return data2

  
    def convertDictArrayToArrayDict(self, data, key1, key2):
        data2 = {}
        for d in data:
            if d[key1] not in data2: 
                data2[d[key1]] = []
            data2[d[key1]].append(d[key2])
        return data2


    def convertDateRangeToDictArray(self, data, startKey, endKey):
        data2 = []
        for d in data:
            startDate = d[startKey]
            endDate   = d[endKey]
            dates = self.createDatesList(startDate, endDate)
            for date in dates:
                obj = d.copy()
                obj['date'] = date
                del obj[startKey]
                del obj[endKey]
                data2.append(obj)
        return data2
