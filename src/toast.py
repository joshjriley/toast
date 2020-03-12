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

import logging
log = logging.getLogger('toast')

from scheduler_random import SchedulerRandom



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
    parser = argparse.ArgumentParser(description="Start Keck scheduler")
    parser.add_argument("configFile", type=str, help="Config file for run.")
    args = parser.parse_args()

    #run the scheduler
    scheduler = SchedulerRandom(args.configFile)
    scheduler.start()

    
    
