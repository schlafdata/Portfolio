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
# from error_log.configs import congigurations
import logging

# error logging configurations
logging.basicConfig(filename='error_log/app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

# get todays date and time in a file friendly format
now = '-'.join('_'.join(str(datetime.datetime.now()).split('.')[0].split()).split(':'))

sf = salesforce_login.bsna()
#initialize salesforce login

def updateSkills(territory, employee, skillsReplace, Except):

    try:
        territoryId = sf.query(f"SELECT Id from Territory__c WHERE Name = '{territory}'")['records'][0]['Id']
        # get new territory ID
    except IndexError:
        # likely manual error in file or this territory doesn't exist -- can be created in zip/terr
        logging.error(f'{territory} raised an error in skills_update file -- {now}')
        return []
        # or this territory doesn't exist?

    skillSets = sf.query_all(f"SELECT Id,Name,OwnerId,SkillSet_Object__c,Skill_Set__c,Territory__c \
                           FROM Territory_SkillSet_Mapping__c WHERE Territory__c = '{territoryId}'")
    skillIdDict = {x['Skill_Set__c'] : x['Id'] for x in skillSets['records']}
    # query salesforce for up to date data for the given territory
    skillSets = pd.DataFrame.from_records(skillSets['records'])
    # retrieve skillsets for territory

    allSkills = list(itertools.chain(*list(skillDict.values())))

    if skillsReplace == 10:
        # 14 is changing a manager, making them the owner of the territory
        try:
            resp = sf.Territory__c.update(territoryId, {'OwnerId':employee})
            return []
            #update territory in salesforce to new manger owner, there will be no locations to update end script
        except SalesforceMalformedRequest as e:
            logging.error(f'{e.content} -- there was an error assigning {employee} to territory {territoryId} --- {now}')

    def missingSkills(skillSets):
        # sometime skills are missing or deleted from territories, if they dont exist.. create
        try:
            if len(skillSets) == 0:
                newSkills = allSkills
            else:
                newSkills = list(set(allSkills) - set([x for x in skillSets['Skill_Set__c'].tolist() if pd.isnull(x) == False]))

            if len(newSkills) > 0:
                # if there are no skillsets in the territory, create all of the generic skillsets and assign them all to the new rep
                skillFrame = pd.DataFrame(newSkills)
                skillFrame.columns = ['Skill_Set__c']
                skillFrame['OwnerId'] = employee
                skillFrame['Territory__c'] = territoryId
                skillFrame['Status__c'] = 'Active'
                skillDict = skillFrame.to_dict('records')

                for skill in skillDict:
                    result = sf.Territory_SkillSet_Mapping__c.create(skill)

            if len(newSkills) == 0:
                pass
            else:
                skillSets = sf.query_all(f"SELECT Id,Name,OwnerId,SkillSet_Object__c,Skill_Set__c,Territory__c \
                            FROM Territory_SkillSet_Mapping__c WHERE Territory__c = '{territoryId}'")
                skillSets = pd.DataFrame.from_records(skillSets['records'])

            return skillSets
        except:
            logging.error(f'There was an error creating skills in territory {territory} --- {now}')
            return skillSets

    skillSets = missingSkills(skillSets)

    def getSkills(skillsReplace, Except):
        # take (str) values from excel sheet and convert to ints to map to territory skills for updating
        if skillsReplace.upper() == 'ALL':
            try:
                except_ = [int(x) for x in Except.split(',')]
                skillCodes = list(set([1,2,3,4,5,6,7,8,9]) - set(except_))
            except:
                skillCodes = [1,2,3,4,5,6,7,8,9]
        else:
            try:
                skillCodes = [int(x) for x in skillsReplace.split(',')]
                # skillCodes rep the index of which skills are being replaced from the excel spreadsheet
            except:
                skillCodes = [int(skillsReplace)]
        return skillCodes

    skillCodes = getSkills(skillsReplace, Except)
    # map skill codes to specific salesforce id to be updated
    updateIds = [skillIdDict[x] for x in list(itertools.chain(*[skillDict[x] for x in skillCodes]))]

    for Id in updateIds:
        try:
            result = sf.Territory_SkillSet_Mapping__c.update(Id, {'OwnerId':employee})
        except SalesforceMalformedRequest as e:
            logging.error(f'{e.content} -- There was an error updating skillset mapping for --  {territory} --- {now} --- {Id}')


    def getLocations(skillCodes):

        if any([x in [6,7,8,9] for x in skillCodes]):
            try:
                locUpdates = territory_alignment.realign(territory)
                return locUpdates
            except:
                logging.error(f'{e.content} -- There was an error retrieving locations for --  {territory} --- {now}')
                return []
        else:
            return []


    updates = getLocations(skillCodes)


    return updates
