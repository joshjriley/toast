# Overview

The thinking for this approach is that the complexity of the problem and number of variables is large enough that solving it in some sort of exact manner is too hard.  So, we will use some degree of randomness for the difficult parts.  We can do some basic filtering, scoring and sorting up front to get the scheduling off in the right direction, but at some level we will fill in the schedule randomly at the point where our computer science/algorithm skills are lacking.  Once we have a schedule, we will score it in a detailed manner.  We can then repeatedly generated thousands or millions of schedules until we produce the best schedule based on score.  It stands to argue that if you can acceptible score a schedule, then there must be some graphing/mapping algorithm that can then solve the problem to some exact degree... I just don't know what that is or how it would look.  From experience, I have had good luck with this approach to solving complex problems, so we will try it first.  --Josh



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

