# Basic algorithm

- From program data, create full list of of program blocks to schedule. Example:
    [
        {progId:'C123', 'instr':'MOSFIRE', portion:1.0, run:1}
        {progId:'N234', 'instr':'OSIRIS',  portion:0.5, run:2}, 
        {progId:'U345', 'instr':'HIRESr',  portion:0.25, cadence: {'startDate': '2019-04-05', 'rangeDays': 3, 'slotIndex': 2, 'consecutive': 6}}, 
    ]
   (Runs: Use 'run' to indicate a run of consecutive nights. Some instruments prefer runs.)
   (Cadence: Defines repititive scheduling from a start date.)
- Divide blocks array into groups by size/difficulty (cadence, runs, full, 3/4, 1/2, 1/4) and consider the blocks in decreasing order of difficulty.
- For each block:
    - Get list of all remaining valid dates slots and score each one based on several factors and sort by score.
    - Pick a random slot from the top scores (ie weighted randomness with cutoff)
- Score schedule (Getting the scoring right is very important)
- Repeat X number of times and take best schedule or repeat until high score converges


