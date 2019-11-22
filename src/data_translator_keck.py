import os
import sys
import yaml
import json
import pandas
import datetime
import db_conn



#todo: Load this from config file
telescopes_assoc = { 
    "1": ["LRIS-ADC","LRISp-ADC","HIRESr","HIRESb","OSIRIS-NGS","OSIRIS-LGS","MOSFIRE"], 
    "2": ["DEIMOS","ESI","ESI-ifu","KCWI","NIRSPEC","NIRSPAO-NGS","NIRSPAO-LGS","NIRC2-NGS","NIRC2-NGS+NIRSPEC", "NIRC2-NGS+NIRSPAO", "NIRC2-LGS", "NIRC2-LGS+NIRSPEC", "NIRC2-LGS+NIRSPAO", "NIRES"]
    } 


def jsonConverter(o):
    if isinstance(o, datetime.date):
        return o.__str__()



def queryProgramData(semester, dbConfigFile):

    #db connection
    dbc = db_conn.db_conn(dbConfigFile, configKey='database', persist=True)
    if not dbc: return False


    #programs object to store all results
    programs = {}


    #------------------------------------------------------------------------------
    # Get approved programs (classical and cadence)
    #------------------------------------------------------------------------------
    query1 = f"select KTN from ClassicalInformation_TAC where KTN like '{semester}_%' and Blocks > 0"
    query2 = f"select KTN from CadenceInformation_TAC   where KTN like '{semester}_%' and Nights > 0"
    query  = f"select distinct(KTN) from ({query1} union {query2}) t order by KTN"    
    ktns = dbc.query('proposals', query, getColumn='KTN')
    for i, ktn in enumerate(ktns):

        #todo: temp
        #if i> 5: continue

        #------------------------------------------------------------------------------
        # Get program data
        #------------------------------------------------------------------------------
        query = f"select KTN, ProgramType from ProgramInformation where KTN='{ktn}'"
        prog = dbc.query('proposals', query, getOne=True)
        if not prog:
            print ('WARNING: NO PROG INFO. SKIPPING. (possible ktn rename) ', ktn)
            continue
        type        = prog['ProgramType']
        typeCol     = type+"ID"


        #------------------------------------------------------------------------------
        # Get PI
        #------------------------------------------------------------------------------
        query =  f"select * from ContactInformation where "
        query += f" KTN='{ktn}' and Type='PI' and DelFlag=0"
        pi = dbc.query('proposals', query, getOne=True)
        if pi:
            prog['piLast']  = pi['LastName']
            prog['piFirst'] = pi['FirstName']


        #------------------------------------------------------------------------------
        # Get dates to avoid
        #------------------------------------------------------------------------------
        query = f"select AvoidStartDate, AvoidEndDate from DatesToAvoid where KTN='{ktn}' and DelFlag=0"
        prog['datesToAvoid'] = dbc.query('proposals', query)


        #------------------------------------------------------------------------------
        # Get priority targets
        #------------------------------------------------------------------------------
        query = f"select Target, RA, DECL, Epoch, Priority from TargetList where KTN='{ktn}' and DelFlag=0 order by Priority asc"
        prog['priorityTargets'] = dbc.query('proposals', query)


        #------------------------------------------------------------------------------
        # Get approved IDs for this proposal type
        #------------------------------------------------------------------------------
        query = f"select distinct({typeCol}) from {type}Information_TAC where KTN='{ktn}' order by {typeCol}"
        typeIds = dbc.query('proposals', query, getColumn=f'{typeCol}')
        prog['instruments'] = []
        for typeId in typeIds:

            progInstr = {}

            #------------------------------------------------------------------------------
            # Get requested info
            #------------------------------------------------------------------------------
            portion = ""
            query =  f"select * from {type}Information "
            query += f" where KTN='{ktn}' and ID={typeId} and DelFlag=0 "
            query += f" order by ID desc limit 1"
            infoReq = dbc.query('proposals', query, getOne=True)

            progInstr['moonPrefs']  = None
            progInstr['reqPortion'] = 0
            if infoReq:
                if   type == "Classical": 
                    progInstr['moonPrefs']  = infoReq['PAX']
                    progInstr['reqPortion'] = infoReq['Portion']
                elif type == "Cadence"  : 
                    progInstr['moonPrefs']  = None
                    progInstr['reqPortion'] = infoReq['Time']


            #------------------------------------------------------------------------------
            # Get approval info
            #------------------------------------------------------------------------------
            query  = f"select * from {type}Information_TAC "
            query += f" where KTN='{ktn}' and {typeCol}={typeId} "
            query += f" order by ID desc limit 1"
            infoTac = dbc.query('proposals', query, getOne=True)

            if   type == "Classical": 
                progInstr['appPortion'] = infoTac['Portion']
                progInstr['appTotal']   = infoTac['Portion'] * infoTac['Blocks']
            elif type == "Cadence"  : 
                progInstr['appPortion'] = infoTac['Time']
                progInstr['appTotal']   = infoTac['Time']    * infoTac['Nights']


            #------------------------------------------------------------------------------
            # Get instr and check instr in instrument list
            #------------------------------------------------------------------------------
            #NOTE: Approval step can change the instrument so we must get instr from *_TAC table
            progInstr['instr'] = infoTac['Instrument']
            found = 0
            for tel, instlist in telescopes_assoc.items():
                if progInstr['instr'] in instlist:
                    found = 1
                    break
            if not found:
                continue


            #------------------------------------------------------------------------------
            # Check thisTotal > 0
            #------------------------------------------------------------------------------
            #NOTE: We do this b/c of design of *_TAC tables which insert new rows each time with no DelFlag
            #So, the distinct KTN query will still query a KTN if it was approved but then zeroed out.
            if progInstr['appTotal'] <= 0: 
                continue


            #------------------------------------------------------------------------------
            # Get TAC scheduled cards (blocks) for the approved prog instr
            #------------------------------------------------------------------------------
            query =  f"select distinct CardNum from TACschedule "
            query += f" where KTN='{ktn}' and ProposalId='{infoTac[typeCol]}' and DelFlag=0 "
            query += f" order by CardNum asc"
            cardNums = dbc.query('proposals', query, getColumn='CardNum')

            progInstr['cards'] = []
            for num, cardNum in enumerate(cardNums):

                query =  f"select CardNum, Slot, Moon, Time, Date, Portion from TACschedule "
                query += f" where KTN='{ktn}' "
                query += f" and ProposalId='{infoTac[typeCol]}' "
                query += f" and CardNum={cardNum} "
                query += f" and DelFlag=0 order by ID desc limit 1"
                
                card = dbc.query('proposals', query, getOne=True)
                progInstr['cards'].append(card)
                # nights = card['Time']
                # period = card['Slot']


            #add full progInstr data to array
            #NOTE: skip if no scheduled cards
            if not progInstr['cards']: continue
            prog['instruments'].append(progInstr)

        #add full KTN data to programs dict
        #NOTE: skip if no instruments
        if not prog['instruments']: continue
        programs[ktn] = prog


    #close db conn
    dbc.close()

    return programs


