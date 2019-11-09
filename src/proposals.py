import os
import sys
import yaml
import json
import pandas
import db_conn


#todo: Load this from config file
telescopes_assoc = { 
    "1": ["LRIS-ADC","LRISp-ADC","HIRESr","HIRESb","OSIRIS-NGS","OSIRIS-LGS","MOSFIRE"], 
    "2": ["DEIMOS","ESI","ESI-ifu","KCWI","NIRSPEC","NIRSPAO-NGS","NIRSPAO-LGS","NIRC2-NGS", "NIRC2-NGS+NIRSPEC", "NIRC2-NGS+NIRSPAO", "NIRC2-LGS", "NIRC2-LGS+NIRSPEC", "NIRC2-LGS+NIRSPAO", "NIRES"]
    } 


def queryProgramBlocks(semester, tel=None):

    dbc = db_conn.db_conn('config_db.live.yaml')

    #------------------------------------------------------------------------------
    # Get approved programs (classical and cadence)
    #------------------------------------------------------------------------------
    query1 = f"select KTN from ClassicalInformation_TAC where KTN like '{semester}_%' and Blocks > 0"
    query2 = f"select KTN from CadenceInformation_TAC   where KTN like '{semester}_%' and Nights > 0"
    query  = f"select distinct(KTN) from ({query1} union {query2}) t order by KTN"
    ktns = dbc.query('proposals', query, getColumn='KTN')
    for ktn in ktns:

        #------------------------------------------------------------------------------
        # Get program data
        #------------------------------------------------------------------------------
        query = f"select ProgramType, AllocInst, SpecialRequests from ProgramInformation where KTN='{ktn}'"
        program = dbc.query('proposals', query, getOne=True)

        institution = program['AllocInst']
        type        = program['ProgramType']
        special     = program['SpecialRequests'].replace("\r\n", ' ')
        typeCol     = type+"ID"

        #------------------------------------------------------------------------------
        # Get date to avoid
        #------------------------------------------------------------------------------
        query = f"select * from DatesToAvoid where KTN='{ktn}' and DelFlag=0"
        avoidDates = dbc.query('proposals', query)
        avoidDatesStr = ''
        for av in avoidDates:
            avoidDatesStr += f"{av['AvoidStartDate']} to {av['AvoidEndDate']} "


        #todo: get targets
        #tooo: get moon prefs


        #------------------------------------------------------------------------------
        # Get approved IDs for this proposal type
        #------------------------------------------------------------------------------
        query = f"select distinct({typeCol}) from {type}Information_TAC where KTN='{ktn}' order by {typeCol}"
        typeIds = dbc.query('proposals', query, getColumn=f'{typeCol}')
        for typeId in typeIds:

            #------------------------------------------------------------------------------
            # Get requested info
            #------------------------------------------------------------------------------
            # TODO: Should we be getting Portion/Time from _TAC table b/c when approved they can change this??
            portion = ""
            query =  f"select * from {type}Information "
            query += f" where KTN='{ktn}' and ID={typeId} and DelFlag=0 "
            query += f" order by ID desc limit 1"
            infoReq = dbc.query('proposals', query, getOne=True)
            if infoReq:
                if   type == "Classical": portion = infoReq['Portion']
                elif type == "Cadence"  : portion = infoReq['Time']

            #------------------------------------------------------------------------------
            # Get approval info
            #------------------------------------------------------------------------------
            query  = f"select * from {type}Information_TAC "
            query += f" where KTN='{ktn}' and {typeCol}={typeId} "
            query += f" order by ID desc limit 1"
            infoTac = dbc.query('proposals', query, getOne=True)

            approvedPortion = ''
            if   type == "Classical": approvedPortion = infoTac['Portion']
            elif type == "Cadence"  : approvedPortion = infoTac['Time']

            thisTotal = 0
            if   type == "Classical": thisTotal = infoTac['Portion'] * infoTac['Blocks']
            elif type == "Cadence"  : thisTotal = infoTac['Time']    * infoTac['Nights']

            sem, progId = infoTac['KTN'].split("_")


            #------------------------------------------------------------------------------
            # Check thisTotal > 0
            #------------------------------------------------------------------------------
            #NOTE: We do this b/c of design of *_TAC tables which insert new rows each time with no DelFlag
            #So, the distinct KTN query will still query a KTN if it was approved but then zeroed out.
            if thisTotal <= 0: continue


            #------------------------------------------------------------------------------
            # Check instr is in telescope instrument list if telescope was defined
            #------------------------------------------------------------------------------
            #NOTE: Approval step can change the instrument so we must get instr from *_TAC table
            if tel:
                instr = infoTac['Instrument']
                if instr not in telescopes_assoc[tel]:
                    continue;


            #------------------------------------------------------------------------------
            # Get PI
            #------------------------------------------------------------------------------
            pi = '?'
            query =  f"select * from ContactInformation where "
            query += f" KTN='{ktn}' and Type='PI' and DelFlag=0"
            pi = dbc.query('proposals', query, getOne=True)
            if pi:
                piLast  = pi['LastName']
                piFirst = pi['FirstName']

            #----------------------------------------------
            # Get TAC scheduled cards (blocks)
            #----------------------------------------------
            query =  f"select distinct CardNum from TACschedule "
            query += f" where KTN='{ktn}' and ProposalId='{infoTac[typeCol]}' and DelFlag=0 "
            query += f" order by CardNum asc"
            cardNums = dbc.query('proposals', query, getColumn='CardNum')

            for num, cardNum in enumerate(cardNums):

                query =  f"select * from TACschedule "
                query += f" where KTN='{ktn}' "
                query += f" and ProposalId='{infoTac[typeCol]}' "
                query += f" and CardNum={cardNum} "
                query += f" and DelFlag=0 order by ID desc limit 1"
                
                card = dbc.query('proposals', query, getOne=True)
                nights = card['Time']
                period = card['Slot']
                line = ''
                line += f"{piLast}\t{piFirst}\t{instr}\t{institution}\t{progId}\t{cardNum}\t{nights}\t{portion}\t{period}"
                if (num == 0):
                    line += f"\t{thisTotal}"
                    #line += f"\t{avoidDatesStr}"
                    line += f"\t{card['Date']}"
                    line += f"\t{card['Portion']}"
                    #line += f"\t{infoTac['Notes']}"
                    #line += f"\t{special}"
                else:
                    line += f"\t\t"
                    line += f"\t{card['Date']}"
                    line += f"\t{card['Portion']}"
                print (line)



if __name__ == "__main__":

    queryProgramBlocks(sys.argv[1], sys.argv[2])