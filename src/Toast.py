import os
import sys
import yaml
import json
import argparse
import pandas
from random import randrange, shuffle, random
from ToastRandom import *
from datetime import datetime as dt, timedelta
import pathlib
import time

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
        self.telShutdowns   = self.getTelescopeShutdowns()
        self.instrShutdowns = self.getInstrumentShutdowns()
        self.programs       = self.getPrograms(self.semester)

        #perform data conversion optimizations
        self.createMoonIndexDates()
        self.createMoonPrefLookups()

        #create new blank schedule
        self.initSchedule()
        
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
        menu += "|  s [tel] [start day] [stop day]      Show schedule        |\n"
        menu += "|  q                                   Quit (or Control-C)  |\n"
        menu += "-------------------------------------------------------------\n"
        menu += "> "

        quit = None
        while quit is None:
            cmds = input(menu).split()       
            if not cmds: continue
            cmd = cmds[0]     
            if   cmd == 'q'          :  quit = True
            elif cmd in ['s', 'show']:  self.showSchedule(cmds=cmds)
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


    def getTelescopeShutdowns(self):

        data = None
        if self.config['telShutdownsFile']: 
            fp = self.config['telShutdownsFile']
            assert os.path.isfile(fp), f"ERROR: getTelescopeShutdowns: file '{fp}'' does not exist.  Exiting."
            with open(fp) as f: data = yaml.safe_load(f)        
        else:
            #todo: optional query.  Note: No such table yet.
            assert False, "ERROR: getTelescopeShutdowns: DB retrieve not implemented!"

        #convert to dict indexed by keys
        data = self.convertDictArrayToArrayDict(data, 'tel', 'date')
        return data

    def isTelShutdown(self, tel, date):
        if tel in self.telShutdowns: 
            shutdownDates = self.telShutdowns[tel]
            if date in shutdownDates:
                return True
        return False


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
        data = self.convertDictArrayToArrayDict(data, 'instr', 'date')
        return data

    def isInstrShutdown(self, instr, date):
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
        schedule['telescopes'] = {}
        for key, tel in self.telescopes.items():
            schedule['telescopes'][key] = {}
            schedule['telescopes'][key]["nights"] = {}
            for date in self.datesList:
                night = {}
                night['slots'] = []
                schedule['telescopes'][key]['nights'][date] = night
        return schedule 


    def assignToSchedule(self, schedule, tel, date, index, size, ktn, instr):
        telsched = schedule['telescopes'][tel]
        night = telsched['nights'][date]
        data = {
            'index': index,
            'size': size,
            'ktn': ktn,
            'instr': instr
        }
        night['slots'].append(data)


    def getScheduleDateInstrs(self, schedule, tel, date):
        allInstrs = []
        telsched = schedule['telescopes'][tel]
        if date not in telsched['nights']:
            return []
        night = telsched['nights'][date]
        for slot in night['slots']:
            instr = slot['instr']
            instrs = instr.split('+')
            allInstrs += instrs
        return allInstrs


    def getInstrBase(self, instr):
        instr = instr.split('-')[0]
        #todo: temp: this should be in config, not hardcoded
        if   'HIRES' in instr: instr = 'HIRES'
        elif 'LRIS' in instr: instr = 'LRIS'
        return instr


    def checkInstrCompat(self, instr, schedule, tel, date):
        #todo: This whole thing is inefficient
        instrBase = self.getInstrBase(instr)
        schedInstrs = self.getScheduleDateInstrs(schedule, tel, date)
        for schedInstr in schedInstrs:
            schedInstrBase = self.getInstrBase(schedInstr)
            if schedInstrBase in self.config['instrIncompatMatrix'][instrBase]:
                #print ("\tINSTR INCOMPAT: ", instr, schedInstrs)
                return False
        return True


    def isScheduledInstrMatch(self, instr, schedule, tel, date):
        #todo: This whole thing is inefficient
        instrBase = self.getInstrBase(instr)
        schedInstrs = self.getScheduleDateInstrs(schedule, tel, date)
        for schedInstr in schedInstrs:
            schedInstrBase = self.getInstrBase(schedInstr)
            if instrBase == schedInstrBase:
                #print ("\tINSTR MATCH: ", instr, schedInstrs)
                return True
        return False


    def getNumAdjacentIntr(self, instr, schedule, tel, date):
        #todo: This whole thing is inefficient
        #todo: Should we count more than just +/- one day?
        num = 0
        instrBase = self.getInstrBase(instr)
        for delta in range(-1, 2, 2):
            adjDate = self.getDeltaDate(date, delta)
            schedInstrs = self.getScheduleDateInstrs(schedule, tel, adjDate)
            for schedInstr in schedInstrs:
                schedInstrBase = self.getInstrBase(schedInstr)
                if instrBase == schedInstrBase:
                    num += 1
                    break
        return num  


    def getDeltaDate(self, dateStr, delta):
        date = dt.strptime(dateStr, "%Y-%m-%d")
        newdate = date + timedelta(days=delta)
        return dt.strftime(newdate, "%Y-%m-%d")        


    def isSlotAvailable(self, schedule, tel, date, index, size):

        #see if slot requested overlaps any slot assignments
        telsched = schedule['telescopes'][tel]
        night = telsched['nights'][date]
        for slot in night['slots']:
            vStart = slot['index']
            vEnd = vStart + int(slot['size'] / self.config['slotPerc']) - 1
            sStart = index 
            sEnd = sStart + int(size / self.config['slotPerc']) - 1
            if (sStart >= vStart and sStart <= vEnd) or (sEnd >= vStart and sEnd <=vEnd):
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


    #######################################################################
    # SCORING FUNCTIONS
    #######################################################################
      
    def scoreSchedule(self, schedule):

        #TODO: finish this psuedocode
        gInstrSwitchesFactor = -1.5
        gslotPrefFactor = {'P': 10,  'A': 5,  'N': 0,  'X': -20}

        score = 0
        for telkey, telsched in schedule['telescopes'].items():
            for night in telsched['nights']:
                pass
                # # deduct score based on number instrument switches
                # numInstrSwitches = night.getNumInstrSwitches()
                # score += numInstrSwitches * gInstrSwitchesFactor

                # # for each slot, alter score based on assignment preference [P,A,N,X]
                # for slot in night:
                #     pref = self.getAssignmentPref(slot.date, slot.ktn)
                #     score += gslotPrefFactor[pref]

                # #todo: alter score based on priority RA/DEC list?

                # #todo: can a block get a size greater or less than requested?

                # #todo: score based on minimal runs for instruments that want runs

        schedule['meta']['score'] = score


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
        print (f"Schedule score: {schedule['meta']['score']}")
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

                if self.isTelShutdown(telkey, date):
                    print("*** SHUTDOWN ***", end='')

                slots = night['slots']
                slotsSorted = sorted(slots, key=lambda k: k['index'], reverse=False)
                for i, slot in enumerate(slotsSorted):
                    if i>0: print ("\n            \t", end='')
                    print(f"{slot['index']}\t{slot['size']}\t{slot['ktn']}\t{slot['instr']}", end='')



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
    
    