def formDataToStandard(progData):
    '''
    Re-form data to what the TOAST program is expecting.
    '''

    programs = {}
    for ktn, prog in progData.items():

        programs[ktn] = {}
        programs[ktn]['ktn']  = ktn
        programs[ktn]['type'] = prog['ProgramType']

        #dates to avoid    
        #todo: sort dates?
        datesToAvoid = []
        for av in prog['datesToAvoid']:
            datesToAvoid += convertDateRangeToDatesArray(av['AvoidStartDate'], av['AvoidEndDate'])
        programs[ktn]['datesToAvoid'] = datesToAvoid

        # priority targets
        priorityTargets = []
        for pt in prog['priorityTargets']:
            priorityTargets.append(
            {
                'priority'  : pt['Priority'],
                'ra'        : pt['RA'],
                'dec'       : pt['DECL'],
                'epoch'     : pt['Epoch'],
                'target'    : pt['Target'],
            })
        programs[ktn]['priorityTargets'] = priorityTargets

        #instruments
        instruments = []
        for instr in prog['instruments']:
            progInstr = {
                'instr'     : instr['instr'],
                'moonPrefs' : instr['moonPrefs'].split(":") if instr['moonPrefs'] else [],
                'reqPortion': float(instr['reqPortion']),
                'appPortion': float(instr['appPortion']),
                'appTotal'  : float(instr['appTotal']),
            }
            blocks = []
            for card in instr['cards']:
                if card['Portion'] and card['Portion'].lower() == 'any': card['Portion'] = None
                blocks.append(
                {
                    'size'      : card['Time'],
                    'moonIndex' : int(card['Slot'][1:])-1,
                    'reqDate'   : card['Date'],
                    'reqPortion': card['Portion'],
                })
            progInstr['blocks'] = blocks
            instruments.append(progInstr)
        programs[ktn]['instruments'] = instruments



    return programs


