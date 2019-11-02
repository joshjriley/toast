import os
import yaml
import json
import argparse
import pandas
from random import randrange, shuffle, random
from ToastRandom import *
from datetime import datetime as dt


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
        self.moonPhases      = self.getMoonPhases()
        self.programs       = self.getPrograms(self.semester)
        self.telShutdowns   = self.getTelescopeShutdowns(self.semester)
        self.instrShutdowns = self.getInstrumentShutdowns(self.semester)

        #create new blank schedule
        self.initSchedule()
        
        #todo: check if they total proposed hours exceeds semester hours

        #do it
        self.schedule = self.createSchedule()


    def loadConfig(self):

        #load config
        configFile = 'config.yaml'
        assert os.path.isfile(configFile), f"ERROR: config file '{configFile}'' does not exist.  Exiting."
        with open(configFile) as f: self.config = yaml.safe_load(f)        

        #do some basic calcs from config
        self.numPortions = int(1 / self.config['portionPerc'])

    
    #abstract methods that must be implemented by inheriting classes
    def createSchedule(self) : raise NotImplementedError("Abstract method not implemented!")


    def getSemesterDates(self, semester):
        #todo: calc from semester
        # return '2019-08-01', '2019-08-01'
        return '2019-08-01', '2019-08-12'
        return '2019-08-01', '2020-01-31'


    def getPrograms(self, semester):

        #todo: generate random data for testing?

        #todo: temp: get test data for now
        with open('../test/test-data-programs.json') as f:
            data = json.load(f)
        return data
        
        #todo: query proposals database for all approved programs for semester
        #todo: query for all the other auxilliary info needed
        # query = f"select * from ClassicalInformation_TAC where semester='{semester}' and DelFlag=0"
        # data = dbConn.query(query)
        # return data
  

    def getTelescopeShutdowns(self, semester):

        #todo: temp: test data one random shutdown date per telescope
        shutdowns = {}
        for telNum in self.config['telescopes']:
            shutdowns[telNum] = []
            index = randrange(0, len(self.datesList))
            randDate = self.datesList[index]
            shutdowns[telNum].append(randDate)
        return shutdowns

        #query for known telescope shutdowns
#        shutdowns = {}
#        for telNum in self.config['telescopes']:
#            shutdowns[telNum] = []
#            #todo: query
#        return shutdowns


    def getInstrumentShutdowns(self, semester):

        #todo: temp: test data one random shutdown date per telescope
        shutdowns = {}
        for instr in self.config['instruments']:
            shutdowns[instr] = []
            index = randrange(0, len(self.datesList))
            randDate = self.datesList[index]
            shutdowns[instr].append(randDate)
        return shutdowns

        #query for known telescope shutdowns
#        shutdowns = {}
#        for instr in self.config['instruments']:
#            shutdowns[instr] = []
#            #todo: query
#        return shutdowns


    def initSchedule(self):

        #create blank schedule for each telescope
        self.schedules = {}
        for key, tel in self.config['telescopes'].items():
            self.schedules[key] = {}
            self.schedules[key]["nights"] = {}
            for date in self.datesList:
                night = {}
                night['slots'] = []
                self.schedules[key]['nights'][date] = night
      

    def assignToSchedule(self, telNum, date, index, portion, progId, instr):
        schedule = self.schedules[telNum]
        night = schedule['nights'][date]
        data = {
            'index': index,
            'portion': portion,
            'progId': progId,
            'instr': instr
        }
        night['slots'].append(data)


    def isSlotAvailable(self, telNum, date, index, portion):

        #see if slot requested overlaps any slot assignments
        night = self.schedules[telNum]['nights'][date]
        for slot in night['slots']:
            vStart = slot['index']
            vEnd = vStart + int(slot['portion'] / self.config['portionPerc']) - 1
            sStart = index 
            sEnd = sStart + int(portion / self.config['portionPerc']) - 1

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
            return self.getMoonPhasesFromFile(self.config['moonPhasesFile'])
        else:
            return self.getMoonPhasesFromDB(self.startDate, self.endDate)

    def getMoonPhasesFromDB(self, startDate, endDate):
        #todo: optional query for moon dates.  Note: No such table yet.
        assert False, "getMoonPhasesFromDB not implemented!"

    def getMoonPhasesFromFile(self, filepath):
        assert os.path.isfile(filepath), f"ERROR: getMoonPhasesFromFile: file '{filepath}'' does not exist.  Exiting."
        with open(filepath) as f: dates = yaml.safe_load(f)        
        return dates

    def getMoonDatePreference(self, date, progId, instr):
        '''
        Find moon phase by date and use same index to look up moon phase preference for program+instr
        '''
        pref = None
        date = dt.strptime(date, "%Y-%m-%d")
        for index, mp in enumerate(self.moonPhases):
            phaseStart = dt.strptime(mp['start'], "%Y-%m-%d")
            phaseEnd   = dt.strptime(mp['end'],   "%Y-%m-%d")
            if phaseStart <= date <= phaseEnd:
                moonPrefs = self.programs[progId]['instruments'][instr]['moonPrefs']
                pref = moonPrefs[index]
                break
        return pref

      
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
                pref = self.getAssignmentPref(slot.date, slot.progId)
                score += gslotPrefFactor[pref]

            #todo: alter score based on priority RA/DEC list?

            #todo: can a program get a portion of night greater or less than requested?

            #todo: score based on minimal runs for instruments that want runs

            return score


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


    def printSchedule(self, telNum=None, format='txt'):
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
            schedName = self.config['telescopes'][schedKey]['name']
            print (f'\nSchedule for {schedName}:')
            print (f'--------------------------')

            for date in self.datesList:
                night = schedule['nights'][date]
                print(f"==={date}===")

                if date in self.telShutdowns[schedKey]:
                    print(" *** SHUTDOWN ***")

                slots = night['slots']
                slotsSorted = sorted(slots, key=lambda k: k['index'], reverse=False)
                for slot in slotsSorted:
                    print(f"{slot['index']}\t{slot['portion']}\t{slot['progId']}\t{slot['instr']}")
    
    

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
    
    
