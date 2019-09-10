import pandas as pd
from files.dictionaries import vertMarkets, locSkills
from common_functions import batches
import salesforce_login
import warnings
warnings.filterwarnings('ignore')
import datetime
from tqdm import tqdm
from simple_salesforce import SalesforceMalformedRequest
import time
import datetime

now = '-'.join('_'.join(str(datetime.datetime.now()).split('.')[0].split()).split(':'))


sf = salesforce_login.bsna()

def realign(territory):


    territoryId = sf.query(f"SELECT Id FROM Territory__c WHERE Name = '{territory}'")['records'][0]['Id']

    skillSets = sf.query_all(f"SELECT OwnerId,Skill_Set__c \
                               FROM Territory_SkillSet_Mapping__c WHERE Territory__r.Id = '{territoryId}' AND SkillSet_Object__c LIKE '%Account Location%'")

    skillDict = {locSkills[x['Skill_Set__c']]:x['OwnerId'] for x in skillSets['records']}


    zips = sf.query_all(f"SELECT Postal_Code__c FROM Postal_Code_Mapping__c WHERE Territory__c = '{territoryId}'")
    zips = [x['Postal_Code__c'] for x in zips['records']]
    zipQuery = batches.likeBatch('Postal_Code__c', zips, 5000)

    def getLocations(zipQuery):

        loc_frames = []

        for query in zipQuery:

            security_locations = sf.query_all(f"SELECT Associated_Location__r.Security_Owner__c,Associated_Location__r.Vertical_Market__c, \
                                                Associated_Location__r.Vertical_Sub_Market__c, Associated_Location__c,Security_Business_ID__c \
                                                FROM Associated_ERP_Account__c \
                                                WHERE ({query}) AND (Associated_Location__r.Security_Owner__c != Null)")
            security_locations = pd.DataFrame.from_records(security_locations['records'])
            loc_frames.append(security_locations)

        security_locations = pd.concat(loc_frames)

        return security_locations

    if len(zipQuery) == 0:
        return
    else:

        security_commercial = getLocations(zipQuery).groupby('Associated_Location__c').\
        filter(lambda x : all(x['Security_Business_ID__c'].str.contains('Commercial'))).drop_duplicates('Associated_Location__c')

        security_commercial = pd.concat([security_commercial.drop(['Associated_Location__r'], axis=1),\
        security_commercial['Associated_Location__r'].apply(pd.Series)], axis=1)

        def wrong_owner(locations):

            banking = locations[locations['Vertical_Market__c'].isin(vertMarkets[0])]
            banking.Security_Owner__c = skillDict['Security_Banking_Skill']

            education = locations[locations['Vertical_Market__c'].isin(vertMarkets[1])]
            education.Security_Owner__c = skillDict['Security_Education_Skill']

            slg = locations[locations['Vertical_Market__c'].isin(vertMarkets[2])]
            slg.Security_Owner__c = skillDict['Security_SLG_Skill']

            territory = locations[locations['Vertical_Market__c'].isin(vertMarkets[3])==False]
            territory.Security_Owner__c = skillDict['Security_TerritoryRep_Skill']

            wrong_owner = pd.concat([banking, education, slg, territory])[['Associated_Location__c','Security_Owner__c']]

            return wrong_owner

        updates = wrong_owner(security_commercial)
        updates = list(zip(updates['Associated_Location__c'], updates['Security_Owner__c']))

        return updates