def convertDateRangeToDatesArray(start, end):

    dates = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days+1)]
    dateStrs = [date.strftime("%Y-%m-%d") for date in dates]
    return dateStrs



def saveProgramDataToFile(programs, outfile, compact=False):

    if not compact:
        with open(outfile, 'w') as f:
            txt = json.dumps(programs, indent=4, default=jsonConverter)
            f.write(txt)

    #todo: https://stackoverflow.com/questions/13249415/how-to-implement-custom-indentation-when-pretty-printing-with-the-json-module
    else:
        txt = ''
        txt += "{\n"
        for pcount, (i, prog) in enumerate(programs.items()):
            txt += f'\t"{prog["ktn"]}": \n'
            txt += "\t{\n"
            txt += f'\t\t"ktn": "{prog["ktn"]}",\n'
            txt += f'\t\t"type": "{prog["type"]}",\n'
            txt += f'\t\t"datesToAvoid": {json.dumps(prog["datesToAvoid"], default=jsonConverter)},\n'

            if len(prog['priorityTargets']) == 0:
                txt += f'\t\t"priorityTargets": [],\n'
            else:
                txt += f'\t\t"priorityTargets":\n'
                txt += f'\t\t[\n'
                for ptcount, pt in enumerate(prog['priorityTargets']):
                    txt += f'\t\t\t{json.dumps(pt, default=jsonConverter)}'
                    txt += ",\n" if ptcount < len(prog['priorityTargets'])-1 else "\n"
                txt += f'\t\t],\n'

            txt += f'\t\t"instruments":\n'
            txt += f'\t\t[\n'
            for icount, instr in enumerate(prog['instruments']):
                txt += "\t\t\t{\n"
                txt += f'\t\t\t\t"instr": "{instr["instr"]}",\n'
                txt += f'\t\t\t\t"moonPrefs": {json.dumps(instr["moonPrefs"])},\n'
                txt += f'\t\t\t\t"reqPortion": {instr["reqPortion"]},\n'
                txt += f'\t\t\t\t"appPortion": {instr["appPortion"]},\n'
                txt += f'\t\t\t\t"appTotal": {instr["appTotal"]},\n'
                txt += f'\t\t\t\t"blocks":\n'
                txt += f'\t\t\t\t[\n'
                for bcount, block in enumerate(instr['blocks']):
                    txt += f'\t\t\t\t\t{json.dumps(block, default=jsonConverter)}'
                    txt += ",\n" if bcount < len(instr['blocks'])-1 else "\n"
                txt += f'\t\t\t\t]\n'
                txt += "\t\t\t}"
                txt += ",\n" if icount < len(prog['instruments'])-1 else "\n"
            txt += f'\t\t]\n'

            txt += "\t}"
            txt += ",\n" if pcount < len(programs)-1 else "\n"

        txt += "}\n"

        with open(outfile, 'w') as f:
            f.write(txt)



#------------------------------------------------------------------------------
# Command line
#------------------------------------------------------------------------------
if __name__ == "__main__":

    semester     = sys.argv[1]
    dbConfigFile = sys.argv[2]
    outdir       = sys.argv[3] 

    data = queryProgramData(semester, dbConfigFile)
    programs = formDataToStandard(data)

    outfile = f"{outdir}/{semester}-programs.json"
    saveProgramDataToFile(programs, outfile, True)
