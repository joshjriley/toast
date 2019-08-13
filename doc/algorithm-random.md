# Data queries needed
- Program data
- Telescope and instrument shutdown dates
- Moon phase date ranges


# Basic algorithym
- From program data, create full list of of program blocks to schedule. Example:
    [
        {progId:'C123', 'instr':'MOSFIRE', portion:1.0, run:1}
        {progId:'N234', 'instr':'OSIRIS',  portion:0.5, run:2}, 
        {progId:'U345', 'instr':'HIRESr',  portion:0.25, cadence: {'startDate': '2019-04-05', 'rangeDays': 3, 'slotIndex': 2, 'consecutive': 6}}, 
    ]
   (Runs: Use 'run' to indicate a run of consecutive nights. Some instruments prefer runs.)
   (Cadence: Defines repititive scheduling from a start date.)
- Divide blocks array into groups by size/difficulty (cadence, runs, full, 3/4, 1/2, 1/4). 
- For each block:
    - Get list of all remaining valid dates slots and score each one based on several factors and sort by score.
    - Pick a random slot from the top scores (ie weighted randomness with cutoff)
- Score schedule
- Repeat X number of times and take best or repeat until high score converges


# Special considerations:
- If there are more requests than space in calendar:
    - Shorten full nights and 3/4 nights to fit in remaining quarter nights.
    - Shorten full nights to fit in remaining half nights.

- If there is remaining space in calendar:
    - Bump up quarter nights to half nights first.
    - Bump up halfs and 3/4 to fulls.


# Factors in scoring a schedule
- number of instrument switches
- visit is on preferred/acceptable/neutral/bad date
- visit date and time has priority target visible

