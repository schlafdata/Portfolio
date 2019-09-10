import pandas as pd
import os
import datetime
import zip_code_alignment
import skills_update
from tqdm import tqdm
from shutil import copyfile
import itertools
import glob

now = '-'.join('_'.join(str(datetime.datetime.now()).split('.')[0].split()).split(':'))

folder = r'C:\Users\jschlajo\OneDrive - Johnson Controls\TRAMZ 2.0'
filePaths = glob.glob(folder + '\*.csv')

def getData(filePaths):

    if len(filePaths) == 0:
        print('No Files. Exiting')
        quit()

    elif len(filePaths) == 1:
        skillAlign = pd.read_csv(filePaths[0], usecols = ['Territory','EmployeeAdd','SkillsReplace','Except']).dropna(subset = ['Territory'])
        zips = pd.read_csv(filePaths[0], usecols = ['Zip','Town'], dtype=str).dropna()

    else:
        skillAlign = pd.concat(pd.read_csv(file, usecols = ['Territory','EmployeeAdd','SkillsReplace','Except']) for file in filePaths).dropna(subset = ['Territory'])
        zips = pd.concat(pd.read_csv(file, usecols = ['Zip','Town'], dtype=str).dropna() for file in filePaths)

    return skillAlign, zips

updateData = getData(filePaths)

skillAlign = updateData[0]
zips = updateData[1]

def zipCodeAlign(zips):
    if len(zips) > 0:
        alignment = zip_code_alignment.zipAlign(zips)
        return alignment
    else:
        return

executeZips = zipCodeAlign(zips)

def skillSetAlign(skillAlign):

    all_locations = []
    for row in tqdm(skillAlign.values):
        town = row[0]
        employee = row[1]
        skillsReplace = row[2]
        except_ = row[3]

        try:
            locations = skills_update.updateSkills(town, employee, skillsReplace, except_)
            all_locations.append(locations)
        except:
            print(skillAlign)

    locations = list(itertools.chain(*all_locations))
    locations = pd.DataFrame(locations)

    return locations

locations = skillSetAlign(skillAlign)

def moveFiles(filePaths, locations, skillAlign, zips, now):

    locations.to_csv(f'update_files/queue/assoc_loc_owner_file_{now}.csv', index=False)
    # send location updates to the queue
    [os.remove(file) for file in filePaths]
    # remove file that has been completed

    # append updates made to a file for tracking purposes, searches / lookups etc.
    skillAlign['Date'] = now
    zips['Date'] = now
    with open('update_files/territory_alignments/completed/skillset_alignments_completed.csv', 'a') as file:
        skillAlign.to_csv(file, header=False, index=False)
    with open('update_files/territory_alignments/completed/zip_code_completed.csv', 'a') as file:
        zips.to_csv(file, header=False, index=False)

    return 'Completed!'

print(moveFiles(filePaths, locations, skillAlign, zips, now))
