from collections import defaultdict

vertMarkets = defaultdict(list)
vertMarkets['0'] = ['Real Estate, Financial, Data Centers, and other Offices']
vertMarkets['1'] = ['K12 Schools']
vertMarkets['2'] = ['State Government','Local Government']
vertMarkets['3'] = ['Real Estate, Financial, Data Centers, and other Offices','K12 Schools','State Government','Local Government']


locSkills = defaultdict(dict)
locSkills['a2S1V000000oMplUAE']  = 'Security_Banking_Skill'
locSkills['a2S1V000000oMpqUAE'] = 'Security_Education_Skill'
locSkills['a2S1V000000oMpgUAE'] = 'Security_SLG_Skill'
locSkills['a2S1V000000oMpvUAE'] = 'Security_TerritoryRep_Skill'


skillDict = defaultdict(list)

skillDict[1] = ['a2S1V000000oMj8UAE']
skillDict[2] = ['a2S1V000000oMj9UAE']
skillDict[3] = ['a2S1V000000oMjFUAU']
skillDict[4] = ['a2S1V000000oMjAUAU']
skillDict[5] = ['a2S1V000000oMjEUAU']
skillDict[6] = ['a2S1V000000oMplUAE','a2S1V000000oMjBUAU']
skillDict[7] = ['a2S1V000000oMpqUAE','a2S1V000000oMjDUAU']
skillDict[8] = ['a2S1V000000oMpgUAE','a2S1V000000oMjCUAU']
skillDict[9] = ['a2S1V000000oMpvUAE','a2S1V000000oMiwUAE']

acctTeam = {'TeamMemberRole':'Sales - Security',
            'AccountAccessLevel': 'Edit',
            'OpportunityAccessLevel':'Edit'}
