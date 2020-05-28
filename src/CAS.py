#!/usr/bin/env python3
import requests, sys, re, time, pickle, cookie
from bs4 import BeautifulSoup

# This module is intend to login in the UMD Central Authentication System.
# Perform the DUO Security push, and then store the cookies for other module.

loginURL = "https://app.testudo.umd.edu/commonLogin/"
postURL = "https://shib.idm.umd.edu/shibboleth-idp/profile/cas/login?execution=e1s1"
authenURL = "https://shib.idm.umd.edu/shibboleth-idp/profile/cas/login?execution=e1s2"

def login(username:str, password:str, loginURL = loginURL):
    s = requests.Session()
    
    loginData = {   'j_username': username,
                    'j_password': password,
                    '_eventId_proceed': ''}

    r = s.get(url = loginURL)
    r = s.post(url = postURL, data = loginData)

    soup = BeautifulSoup(r.text, features = 'html.parser')

    if soup.find('p', {'class': "form-element form-error"}) != None:
        raise ValueError("The username or password you entered was incorrect or expired.")

    duoInfo = soup.findAll('iframe')[0]
    
    host = duoInfo['data-host']
    sig = duoInfo['data-sig-request']
    sid = sig[:100]
    referral = authenURL

    duoURL = "https://{0}/frame/web/v1/auth?tx={1}&parent={2}&v=2.6".format(host, sid, referral)
    duoData = { 'tx': sid,
                'parent': referral,
                'referer': referral,
                'java_version': "",
                'flash_version': "",
                'screen_resolution_width': "1920",
                'screen_resolution_height': "1080",
                'color_depth': "24",
                'is_cef_broswer': "false",
                'is_ipad_os': "false"}
    r = s.post(url = duoURL, data = duoData)
    match = re.search(r'^.*sid=(.*)$', r.url)
    sid = (match.group(1))

    print("A Duo Push has been sent to your primary device, please APPROVE the login request immediately!")

    duoPushData = { 'device': 'phone1',
                    'factor': 'Duo Push',
                    'dampen_choice': 'true',
                    'out_of_date': 'False',
                    'days_out_of_date': '0',
                    'days_to_block': 'None'}

    r = s.post(url = r.url, data = duoPushData)
    txid = r.json()['response']['txid']
    
    duoStatusURL = "https://{0}/frame/status?sid={1}&txid={2}".format(host, sid, txid)

    r = s.post(url = duoStatusURL)

    while r.json()['response']['status_code'] != 'allow':
        time.sleep(1)
        r = s.post(url = duoStatusURL)

    r = s.post("https://{0}/frame/status/{1}?sid={2}".format(host, txid, sid))

    auth = r.json()['response']['cookie'] + sig[100:]
    
    finalPayload = {'_eventId': "proceed",
                    'sig_response': auth}
                    
    r = s.post(url = authenURL, data = finalPayload)

    cookie.saveCookie(s)

    return True

def main():
    if len(sys.argv) == 3:
        login(sys.argv[1], sys.argv[2])
    else:
        raise ValueError("Not enough/Too much input!")

if __name__ == "__main__":
    main()