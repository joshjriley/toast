## Setup config.yaml
todo


## Retrieve data
todo


## Define telescope shutdowns and engineering blocks
Example '2020A-engineering.json' file:

	[
	    {"tel": "1", "schedDate": "2020-05-05", "instr": "PCS", "ktn": "2020A_ENG", "schedIndex": 0, "size": 1.0, "type": "Segment Exchange"},
	    {"tel": "1", "schedDate": "2020-05-06", "instr": "PCS", "ktn": "2020A_ENG", "schedIndex": 0, "size": 1.0, "type": "Segment Exchange"},
	    {"tel": "1", "schedDate": "2020-05-07", "instr": "PCS", "ktn": "2020A_ENG", "schedIndex": 0, "size": 0.5, "type": "Seg Exch"},
	    {"tel": "1", "schedDate": "2020-05-07", "instr": "TBD", "ktn": "2020A_ENG", "schedIndex": 2, "size": 0.5, "type": "Engineering"},
	    {"tel": "2", "schedDate": "2020-07-29", "instr": "",    "ktn": "2020A_ENG", "schedIndex": 0, "size": 1.0, "type": "SHUTDOWN"}
	]


## Define instrument shutdowns
todo


## Define moon phases
todo


## Scheduling Directives

You can set the following keywords for program data entries to force scheduling behavior:

KTN entries :
- ???

"instruments" entries :
- ???

"blocks" entries:
- "schedDate": Fixed scheduled yyyy-mm-dd date
- "schedIndex": Fixed scheduled slot index number from 0 to 3
- "orderScore": Fixed order score for pre-ordering which blocks to schedule first.


## Run TOAST