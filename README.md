# TOAST
Telescope Observing Automated Scheduling Tool

Given a list of approved observing program proposals for a period of time, generate an observing schedule meeting each program's constraints as best as possible.  


# Description:
PIs submit proposals before each semester for each of their observing programs.  Programs can request one or more nights using one or more instruments on both of the Keck telescopes.  Proposals can also provide, based on the moon phase, preferred nights and nights to avoid.  Proposals can also provide info on priority targets as a list of RA/DECs.  Scheduled observing nights can be divided and shared into full, half, and/or quarter portions of the night.

Other considerations come into play such as holidays, telescope shutdowns, instrument downtime, scientific conferences, special requests, etc.

The output will be a schedule which is a list of Visits (ie night program portions) that fill the schedule for each observing night in the semester date range.  A Visit will consist simply of the following data for each record:
- Date
- Portion of Night
- Instrument
- ProgId


# Usage:

    python Toast.py [semester] --method [method]
    python Toast.py 2019B --method random

