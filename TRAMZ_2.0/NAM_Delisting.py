import salesforce_login
import pandas as pd
from common_functions import batches
import itertools
import territory_alignment
import warnings
warnings.filterwarnings('ignore')
import logging
import time

# error logging configurations
logging.basicConfig(filename='error_log/app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

sf = salesforce_login.bsna()
#initialize salesforce login

def getLocations(ntlNum, managerId, nameList):

    # find all locs related to a given national acct # or list, or to manager Id and account username_e3
    nameQuery = batches.likeBatch('Associated_Location__r.Location_Name_Security__c', nameList, 10000)

    if len(ntlNum) == 1:
        ntlNumQuery = f"('{ntlNum[0]}')"
    else:
        ntlNumQuery = tuple(ntlNum)

    locations = sf.query_all(f"SELECT ERP_SFDC_Account__c ,Account__c, Associated_Location__r.Postal_Code__c,Associated_Location__c, Id, Security_Business_ID__c,\
                                      Associated_Location__r.Location_Name_Security__c, Associated_Location__r.Security_Owner__c,Security_National_Account_Num__c\
                                      FROM Associated_ERP_Account__c \
                                      WHERE \
                                      (Security_National_Account_Num__c IN {ntlNumQuery}) OR \
                                      ((Associated_Location__r.Security_Owner__c = '{managerId}') AND ({nameQuery[0]}))")

    locFrame = pd.DataFrame.from_records(locations['records'])
    locFrame = pd.concat([locFrame.drop(['Associated_Location__r'], axis=1), locFrame['Associated_Location__r'].apply(pd.Series)], axis=1)

    def accountTeamQuery(df):

        accountIds = df['Account__c'].unique().tolist()
        accountQuery = batches.inBatch(accountIds, 10000)

        accountTeam = []
        for query in accountQuery:
                resp = sf.query_all(f"SELECT Id FROM AccountTeamMember WHERE (Account.Id IN {tuple(query)}) AND UserId = '{managerId}'")
                ids = [x['Id'] for x in resp['records']]
                accountTeam.append(ids)

        return list(itertools.chain(*accountTeam))

    def findTerritories(df):

        zips = [zip for zip in list(set(df['Postal_Code__c'].map(lambda x : x if pd.isnull(x) else x.split('-')[0]).tolist())) if zip is not None]
        zipQuery = batches.inBatch(zips, 5000)

        allTerrs = []
        for query in zipQuery:
            resp = sf.query_all(f"SELECT Postal_Code__c, Territory__c FROM Postal_Code_Mapping__C \
                                  WHERE Postal_Code__c IN {tuple(query)} AND Territory__r.Object__c = 'Account Location;Lead'")
            frame = pd.DataFrame.from_records(resp['records'])
            allTerrs.append(frame)

        postalTerr = pd.concat(allTerrs)
        uniqueTerrs = postalTerr.Territory__c.unique().tolist()
        skillOwners = sf.query_all(f"SELECT Territory__c, OwnerId FROM Territory_SkillSet_Mapping__c WHERE (Territory__c IN {tuple(uniqueTerrs)}) AND (Skill_Set__c = 'a2S1V000000oMpvUAE')")
        ownerTerrDict = {x['Territory__c']:x['OwnerId'] for x in skillOwners['records']}
        postalTerr.Territory__c = postalTerr.Territory__c.map(ownerTerrDict)
        postalOwner = dict(zip(postalTerr.Postal_Code__c, postalTerr.Territory__c))

        return postalOwner

    postalOwner = findTerritories(locFrame)
    locFrame['zip_match'] = locFrame['Postal_Code__c'].map(lambda x : x if pd.isnull(x) else x.split('-')[0])
    locFrame['Territory_Rep'] = locFrame.zip_match.map(postalOwner)

    accountTeamIds = accountTeamQuery(locFrame)
    accountTeamIds = pd.DataFrame(accountTeamIds)

    def updates(locFrame):

            erpUpdates = locFrame[locFrame['Security_Business_ID__c'] == 'National Account']['ERP_SFDC_Account__c'].tolist()
            # list of erp ids to update to commercial
            for loc in erpUpdates:
                try:
                    resp = sf.ERP_Account__c.update(loc, {'Security_Business_ID__c':'Commercial'})
                    time.sleep(3)
                    print('----')
                except SalesforceMalformedRequest as e:
                    logging.error(f'{e.content} raised an error in NAM_Delisting file for erp_account {loc} -- {now}')


            accountTeamIds = accountTeamQuery(locFrame)

            for id in accountTeamIds:
                try:
                    resp = sf.AccountTeamMember.delete(id)
                except SalesforceMalformedRequest as e:
                    logging.error(f'{e.content} raised an error in NAM_Delisting file deleting team member {id} -- {now}')


            locFrame['zip_match'] = locFrame['Postal_Code__c'].map(lambda x : x if pd.isnull(x) else x.split('-')[0])
            locFrame['Territory_Rep'] = locFrame.zip_match.map(postalOwner)
            return

    perform_updates = updates(locFrame)

    return locFrame


    def findTerritories(df):

        zips = [zip for zip in list(set(df['Postal_Code__c'].map(lambda x : x if pd.isnull(x) else x.split('-')[0]).tolist())) if zip is not None]
        zipQuery = batches.inBatch(zips, 5000)

        allTerrs = []
        for query in zipQuery:
            resp = sf.query_all(f"SELECT Territory__r.Name, Territory__c FROM Postal_Code_Mapping__C \
                                  WHERE Postal_Code__c IN {tuple(query)} AND Territory__r.Object__c = 'Account Location;Lead'")
            territories = list(set([x['Territory__r']['Name'] for x in resp['records']]))
            allTerrs.append(territories)

        return list(itertools.chain(*allTerrs))

    territories = findTerritories(locFrame)


    def territoryUpdates(territories):
        updates = []
        for ter in territories:
            data = territory_alignment.realign(ter)
            updates.append(data)

        return list(itertools.chain(*updates))

    updates = territoryUpdates(territories)


    return updates
