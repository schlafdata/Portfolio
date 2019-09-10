import warnings
warnings.filterwarnings('ignore')
import salesforce_login
from simple_salesforce import SalesforceMalformedRequest
import pandas as pd
from common_functions import batches
import itertools
import territory_alignment
import datetime
from files.dictionaries import skillDict
from common_functions import batches
from files.dictionaries import skillDict
# from error_log.configs import congigurations
import logging

sf = salesforce_login.bsna()
#initialize salesforce login

logging.basicConfig(filename='error_log/app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
now = '-'.join('_'.join(str(datetime.datetime.now()).split('.')[0].split()).split(':'))

def zipAlign(zips):

    # zips = pd.read_csv(file, encoding= 'latin-1')
    zips['Zip'] = zips['Zip'].map(str)
    zips['Zip'] = zips['Zip'].map(lambda x : x.zfill(5))

    # get list of zip codes for updating from the file / format
    zipList = [str(x.strip()) for x in list(set(zips['Zip'].tolist()))]

    zipQuery = batches.inBatch(zipList, 5000)

    terrFrames = []
    for query in zipQuery:

        # verify all postal_code_mappings and territories retrieved are the object 'Account Location; Lead'
        # through query on the Territory__c object
        if len(query) == 1:
            query = f"('{query[0]}')"
        else:
            query = tuple(query)

        territories = sf.query_all(f"SELECT Territory__r.Name, Territory__c, Id, Postal_Code__c FROM Postal_Code_Mapping__c \
                                WHERE Postal_Code__c IN {query} \
                                AND Territory_Business_Unit__c != 'Fire' AND Territory__c != Null AND Territory__r.Object__c = 'Account Location;Lead'")
        territories = pd.DataFrame.from_records(territories['records'])
        territories = pd.concat([territories.drop(['Territory__r'], axis=1), territories['Territory__r'].apply(pd.Series)], axis=1)
        terrFrames.append(territories)

    zipTerritories = pd.concat(terrFrames)
    zipTerritories = zipTerritories.merge(zips, left_on='Postal_Code__c', right_on='Zip', how='left')

    # if current territory does not equal requested territory, then it needs to be updateIds

    terrPostalUpdates = zipTerritories[zipTerritories['Name'] != zipTerritories['Town']]
    uniqueTowns = terrPostalUpdates['Town'].unique().tolist()
    uniqueTowns = [x for x in uniqueTowns if pd.isnull(x) == False]

    def createTerritory(town):
        # if a territory doesnt exist it needs to be created - based on information from a similar
        # territory in its district
            # try:
            townQuery = town.split('-')[0]
            terrInfo = sf.query("SELECT Area_Code__c,Area__c,Business_Unit__c,Channel__c,Country__c,\
                                District__c,Local_Market_Code__c,Local_Market__c FROM Territory__c WHERE\
                                    Name LIKE '%{}%' AND Business_Unit__c = 'Security' \
                                    AND Object__c = 'Account Location;Lead' LIMIT 1".format(townQuery))
            createDict = {}
            for key, value in terrInfo['records'][0].items():
                if key == 'attributes':
                    continue
                else:
                    createDict[key] = value
            createDict['Name'] = town
            createDict['Global_Region__c'] = 'NA'

            newTerritory = sf.Territory__c.create(createDict)
            # create territory and retrieve territory id created
            newTerritory = newTerritory['id']
            # add skill sets to the newly created territory
            allSkills = itertools.chain(*list(skillDict.values()))
            createList = [{'Skill_Set__c':x,'Status__c':'Active','Territory__c':newTerritory} for x in allSkills]

            for skill in createList:
                result = sf.Territory_SkillSet_Mapping__c.create(skill)

            return newTerritory

    def updatePostalCode(uniqueTowns,terrPostalUpdates):

        terrDict = {}
        for town in uniqueTowns:
            try:
                terrId = sf.query_all(f"SELECT Id, Name FROM Territory__c WHERE Name = '{town}'")['records'][0]['Id']
                terrDict[town] = terrId
            except IndexError:
                try:
                    terrId = createTerritory(town)
                    terrDict[town] = terrId
                except:
                    logging.error(f'failed to create a new territroy for {town} -- {now}')

        test = []
        for row in terrPostalUpdates.values:
            try:
                resp = sf.Postal_Code_Mapping__c.update(row[2], {'Territory__c':terrDict[row[7]]})
            except SalesforceMalformedRequest as e:
                logging.error(f'failed to update postal code mapping for {row[2]} -- {row[7]} -- {now}')
            except:
                logging.error(f'{town} didnt exist as key in zip_alignment file -- {now}')

    data = updatePostalCode(uniqueTowns,terrPostalUpdates)

    return data
