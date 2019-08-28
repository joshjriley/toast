# todo
- Implement cadence
- Implement runs
- instrument switch incompatibility (ie LRIS/MOSFIRE)
- schedule scoring
- real queries for program data and shutdown data
- real query for moon phases
- Airmass, target scoring
- force small portions to different days (ie avoid same program on same night for 1/2 and 1/4)
- Deal with instrument base config info (ie HIRESr and HIRESb are both base HIRES)
- Deal with multi instrument selection (ie NIRC2+NIRESPEC)
- Consider a sequential approach instead of random?


# questions: 
- The "Cadence" form seems like a misnomer since it is really only for selecting exact dates.  Should it say "Cadence/Exact Dates"?
- Whats up with Subaru instrument selects?


# notes:
- NOTE: We are not loading info from coversheet db tables but rather from post-TAC tables.
- 
- TACs can specify specific dates and/or portion of night and these should be followed if at all possible.
- Consider date-critical observations first (ie cadence and those that were given a date by TAC). 
- Consider dark time requests first, then grey, then bright. (Since bright requests can obviously use dark time)
- Always go for "P" and only use "A" if necessary.  Flag for review if we have to use neutral.  "X" must avoid.  This places more emphasis on ordering the blocks.
- For each classical program instrument entry, if the number of "P"s is one or two back-to-back this typically represents a cluster of observations that we should schedule consecutively.  If there are may "P"s spread out, this *may* indicate to spread the program out though typically they will use multiple instrument entries to indicate a different cluster.  We want to minimize observer travel requirements.
- Reconfig is more important than instrument runs, though runs are nice too.  Reconfig compat chart: https://www2.keck.hawaii.edu/observing/instrumentaccess.html
- Cadence form input dates are absolutely strict.  
- concept of "paired nights" where it is requested (special) that two different hald-night programs could be scheduled on the same night.  
- Probably need a pre-definitions file for special cases like 'paired nights' etc.
- Priority targets is sort of duplicate info b/c they probably did the work in the preferences section.  However, we can use it anyway for weighting the block scoring in case it is needed.
- "X" in moon phase is an absolute no as is DatesToAvoid.
- Engineering can be used as the final blocks filler.  Well unless there are full engineering nights.  Hmm, maybe then put them at the end of each subgroup grouped by size if we know the size of engineering nights.
- We may end up short in the end by a night or two.  That is ok.  Leave those unscheduled.
- If you have to use a grey time for a half night, make sure to consider the DE or DL.
- Full nights sometimes need to be split, but rate.
- Program rankings are independent numerical systems per TAC (letter code?)


# coversheet form changes needed:
- Make it clear not to put dates in the special request field. (parse for them and warn)?
- Make it clear that HST is used throughout.  Where was it that Carolyn said UT date was used?




# misc
- look into "Job Shop Problem"
- find Airmass calc api or python code
    http://www.eso.org/sci/bin/skycalcw/airmass
    http://catserver.ing.iac.es/staralt/index.php
    http://astro.swarthmore.edu/airmass.cgi
    http://www.eso.org/sci/observing/tools/calendar/airmass.html                
    http://www.ucolick.org/~magee/observer/  (python download)  
    http://simbad.u-strasbg.fr/simbad/sim-id?Ident=Vega
    http://ssd.jpl.nasa.gov/horizons.cgi
- Check out SPIE paper: "Research on schedulers for astronomical observatories"

- Ability to pre-lock certain program assignments before builder is run (ie manual intervention)
- Meetings/PI conflicts
- Holidays
- PI particularness
- Offline instruments (sometimes defined, sometimes Carolyn picks downtime
- Segex defined dates
- special requests
- date specific requests (should be cadence but they put them in as classical)
- minimize instrument reconfigs, schedule runs (nirspao minimize runs, consolidate esi runs)
- machine learning?


# Special considerations:
- If there are more requests than space in calendar:
    - Shorten full nights and 3/4 nights to fit in remaining quarter nights.
    - Shorten full nights to fit in remaining half nights.

- If there is remaining space in calendar:
    - Bump up quarter nights to half nights first.
    - Bump up halfs and 3/4 to fulls.


# Factors in scoring a schedule
- number of instrument switches
- visit is on preferred/acceptable/neutral/bad date
- visit date and time has priority target visible
(todo: finish this)


