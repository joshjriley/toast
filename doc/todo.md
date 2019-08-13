# todo
- Implement cadence
- Implement runs
- instrument switch incompatibility (ie LRIS/MOSFIRE)
- schedule scoring
- real queries for program data and shutdown data
- real query for moon phases
- Airmass, target scoring
- force small portions to different days?
- Deal with instrument base config info (ie HIRESr and HIRESb are both base HIRES)
- Deal with multi instrument selection (ie NIRC2+NIRESPEC)
- Whats up with Subaru instrument selects?
- Should we assume if they put an "X" in a moon date range but didn't list individual dates below that they don't want the entire date range?
- Consider a sequential approach instead of random?


# questions: 
- From experience, what order do you consider first when scheduling (ie cadence first, then instr runs, full, 3/4, 1/2, 1/4)?
- How do we typically spread out non-cadence nights?  Try for optimize for preferences and priority targets first?  Otherwise, spread out across semester?
- What is a good strategy for creating instrument runs?
- Do we want to minimize instrument switches?  Are some instrument switches more painful than others?  ie K1DM3 switching vs ?
- Do we typically avoid scheduling the same program on the same night (ie two 1/2 nights, same night , same program)
- Are cadence observations strict with start date and delta and nightPart?
- Having trouble understanding cadence input form?  What is Range input? How do you requests every nth night?
- How are priority targets and their ranking considered?  Just try and optimize airmass for each in a weighted fashion?
- Are "Dates to Avoid" considered an absolute no?  How is the 'X' in moon phase preferences considered?  Only coupled in relation to Dates to Avoid?
- Should we change form to say "X = cannot observe (please list specific dates in the Date to Avoid section below)"
- What to do if proposal hours are greater/less than semester hours?
- What are common special requests that we could avert with some additional form inputs?



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

