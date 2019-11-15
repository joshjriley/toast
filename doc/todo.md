# todo: high level
- [DONE] Keck proposal data translator tool
- [josh] Algorithm logic
- Schedule scoring
- Airmass/target scoring
- Schedule output display



#todo: proposal translator tool
- Implement classes for: Program, ProgInstr, Block


# todo: algorithm
- Implement cadence
- Implement runs
- Implement instrument switch incompatibility (ie LRIS/MOSFIRE)
- Deal with instrument base config info (ie HIRESr and HIRESb are both base HIRES)
- Deal with multi instrument selection (ie NIRC2+NIRESPEC)
- force small portions to different days (ie avoid same program on same night for 1/2 and 1/4)
- real query for other data: shutdown, moon phases, etc



# questions: 
- The "Cadence" form seems like a misnomer since it is really only for selecting exact dates.  Should it say "Cadence/Exact Dates"?
- Whats up with Subaru instrument selects?


# coversheet form changes needed:
- Make it clear not to put dates in the special request field. (parse for them and warn)?
- Make it clear that HST is used throughout.  Where was it that Carolyn said UT date was used?




#misc
- Consider a sequential approach instead of random?
