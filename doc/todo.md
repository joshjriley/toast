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
!- Add in DateSpecific (see progInstr['dateOptions'])
!- Program ranking per institution
!- Save/load entire schedule run (db or file) 
!- force small portions to different days for same ktn (ie avoid same program on same night for 1/2 and 1/4) (ie dup col in show report) (we do this in scoreBlockSlot but not working well)
!- Normalize scoring
- Score Carolyn's 2020A schedule (this may be impossible since there is no linkage to specific progInstr, but we could do another type of scoring)
- target/airmass scoring (use lst@midnight data)
- real query for other data: shutdowns, moon phases, etc (see proposals.InstrumentUnavailable)
- IDEA: When picking a slot, cascade down in groups. See if any moonIndex work.  If not, see if any 'P' work and so on.  Or can we achieve this with our weighting?
- Fix getReconfigScore. It really needs to define instrument positions and track state changes, for instance MOSFIRE switch to LRIS days later is still a reconfig.
- Improve adjacent instrument scoring
- NIRSPAO-NIRSPEC reconfig is worse than others.  Minimize NIRSPAO runs.  
- Consider laser runs?
- Rule: Avoid 3-way or 4-way splits with 2 or more programs
- Engineering pref is to have a few each month preferably during bright time.  Should we allow some seeding of Engineering nights and avoid adjacency?
- option to run one of the telescopes only
- check if the total proposed hours exceeds semester hours
- check for Cadence/Specific date conflicts
- instead of or additionally, have random movement of order by position instead of score randomness.



# questions: 
- Q: How do you know whether to clump program blocks into runs or to spread them out?  A: If same or adjacent moonIndex
- Q: If a card is slotted on an 'X' moon pref, what is more important?  To follow the suggested slot or find a non-X moon pref?  Or manually fix it for them?
- Q: Would you give a program a date that is "P" or "A" but not requested moonIndex if it meant you could save a reconfig?
- Q: Whats up with Subaru instrument selects?
- Q: What is the deal with Planet Hunters again?





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

