import os
import sys
import yaml
import json
import argparse
import pandas
from random import randrange, shuffle, random
from datetime import datetime as dt, timedelta
import pathlib
import time
import math
import re

from ToastRandom import *

import logging
log = logging.getLogger('toast')



class Toast(object):

    def __init__(self, semester):
    
        #input class vars
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
        self.instrShutdowns = self.getInstrumentShutdowns()
        self.engineering    = self.getEngineering()
        self.programs       = self.getPrograms(self.semester)

        #perform data conversion optimizations
        self.createMoonIndexDates()
        self.createMoonPrefLookups()
        self.createInstrBaseNames()

        #todo: check if the total proposed hours exceeds semester hours

        #do it
        self.schedule = self.createSchedule()
        self.promptMenu()
        #self.printSchedule(self.schedule)


    def promptMenu(self):

        menu = "\n"
        menu += "------------------------------------------------------------\n"
        menu += "|                    MENU                                   |\n"
        menu += "------------------------------------------------------------|\n"
        menu += "|  show [tel] [start day] [stop day]   Show schedule        |\n"
        menu += "|  stats                               Show stats           |\n"
        menu += "|  q                                   Quit (or Control-C)  |\n"
        menu += "-------------------------------------------------------------\n"
        menu += "> "

        quit = None
        while quit is None:
            cmds = input(menu).split()       
            if not cmds: continue
            cmd = cmds[0]     
            if   cmd == 'q'     :  quit = True
            elif cmd == 'show'  :  self.showSchedule(cmds=cmds)
            elif cmd == 'stats' :  self.printStats(self.schedule)
            else:
                log.error(f'Unrecognized command: {cmd}')


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
        schedule['meta']['unscheduledBlocks'] = []
        schedule['meta']['score'] = 0

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
            'orderScore': None,  # admin override for calculated block order score

            'slots': None,       # temp array of slot data and slot scoring for picking slot in schedule

            'warnSchedDate': 0,  # set to 1 if block did not get scheduled
            'warnReqDate': 0,    # set to 1 if scheduled date does not equal requested date
            'warnReqPortion': 0, # set to 1 if scheduled portion does not equal requested portion
        }
        return block


    def assignBlockToSchedule(self, schedule, tel, date, index, block):
        #mark block with scheduled info
        block['schedDate']  = date
        block['schedIndex'] = index

        #add block to schedule object
        telsched = schedule['telescopes'][tel]
        night = telsched['nights'][date]
        night['slots'][index] = block


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
        

    def isSlotAvailable(self, schedule, tel, date, index, size):

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
        dates = [d.strftime('%Y-%m-%d') for d in pandas.date_range(startDate, endDate)]
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
                    start = dt.strptime(mp['start'], "%Y-%m-%d")
                    end   = dt.strptime(mp['end'],   "%Y-%m-%d")
                    delta = end - start
                    for i in range(delta.days + 1):
                        day = start + timedelta(days=i)
                        daystr = day.strftime('%Y-%m-%d')
                        val = progInstr['moonPrefs'][index]
                        if val not in self.config['moonDatePrefScore']:
                            val = "N"
                        progInstr['moonPrefLookup'][daystr] = val


    def createMoonIndexDates(self):
        '''
        For each moon phase date range, create a hash of dates in that range for easier lookup
        '''
        self.moonIndexDates = {}
        for index, mp in enumerate(self.moonPhases):
            self.moonIndexDates[index] = {}
            start = dt.strptime(mp['start'], "%Y-%m-%d")
            end   = dt.strptime(mp['end'],   "%Y-%m-%d")
            delta = end - start
            for i in range(delta.days + 1):
                day = start + timedelta(days=i)
                daystr = day.strftime('%Y-%m-%d')
                self.moonIndexDates[index][daystr] = 1


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


    #######################################################################
    # UTILITY FUNCTIONS
    #######################################################################

    def getListItemByWeightedRandom(theList, key):
        '''
        Returns a random item from list based on weighted random factor of given key values.
        (Assumes a list of dict items)
        '''

        #print ('getListItemByWeightedRandom', theList)

        #get total sum of values we are weighting so we can calc proper rand percs
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


    def showSchedule(self, cmds):
        tel   = cmds[1] if len(cmds) > 1 else None
        start = cmds[2] if len(cmds) > 2 else None
        end   = cmds[3] if len(cmds) > 3 else None
        self.printSchedule(self.schedule, tel=tel, start=start, end=end)


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
            print (f'\nSchedule for {schedName}:')
            print (f'--------------------------')

            for date in self.datesList:
                if start and date < start: continue
                if end   and date > end  : continue

                night = telsched['nights'][date]
                print(f"\n[{date}]\t", end='')

                percTotal = 0
                num = 0
                for i, block in enumerate(night['slots']):
                    if block == None: continue
                    if num>0: print ("\n            \t", end='')
                    print(f"{block['schedIndex']}\t{block['size']}\t{block['ktn']}", end='')
                    print(f"\t{block['instr'].ljust(12)}", end='')
                    print(f"\t{block['type'][:10].ljust(10)}", end='')
                    print(f"\t{block['warnSchedDate']}", end='')
                    print(f"\t{block['warnReqDate']}", end='')
                    print(f"\t{block['warnReqPortion']}", end='')
                    percTotal += block['size']
                    num += 1
                if percTotal < 1.0:
                    unused = 1 - percTotal
                    totalUnused += unused
                    print (f"\n          \t!!! unused = {unused} !!!", end='')
            print ("\n")
            print (f"total unused = {totalUnused}")

        if schedule['meta']['unscheduledBlocks']:
            print ("********************************************")
            print ("*** WARNING: Unscheduled program blocks! ***")
            print ("********************************************")
            for block in schedule['meta']['unscheduledBlocks']:
                print (f"\t!!! {block['ktn']}, instr {block['instr']}")


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
                if self.isTelShutdown(telkey, date):
                    continue

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



