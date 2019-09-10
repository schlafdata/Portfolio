import salesforce_login
import pandas as pd
from files.dictionaries import acctTeam
from common_functions import batches

sf = salesforce_login.bsna()
#initialize salesforce login

def addTeam(ntlNum, ownerId):

    accounts = sf.query_all(f"SELECT  Account__c FROM Associated_ERP_Account__c \
                                      WHERE \
                                      Security_National_Account_Num__c IN {batches.basicQuery(ntlNum)}")
    accountIds = list(set([x['Account__c'] for x in accounts['records']]))

    responses = []
    for account in accountIds:
        for owner in ownerId:

            create  = {'UserId':owner, 'AccountId':account}
            createAcctTeam = {**create, **acctTeam}

            resp = sf.AccountTeamMember.create(createAcctTeam)
            responses.append(resp)

    return responses
