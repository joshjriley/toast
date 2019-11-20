

## notes:
- [done] TACs can specify specific dates and/or portion of night and these should be followed if at all possible. (cadence)
- [done] Consider date-critical observations first (ie cadence and those that were given a date by TAC). 
- Consider dark time requests first, then grey, then bright. (Since bright requests can obviously use dark time)
- For each classical program instrument entry, if the number of "P"s is one or two back-to-back this typically represents a cluster of observations that we should schedule consecutively.  If there are may "P"s spread out, this *may* indicate to spread the program out though typically they will use multiple instrument entries to indicate a different cluster.  We want to minimize observer travel requirements.
- Reconfig is more important than instrument runs, though runs are nice too.  Reconfig compat chart: https://www2.keck.hawaii.edu/observing/instrumentaccess.html
- Cadence form input dates are absolutely strict.  
- concept of "paired nights" where it is requested (special) that two different half-night programs could be scheduled on the same night.  
- Probably need a pre-definitions file for special cases like 'paired nights' etc.
- Priority targets is sort of duplicate info b/c they probably did the work in the preferences section.  However, we can use it anyway for weighting the block scoring in case it is needed.
- "X" in moon phase is an absolute no as is DatesToAvoid.
- Engineering can be used as the final blocks filler.  Well unless there are full engineering nights.  Hmm, maybe then put them at the end of each subgroup grouped by size if we know the size of engineering nights.
- We may end up short in the end by a night or two.  That is ok.  Leave those unscheduled.
- If you have to use a grey time for a half night, make sure to consider the DE or DL.
- Full nights sometimes need to be split, but rate.
- Program rankings are independent numerical systems per TAC (letter code?)




## misc
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

- Research the "Course Scheduling Problem"
http://digitalcommons.calpoly.edu/cgi/viewcontent.cgi?article=1255&context=theses


# Special considerations:
- If there are more requests than space in calendar:
    - Shorten full nights and 3/4 nights to fit in remaining quarter nights.
    - Shorten full nights to fit in remaining half nights.

- If there is remaining space in calendar:
    - Bump up quarter nights to half nights first.
    - Bump up halfs and 3/4 to fulls.





GUI would allow you to drag and drop and lock blocks and save all to DB
Then you could run algo to juggle non-locked blocks
Could revert to previous saved position



## TERMINOLOGY
- block: A block of time that is to be scheduled.
- portion: Refers to a position and size combination such as "first quarter" or "second half"
- size: The percentage size of a block



## PROGRAM INPUTS
Inputs will be in json format and can be loaded from json file or database (mongo?)

Inputs:
- telShutdowns: An array of dates when telescopes are completely unavailable.  Example:
    [
        {"date" : "2019-08-04", "tel" : "1"},
        {"date" : "2019-08-05", "tel" : "2"},
    ]

- instrShutdowns: An array of dates when instruments are completely unavailable.  Example:
    [
        {"date" : "2019-08-06", "instr" : "OSIRIS"},
        {"date" : "2019-08-07", "instr" : "NIRES"},
    ]

- moonPhases: A time-ordered array of moon phase date ranges and phase type (D, L, G-DE, G-DL). Example:
    [
        {"start" : "2019-08-01", "end" : "2019-08-04", "type" : "D"},
        {"start" : "2019-08-05", "end" : "2019-08-08", "type" : "G-DL"},
    ]

- blocks: A list of all schedulable block units.  Each must have the following vars:
  - progId      str     Program code (for quick index to parent program) (ie N123)
  - instrId     int     Array index of programs "instrument" array (for quick index to parent program instrument data)
  - semester    str
  - instrument  str
  - type        str     Valid values: [classical, cadence]
  - size        float   The percentage size of the block.  Must divisible by config.portionPerc up to max 1.0.  Valid values: [0.25, 0.5, 0.75, 1.0]
  - moonIndex   int     The desired TAC scheduled moon phase index. Index must align with moonPhases array.
  - moonPrefs   array   An array of moon prefs to use in the event we cannot schedule during moonPhase. Valid values: [P, A, N, X]
  - reqPortion  str     (optional) The requested portion of the night.  If specified, it is assumed highly desireable. Valid values: [1h, 2h, 1q, 2q, 3q, 4q].
  - reqDate     date    (optional) The requested date.  If specified, it is assumed highly desireable.

    Example JSON data:
        {
            "semester"   : "2019B",
            'progId'     : "N123",
            "instrument" : "MOSFIRE",
            "type"       : "classical",
            "size"       : 0.5,
            "moonIndex"  : 2
            "moonPrefs"  : ["P","A","N","X","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N","N"],
            "reqPortion" : "2h",
            "reqDate"    : "2019-09-11",
        },






## ISSUES
***Problem***: TACcards entries typically represent a schedulable block unit.  By default a set of program instrument blocks (pig) are divided up by a number of approved nights of approved size.  But, the scheduler can change the number of cards and so we look to TACschedule to see what blocks were actually scheduled by the TAC.  One issue with this is that sometimes a scheduler will leave the block as a chunk of time (ie 3N for 2019B_C269) without dividing it up (though this may happen less now that we auto-divide into blocks).  How do we know that a block is a schedulable unit versus something that needs to be divided up?  Perhaps the only way is to look at the requested portion and see if it is divisible into block chunk.  In this case, can we assume they were lazy and didn't divide it up?  Carolyn says she only looks at the requested portion.  But, there are cases like 2019B_C272 where they approve a smaller amount of time.  In this case, we should look at approved/scheduled blocks.
***IN ANY CASE For the purposes of this code, we should just assume these will be manually rectified into schedulable blocks.***



##misc
program runs: It is preferred to schedule same program blocks back-to-back
instrument runs: Some instruments prefer to be scheduled in runs