##-------------------------------------------------------------------------
## Create logger
##-------------------------------------------------------------------------
def create_logger():

    try:
        ## Create logger object
        log = logging.getLogger('toast')
        log.setLevel(logging.DEBUG)

        #create log file and log dir if not exist
        ymd = dt.utcnow().date().strftime('%Y%m%d')
        pathlib.Path('logs/').mkdir(parents=True, exist_ok=True)

        #file handler (full debug logging)
        logFile = f'logs/keck-remote-log-utc-{ymd}.txt'
        logFileHandler = logging.FileHandler(logFile)
        logFileHandler.setLevel(logging.DEBUG)
        logFormat = logging.Formatter('%(asctime)s UT - %(levelname)s: %(message)s')
        logFormat.converter = time.gmtime
        logFileHandler.setFormatter(logFormat)
        log.addHandler(logFileHandler)

        #stream/console handler (info+ only)
        logConsoleHandler = logging.StreamHandler()
        logConsoleHandler.setLevel(logging.INFO)
        logFormat = logging.Formatter(' %(levelname)8s: %(message)s')
        logFormat.converter = time.gmtime
        logConsoleHandler.setFormatter(logFormat)
        
        log.addHandler(logConsoleHandler)

    except Exception as error:
        print (str(error))
        print (f"ERROR: Unable to create logger at {logFile}")
        print ("Make sure you have write access to this directory.\n")
        log.info("EXITING APP\n")        
        sys.exit(1)


    

##-------------------------------------------------------------------------
##  main
##-------------------------------------------------------------------------
if __name__ == "__main__":
    '''
    Run in command line mode
    '''

    #create logger first
    create_logger()
    log.info(f"Starting TOAST program.")


    # arg parser
    parser = argparse.ArgumentParser(description="Start Keck auto-scheduler.")
    parser.add_argument("semester",   type=str,                                            help="Semester.")
    parser.add_argument("--method",   type=str,    dest="method",    default='random',     help="Algorithm method.")
    parser.add_argument("--runCount", type=int,    dest="runCount",  default=1,            help="Number of times to run.")
    args = parser.parse_args()

    #go
    if   args.method == 'random': toast = ToastRandom(args.semester, args.runCount)
    elif args.method == '???'   : toast = ToastXXX(args.semester)
    else:
        print (f"Unknown method {args.method}")
        sys.exit(0)

    #result
    toast.start()
    
    
