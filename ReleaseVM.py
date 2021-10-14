import requests
import json
import os
import base64
import threading

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def handler(context, inputs):
    lock = threading.Lock()
    lock.acquire()
    vrofqdn = inputs['vrofqdn']
    username = inputs['username']
    password = inputs['password']
    prefix = inputs['prefix']
    # To search and grab the ID of resource ResourceElement

    url = f'https://{vrofqdn}:443/vco/api/catalog/System/ResourceElement?conditions=name~VMwareCode'
    UserCredential = f"{username}:{password}"
    encode = base64.b64encode(UserCredential.encode())
    token = encode.decode("utf-8")
    vroheaders = {
        'accept': "application/json",
        'authorization': "Basic " + token,
    }
    # Making get API call to search for ResourceElement
    outp = requests.get(url, headers=vroheaders, verify=False)
    if outp.status_code == 200:
        link = outp.json()['link']
        data = link[0]['attributes']
        for i in data:

            if 'id' in i.values():
                rid = (i['value'])
                print(f'ID of the ResourceElement is {rid}')

        url2 = f"https://{vrofqdn}:443/vco/api/resources/{rid}"
        apioutput = requests.get(url2, headers=vroheaders, verify=False)
    # Making get API call to search for ResourceElement
        if apioutput.status_code == 200:
            resourcedata = apioutput.json()
            print(f'Existing names in list are\n {resourcedata} ')
            oldname = inputs['inputProperties']['resourceNames']
            print(f'Releasing name of VM : {oldname}')
            for i in oldname:
                resourcedata.append(i)

            numlist = []
            for i in resourcedata:
                numlist.append(int(i.split(prefix)[1]))

            # remove duplicate
            data = list(set(numlist))
            data.sort()
            finallist = []
            for i in data:
                names = prefix + str(i)
                finallist.append(names)

            # updating the data with json and creating the temp file
            with open(os.path.join('/tmp', 'VMwareCode.json'), 'w') as f:
                json.dump(finallist, f)

            fileFp = open('/tmp/VMwareCode.json', 'rb')
            fileInfoDict = {
                "file": fileFp

            }
            # Updating the ResourceElement

            resp = requests.post(url2, files=fileInfoDict, headers=vroheaders, verify=False)
            if resp.status_code == 200:
                lock.release()
                print(finallist)
        else:
            print(apioutput.status_code)

    else:
        result = {
            'StatusCode': outp.status_code,
            'Reason': outp.reason
        }
        print(result)





