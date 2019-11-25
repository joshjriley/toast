Scoring a schedule should be independent of the algorithm chosen to create the schedule.


## Factors in scoring a schedule
- Number of instrument reconfigs (certain reconfigs are worse than others)
- Number of instrument switches during night.
- Scheduled moon preference (P, A, N, X)
- Block scheduled in requested moon phase (block.moonIndex)
- If specified, block scheduled on requested date (block.reqDate)
- If specified, block scheduled in requested portion of night (block.reqPortion)
- Number of priority target(s) visible during date/portion
- Dark requested moon phase time should have higher priority for hitting its moonIndex, reqDate, and/or reqPortion
- Institution particularness, balance?  Score institutions happiness based on collective block happiness average.


(todo: finish this)
