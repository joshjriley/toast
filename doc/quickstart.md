## Checkout code
Use webrun@vm-webtools

    cd
    git clone https://github.com/joshjriley/toast
    cd toast


## Setup config.yaml
Copy template config file:

    mkdir data/[semester]
    cp src/config.yaml data/[semester]/config-[semester].yaml

Edit the following sections of config file:
- semester
- files
- database


## Retrieve proposal data
Run special program that collects proposal and other needed data and writes to data files
    python src/data_translator_keck.py [semester] [configFile] [outdir]
    python src/data_translator_keck.py 2020A data/config-2020A.yaml data/2020A/



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
Example '2020A-instr-shutdowns.json' file:
    [
        {"instr": "OSIRIS-LGS",  "startDate": "2020-02-01", "endDate": "2020-04-14"},
        {"instr": "OSIRIS-NGS",  "startDate": "2020-02-01", "endDate": "2020-03-16"},
        {"instr": "NIRSPEC",     "startDate": "2020-02-01", "endDate": "2020-03-12"},
        {"instr": "NIRSPAO-LGS", "startDate": "2020-02-01", "endDate": "2020-03-12"},
        {"instr": "NIRSPAO-NGS", "startDate": "2020-02-01", "endDate": "2020-03-12"}
    ]

## Define moon phases
Example 2020A-moon-phases.json file:
    [
        {"start" : "2019-08-01", "end" : "2019-08-04", "type" : "D"},
        {"start" : "2019-08-05", "end" : "2019-08-09", "type" : "G-DL"},
        .
        .
        .
        {"start" : "2020-01-19", "end" : "2020-01-28", "type" : "D"},
        {"start" : "2020-01-29", "end" : "2020-02-01", "type" : "G-DL"},
    ]


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

    python toast.py [config]
    python toast.py data/2020A/config-2020A-yaml


