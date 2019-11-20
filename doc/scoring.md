Scoring a schedule is independent of the algorithm chosen to create the schedule.


## Factors in scoring a schedule
- Certain instrument switches are bad.  Need weighting table for instrument switches.
- Block scheduled in requested moon phase (block.moonIndex) (P,A,N,X)
- (high) If specified, block scheduled on requested date (block.reqDate)
- (high) If specified, block scheduled in requested portion of night (block.reqPortion)
- Block datetime has priority target(s) visible
- Cadence type blocks should have more weight given to meeting their moonIndex, reqDate, and/or reqPortion
- Dark requested moon phase time should have higher priority for hitting its moonIndex, reqDate, and/or reqPortion


(todo: finish this)
