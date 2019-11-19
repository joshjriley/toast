import os
import sys
import yaml
import json
import argparse
import pandas
from random import randrange, shuffle, random
from ToastRandom import *
from datetime import datetime as dt, timedelta


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

        #create blank schedule for each telescope
        self.schedules = {}
        for key, tel in self.telescopes.items():
            self.schedules[key] = {}
            self.schedules[key]["nights"] = {}
            for date in self.datesList:
                night = {}
                night['slots'] = []
                self.schedules[key]['nights'][date] = night
      

    def assignToSchedule(self, tel, date, index, size, ktn, instr):
        schedule = self.schedules[tel]
        night = schedule['nights'][date]
        data = {
            'index': index,
            'size': size,
            'ktn': ktn,
            'instr': instr
        }
        night['slots'].append(data)


    def isSlotAvailable(self, tel, date, index, size):

        #see if slot requested overlaps any slot assignments
        night = self.schedules[tel]['nights'][date]
        for slot in night['slots']:
            vStart = slot['index']
            vEnd = vStart + int(slot['size'] / self.config['slotPerc']) - 1
            sStart = index 
            sEnd = sStart + int(size / self.config['slotPerc']) - 1

            if (sStart >= vStart and sStart <= vEnd) or (sEnd >= vStart and sEnd <=vEnd):
                return False

        return True


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
        for night in schedule:

            # deduct score based on number instrument switches
            numInstrSwitches = night.getNumInstrSwitches()
            score += numInstrSwitches * gInstrSwitchesFactor

            # for each slot, alter score based on assignment preference [P,A,N,X]
            for slot in night:
                pref = self.getAssignmentPref(slot.date, slot.ktn)
                score += gslotPrefFactor[pref]

            #todo: alter score based on priority RA/DEC list?

            #todo: can a block get a size greater or less than requested?

            #todo: score based on minimal runs for instruments that want runs

            return score


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


    def printSchedule(self, tel=None, format='txt'):
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
        print ('Semester: ', self.semester)
        for schedKey, schedule in self.schedules.items():            
            schedName = self.telescopes[schedKey]['name']
            print (f'\nSchedule for {schedName}:')
            print (f'--------------------------')

            for date in self.datesList:
                night = schedule['nights'][date]
                print(f"==={date}===")

                if self.isTelShutdown(schedKey, date):
                    print(" *** SHUTDOWN ***")

                slots = night['slots']
                slotsSorted = sorted(slots, key=lambda k: k['index'], reverse=False)
                for slot in slotsSorted:
                    print(f"{slot['index']}\t{slot['size']}\t{slot['ktn']}\t{slot['instr']}")


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
##  main
##-------------------------------------------------------------------------
if __name__ == "__main__":
    '''
    Run in command line mode
    '''

    # arg parser
    parser = argparse.ArgumentParser(description="Start Keck auto-scheduler.")
    parser.add_argument("semester",   type=str,                                            help="Semester.")
    parser.add_argument("--method",   type=str,    dest="method",    default='random',     help="Algorithm method.")
    args = parser.parse_args()

    #go
    if   args.method == 'random': toast = ToastRandom(args.semester)
    elif args.method == '???'   : toast = ToastXXX(args.semester)
    else:
        print (f"Unknown method {args.method}")
        sys.exit(0)

    #result
    toast.start()
    toast.printSchedule()
    
    
