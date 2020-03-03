# todo: high level
- [DONE] Keck proposal data translator tool
- [DONE] TOAST Framework
- [DONE] Algorithm logic
- [DONE] Schedule scoring
- Export to spreadsheet format (Carolyn)
- Save schedule to file and/or db
- Integration with larger TAC web tools
- Optimize for speed
- Schedule GUI display




#todo: details
- Cadence has a range.  we need to factor that in for date options
- swap command?
- Save/write out scheduled program
- target/airmass scoring (use lst@midnight data)
- real query for other data: shutdowns, moon phases, etc (see proposals.InstrumentUnavailable)
- classes: Block, Schedule?
- IDEA: When picking a slot, cascade down in groups. See if any moonIndex work.  If not, see if any 'P' work and so on.  Or can we achieve this with our weighting?
- Fix getReconfigScore. It really needs to define instrument positions and track state changes, for instance MOSFIRE switch to LRIS days later is still a reconfig.
- Implement runs attempts (ie progInstr blocks with adjacent moonIndex)
- NIRSPAO-NIRSPEC reconfig is worse than others.  Minimize NIRSPAO runs.  
- Consider laser runs?
- Consider same program night adjacency desireable? similar to runs?
- force small portions to different days for same ktn (ie avoid same program on same night for 1/2 and 1/4)
- Rule: Avoid 3-way or 4-way splits with 2 or more programs
- Engineering pref is to have a few each month preferably during bright time.  Should we allow some seeding of Engineering nights and avoid adjacency?
- Program ranking per institution
- option to run one of the telescopes only



# questions: 
- Q: How do you know whether to clump program blocks into runs or to spread them out?
- Q: If a card is slotted on an 'X' moon pref, what is more important?  To follow the suggested slot or find a non-X moon pref?  Or manually fix it for them?
- Q: Would you give a program a date that is "P" or "A" but not requested moonIndex if it meant you could save a reconfig?
- Q: Whats up with Subaru instrument selects?





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

