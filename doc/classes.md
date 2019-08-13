
# Toast: Main program that builds schedule    

This class contains the argument parser and code to create the correct type of Toast subclass depending on which method you want to use.  It also contains common functions and variables for all Toast subclasses.

    semester            str     Semester code  (ie 2019B)
    programs            dict    Dictionary of approved proposal program objects
    schedules           list    List of scheduled observing blocks for each telescope
    getSemesterDates()          Get start and end dates of semester
    createDatesList()           Get list of consecutive dates in date range
    getMoonDates()              Get list of moon brightness periods in date range
    getPrograms()               Get list of approved proposal programs in date range
    getTelescopeShutdowns()     Get list of telescope shutdown dates in date range
    getInstrumentShutdowns()    Get list of instrument shutdown dates in date range
    createBlankSchedule         Creates a blank schedule data structure
    createSchedule()            (abstract) Creates the schedule assuming all inputs necessary are loaded

# ToastRandom: A subclass of Toast implementing a Randomness algorithmic solution

    createSchedule()            This subclass start point for solving schedule creation problem


# Program: An approved proposal

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
                "utDate": '2019-08-02,
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


# Schedule

A schedule is a consecutive list of dates for a particular telescope (ie K1, K2).  Each date night is filled with a number of blocks that fill all the potential slots in the schedule that night.

NOTE: In lieu of a full OOP approach, we will just define this data as a JSON object.  Here is an example of a few days of scheduled K1:

    'K1': 
    {
        'nights': 
        {
            '2019-08-01': 
            {
                'slots': 
                [
                    {'index': 0, 'instr': 'OSIRIS',  'portion': 0.5, 'progId': 'C345'},
                    {'index': 2, 'instr': 'MOSFIRE', 'portion': 0.5, 'progId': 'N123'},
                }
            },
            '2019-08-02': 
            {
                'slots': 
                [
                    {'index': 0, 'instr': 'OSIRIS',  'portion': 0.75, 'progId': 'C345'},
                    {'index': 3, 'instr': 'MOSFIRE', 'portion': 0.25, 'progId': 'N123'},
                }
            }
        }
    }


# Block: An observing period for a program on a particular night

Blocks are discrete schedulable chunks of a program to be slotted into the schedule.  For instruments that prefer runs, use 'num' to group together consecutive blocks.


    {
        'instr':   'NIRES',
        'progId':  'C123',
        'portion': 0.5,
        'telNum':  'K1',
        'num':     3,
    }

