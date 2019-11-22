# todo: high level
- [DONE] Keck proposal data translator tool
- [jr] TOAST Framework
- [jr] Random algorithm logic
- Schedule scoring
- Airmass/target scoring
- Schedule GUI display
- Save schedule to file and/or db
- Integration with larger TAC web tools
- Optimize for speed



#todo: proposal translator tool
- Implement classes for: Program, ProgInstr, Block


#todo: framework
- Engineering inputs
- Warning for reqDate or reqPortion that was not met
- Warning if assigned to Neutral or X
- block happiness = a % of max score.  max score is hitting all config score params.  though for some blocks certain ones don't apply (ie reqDate) so max is different).  should scoring always be additive?
- In output, put in rightmost column that notes anything special, warnings, etc (matches reqDate, !!NO MATCH reqPortion!!, 
- In output, mark empty slots visible
- real query for other data: shutdowns, moon phases, etc
- Deal with instrument base config info (ie HIRESr and HIRESb are both base HIRES)



# todo: random algorithm
- Implement runs
- force small portions to different days (ie avoid same program on same night for 1/2 and 1/4)
- avoid half nights straddling middle of night?



# questions: 
- The "Cadence" form seems like a misnomer since it is really only for selecting exact dates.  Should it say "Cadence/Exact Dates"?
- Whats up with Subaru instrument selects?


# coversheet form changes needed:
- Make it clear not to put dates in the special request field. (parse for them and warn)?
- Make it clear that HST is used throughout.  Where was it that Carolyn said UT date was used?




#misc
- Consider a sequential approach instead of random?
