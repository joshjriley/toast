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




#todo: framework
- export to carolyn special spreadsheet
- save, load 
- give line ids to schedule output and provide swap command?
- Save/write out scheduled program
- In output, put in rightmost column that notes anything special, warnings, etc  
- option to run one of the telescopes only
- switch to scoring model where we score each block independently.  block happiness = a % of max score.  max score is hitting all config score params.  though for some blocks certain ones don't apply (ie reqDate) so max is different).  should scoring always be additive?
- real query for other data: shutdowns, moon phases, etc (see proposals.InstrumentUnavailable)
- classes: Block, Schedule



# todo: random algorithm
- IDEA: After each run, look at each block's score in relation to others and bump up order if it didn't find a slot or scored poorly.
- Fix getReconfigScore. It really needs to define instrument positions and track state changes, for instance MOSFIRE switch to LRIS days later is still a reconfig.
- Implement runs attempts (ie progInstr blocks with adjacent moonIndex)
- NIRSPAO-NIRSPEC reconfig is worse than others.  Minimize NIRSPAO runs.  
- Consider laser runs?
- Consider same program night adjacency desireable? similar to runs?
- force small portions to different days for same ktn (ie avoid same program on same night for 1/2 and 1/4)
- Rule: Avoid 3-way or 4-way splits with 2 or more programs
- Engineering pref is to have a few each month preferably during bright time.  Should we allow some seeding of Engineering nights and avoid adjacency?
- Program ranking per institution



# questions: 
- The "Cadence" form seems like a misnomer since it is really only for selecting exact dates.  Should it say "Cadence/Exact Dates"?
- Whats up with Subaru instrument selects?


# coversheet form changes needed:
- Make it clear not to put dates in the special request field. (parse for them and warn)?
- Make it clear that HST is used throughout.  Where was it that Carolyn said UT date was used?




#misc
- If we really need %dark, moon@midnight etc in export, then we need data from http://ucolick.org/calendar/keckcal2011-20/index.html also available from Carolyn's spreadsheet (https://www.keck.hawaii.edu/twiki/bin/view/Main/ProposalCoverSheetNewSemester)
- allow random fluctuation of config scoring params?
- config var to keep top N schedules in memory.  menu option to switch to sched N.
- Kinda need a ToastKeck class that is for Keck specific scoring.
- run a pre-report that flags programs with conflicting moonPrefs and moonIndex/reqDate info?
- Consider data input for 3/4, 1/4 bundled pairs?  Or just have scheduler set this manually?
- Consider last day of previous semester (for runs, reconfigs etc)
- Carolyn requests an export of priority targets to starlist (k1 and k2 starlist files)
- Export to spreadsheet format that resembles Carolyn's starting point
- Consider a sequential approach instead of random?
- perhaps move a bunch of the input data into 2020A-telescopes.json, like shutdowns, instruments, etc.  The assumption is there would be some other translator that would create this file in this format.

