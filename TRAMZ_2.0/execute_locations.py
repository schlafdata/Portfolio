import warnings
warnings.filterwarnings('ignore')
import salesforce_login
from simple_salesforce import SalesforceMalformedRequest
from simple_salesforce import SalesforceResourceNotFound
import pandas as pd
from common_functions import batches
import itertools
import territory_alignment
import datetime
from files.dictionaries import skillDict
# from error_log.configs import congigurations
import logging
import glob
from tqdm import tqdm
import os
import time

# error logging configurations
logging.basicConfig(filename='error_log/app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

# get todays date and time in a file friendly format
now = '-'.join('_'.join(str(datetime.datetime.now()).split('.')[0].split()).split(':'))

sf = salesforce_login.bsna()
#initialize salesforce login

def simpleLocUpdate(file, resetCode):

    try:
        data = pd.read_csv(file)
    except:
        # the file is empty
        return
    success = []
    errors = []

    for x in tqdm(data.values):
        now = datetime.datetime.now()
        if (now.hour > 21) | (now.hour < 5):
            sleep = 0
        else:
            sleep = 1.5
        try:
            if resetCode == 0:
                add = sf.Associated_Location__c.update(x[0], {'Security_Owner__c':x[1]})
                updated = x[1], x[0]
                success.append(updated)
                time.sleep(1*sleep)
            else:
                remove = sf.Associated_Location__c.update(x[0], {'Security_Owner__c':'005f400000366Vv'})
                add = sf.Associated_Location__c.update(x[0], {'Security_Owner__c':x[1]})
                updated = x[1], x[0]
                success.append(updated)
                time.sleep(2*sleep)
        except SalesforceMalformedRequest as e:
            err = x[1], x[0], e.content
            errors.append(err)
        except SalesforceResourceNotFound:
            pass
        except:
            pass

    return success, errors

# check for new contents of the folder every loop. Always take the file on top and run until there
# are no files left to update
while glob.glob(r'C:\Users\jschlajo\Desktop\TRAMZ_2.0\update_files\queue\*.csv') != []:

    file = glob.glob(r'C:\Users\jschlajo\Desktop\TRAMZ_2.0\update_files\queue\*.csv')[0]
    if ('assoc_loc' in file) | ('SFDC' in file):
        result = simpleLocUpdate(file, 0)
        os.remove(file)
    elif 'reset' in file:
        result = simpleLocUpdate(file, 1)
        os.remove(file)
        pass
