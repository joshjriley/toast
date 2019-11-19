
# Toast: Base class and start point

This class contains common functions and variables for all Toast subclasses, so as to standardize the inputs and outputs of the program.  It also contains the command line parser and code to instantiate the correct type of Toast subclass depending on which method you want to use.  A basic list of member vars and functions:

    semester            str     Semester code  (ie 2019B)
    programs            dict    Collection of approved proposal program objects (main input)
    schedule            dict    List of scheduled observing blocks for each telescope (main output)
    getSemesterDates()          Get start and end dates of semester
    getMoonDates()              Get list of moon brightness periods in date range
    getPrograms()               Get list of approved proposal programs in date range
    getTelescopeShutdowns()     Get list of telescope shutdown dates in date range
    getInstrumentShutdowns()    Get list of instrument shutdown dates in date range
    createBlankSchedule         Creates a blank schedule data structure
    createSchedule()            (abstract) Creates the schedule assuming all inputs necessary are loaded

# ToastRandom: A subclass of Toast implementing a Randomness algorithmic solution

    createSchedule()            This subclass start point for solving schedule creation problem


# Program: An approved proposal needing to be scheduled

A program is an approved proposal that we need to schedule.  A program consists of one or more instrument requests each needing one more more nights of a particular portion of the night.  Thus, dirived from a program is a list of scheduled observing Blocks that consitute a single unit that must be slotted into the schedule.  Programs also contain information on preferred dates and dates to avoid.

NOTE: In lieu of a full OOP approach, we will just define the program data as a JSON object.  Here is an example of a classical and a cadence program in JSON format:

    "N123":
    {
        "semester": "2019B", 
        "type": "classical",
        "instruments":
        {
            "MOSFIRE":
            {
                "portion": 0.25,
                "nights": 8,
                "moonPrefs": ["P","A","N","X","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N"]
            },
            "NIRES":
            {
                "portion": 0.5,
                "nights": 5,
                "moonPrefs": ["X","P","A","N","P","A","N","X","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N"]
            }
        },
        "datesToAvoid":["2019-08-02", "2019-08-03"],
        "priorityTargets": 
        [
            {"target":"xxx1", "ra":123.456, "dec":234.345, "epoch":"j2000", "priority":5},
            {"target":"xxx2", "ra":123.456, "dec":234.345, "epoch":"j2000", "priority":5}
        ]
    },
    "C234":
    {
        "semester": "2019B", 
        "type": "cadence",
        "instruments":
        {
            "MOSFIRE":
            {
                "utDate": '2019-08-02',
                "rangeDays": 4,
                "portion": 1.0,
                "index": 2,
                "consecNights": 4
            },
        },
        "datesToAvoid":["2019-08-02", "2019-08-03"],
        "priorityTargets": 
        [
            {"target":"xxx1", "ra":123.456, "dec":234.345, "epoch":"j2000", "priority":5},
            {"target":"xxx2", "ra":123.456, "dec":234.345, "epoch":"j2000", "priority":5}
        ]
    },



# Block: An observing period for a program on a particular night

Blocks are discrete schedulable chunks of a program to be slotted into the schedule.  For instruments that prefer runs, use 'num' to group together consecutive blocks.


    {
        'tel'    : 'K1',            #dict key for telescope
        'ktn'    : 'C123',          #program id
        'instr'  : 'NIRES',         #instrument
        'size'   : 0.5,             #size as perc of night
        'num'    : 1,               #number of these block instances to schedule consecutively
        'moonIndex': 2,             #index to requested moon phase from TAC scheduling
        'reqDate': '2019-08-22',    #specific date requested from TAC scheduling
        'reqPortion': '2h'          #specific night portion requested from TAC scheduling
    }



# Schedule

A schedule encapsulates all the info needed to define an output schedule.  This includes a consecutive list of semester dates for a each telescope (ie K1, K2).  Each date night is filled with a number of blocks of size that fill positional slots in the schedule that night.  A schedule also has a meta object for keeping stats and scores.

NOTE: In lieu of a full OOP approach, we will just define this data as a JSON object.  Here is an example of a few days of scheduled K1:

    {
        'meta':
        {
            'score': 100
        } ,
        'telescopes':
        {
            'K1': 
            {
                'nights': 
                {
                    '2019-08-01': 
                    {
                        'slots': 
                        [
                            {'index': 0, 'size': 0.5, 'instr': 'OSIRIS',  'ktn': 'C345'},
                            {'index': 2, 'size': 0.5, 'instr': 'MOSFIRE', 'ktn': 'N123'}
                        }
                    },
                    '2019-08-02': 
                    {
                        'slots': 
                        [
                            {'index': 0, 'size': 0.75, 'instr': 'OSIRIS',  'ktn': 'C345'},
                            {'index': 3, 'size': 0.25, 'instr': 'MOSFIRE', 'ktn': 'N123'}
                        }
                    }
                }
            }
        }
    }
