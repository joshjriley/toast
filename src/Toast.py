import json
import argparse
import pandas
from random import randrange, shuffle, random
import config
from ToastRandom import *
from datetime import datetime as dt


class Toast(object):

    def __init__(self, semester):
    
        #input class vars
        self.semester = semester

        #member class vars
        self.schedule = None
  

    def start(self):

        #calc start and end date
        self.startDate, self.endDate = self.getSemesterDates(self.semester)

        #get needed input data
        self.datesList      = self.createDatesList(self.startDate, self.endDate)
        self.moonDates      = self.getMoonDates(self.startDate, self.endDate)
        self.programs       = self.getPrograms(self.semester)
        self.telShutdowns   = self.getTelescopeShutdowns(self.semester)
        self.instrShutdowns = self.getInstrumentShutdowns(self.semester)

        #create new blank schedule
        self.initSchedule()
        
        #todo: check if they total proposed hours exceeds semester hours

        #do it
        self.schedule = self.createSchedule()

    
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
        for telNum in config.kTelescopes:
            shutdowns[telNum] = []
            index = randrange(0, len(self.datesList))
            randDate = self.datesList[index]
            shutdowns[telNum].append(randDate)
        return shutdowns

        #query for known telescope shutdowns
#        shutdowns = {}
#        for telNum in config.kTelescopes:
#            shutdowns[telNum] = []
#            #todo: query
#        return shutdowns


    def getInstrumentShutdowns(self, semester):

        #todo: temp: test data one random shutdown date per telescope
        shutdowns = {}
        for instr in config.kInstruments:
            shutdowns[instr] = []
            index = randrange(0, len(self.datesList))
            randDate = self.datesList[index]
            shutdowns[instr].append(randDate)
        return shutdowns

        #query for known telescope shutdowns
#        shutdowns = {}
#        for instr in config.kInstruments:
#            shutdowns[instr] = []
#            #todo: query
#        return shutdowns


    def initSchedule(self):

        #create blank schedule for each telescope
        self.schedules = {}
        for key, tel in config.kTelescopes.items():
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
            vEnd = vStart + int(slot['portion'] / config.kPortionPerc) - 1
            sStart = index 
            sEnd = sStart + int(portion / config.kPortionPerc) - 1

            if (sStart >= vStart and sStart <= vEnd) or (sEnd >= vStart and sEnd <=vEnd):
                return False

        return True


    def createDatesList(self, startDate, endDate):

        startDate = startDate.replace('-','')
        endDate   = endDate.replace('-','')
        dates = [d.strftime('%Y-%m-%d') for d in pandas.date_range(startDate, endDate)]
        return dates


    def getMoonDates(self, startDate, endDate):

        #todo: temp: test data
        dates = [
            ['2019-08-01', 'D'],
            ['2019-08-05', 'G-DL'],
            ['2019-08-10', 'B'],
            ['2019-08-21', 'G-DE'],
            ['2019-08-26', 'D'],
            ['2019-09-03', 'G-DL'],
            ['2019-09-08', 'B'],
            ['2019-09-20', 'G-DE'],
            ['2019-09-24', 'D'],
            ['2019-10-03', 'G-DL'],
            ['2019-10-07', 'B'],
            ['2019-10-19', 'G-DE'],
            ['2019-10-23', 'D'],
            ['2019-11-01', 'G-DL'],
            ['2019-11-06', 'B'],
            ['2019-11-17', 'G-DE'],
            ['2019-11-21', 'D'],
            ['2019-12-01', 'G-DL'],
            ['2019-12-06', 'B'],
            ['2019-12-16', 'G-DE'],
            ['2019-12-21', 'D'],
            ['2019-12-30', 'G-DL'],
            ['2020-01-05', 'B'],
            ['2020-01-15', 'G-DE'],
            ['2020-01-19', 'D'],
            ['2020-01-29', 'G-DL'],
        ]
        return dates

        #todo: query or calc moon dates


    def getMoonDatePreference(self, date, progId, instr):

        date = dt.strptime(date, "%Y-%m-%d")

        #start with second date and loop until not less than date
        for index in range(0, len(self.moonDates)-1):
            mDateEnd   = self.moonDates[index+1][0]
            mDateEnd = dt.strptime(mDateEnd, "%Y-%m-%d")
            if date < mDateEnd:
                break

        moonPrefs = self.programs[progId]['instruments'][instr]['moonPrefs']
        pref = moonPrefs[index]
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

        print ('getListItemByWeightedRandom', theList)

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
                print ('weighted random chosen: ', i, ' of ' , len(theList))
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
        import pprint
        pprint.pprint(self.schedules)
        print ('Semester: ', self.semester)
        for schedKey, schedule in self.schedules.items():            
            schedName = config.kTelescopes[schedKey]['name']
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
    
    
