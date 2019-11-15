# Overview

The thinking for this approach is that the complexity of the problem and number of variables is large enough that solving it in some sort of exact manner is too hard.  So, we will use some degree of randomness for the difficult parts.  We can do some basic filtering, scoring and sorting up front to get the scheduling off in the right direction, but at some level we will fill in the schedule randomly at the point where our computer science/algorithm skills are lacking.  Once we have a schedule, we will score it in a detailed manner.  We can then repeatedly generated thousands or millions of schedules until we produce the best schedule based on score.  It stands to argue that if you can acceptible score a schedule, then there must be some graphing/mapping algorithm that can then solve the problem to some exact degree... I just don't know what that is or how it would look.  From experience, I have had good luck with this approach to solving complex problems, so we will try it first.  --Josh



# Basic algorithm

- Load program data

- Create array of blocks to schedule
    - Blocks need to link back to progInstr parent and program parent.
    - Blocks can be a run (consecutive days to schedule)
    - Blocks with requested Date cannot be part of run.
- Sort block's by priority score based on :
    - size (size * run length)
    - requested Specific Date
    - Institution priority factor
    - Randomness factor
    - Admin priority factor (program, progInstr, block)
- In order of priority, schedule each block according to these steps:
    - Try specific date, if requested
    - Try dates in scheduled moon range
    - Try dates for all moon prefs
        - Use existing weighted randomness with cutoff?
<!--     - Get list of all remaining valid dates slots and score each one based on several factors and sort by score.
    - Pick a random slot from the top scores (ie weighted randomness with cutoff)
 -->
    - If a block run cannot be scheduled, divide in half and/or treat individually?

- Score schedule (Getting the scoring right is very important)
    - ????

- Repeat X number of times and take best schedule or repeat until high score converges


