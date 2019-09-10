from simple_salesforce import Salesforce
from simple_salesforce import SalesforceMalformedRequest

proxies = {
"http": "http://104.129.194.36:10319",
"https": "http://104.129.194.36:10319",
}

username_bsna = 'john.schlafly-ext@jci.com.bsna'
password_bsna = 'JoStifel05!'

username_e3 = 'john.schlafly-ext@jci.com.global'
password_e3 = 'JoStifel04!'

isSandbox = 0
token = ''
instance = 'https://login.salesforce.com'

sf_bsna = Salesforce(username = username_bsna,
                password = password_bsna,
                security_token = token,
                sandbox = isSandbox,
                proxies = proxies)

sf_e3 = Salesforce(username = username_e3,
                password = password_e3,
                security_token = token,
                sandbox = isSandbox,
                proxies = proxies)


def bsna():

    return Salesforce(username = username_bsna,
                    password = password_bsna,
                    security_token = token,
                    sandbox = isSandbox,
                    proxies = proxies)

def e3():

    return Salesforce(username = username_e3,
                    password = password_e3,
                    security_token = token,
                    sandbox = isSandbox,
                    proxies = proxies)
