import requests
import json
import os
import base64
import threading

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

lock = threading.Lock()


def handler(context, inputs):
    lock.acquire()
    vrofqdn = inputs['vrofqdn']
    username = inputs['username']
    password = inputs['password']
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
        if apioutput.status_code == 200:

            resourcedata = apioutput.json()
            currentname = inputs['inputProperties']['resourceNames']

            # Getting new Names
            resourceNames = []
            print(f'current name of the vms are \n{currentname}')
            for i in range(len(currentname)):
                resourceNames.append(resourcedata[i])

            print(f'New VM names are \n{resourceNames}')
            # Removing the allocated name from Main List
            for s in resourceNames:
                resourcedata.remove(s)

            with open(os.path.join('/tmp', 'VMwareCode.json'), 'w') as f:
                json.dump(resourcedata, f)

            fileFp = open('/tmp/VMwareCode.json', 'rb')
            fileInfoDict = {
                "file": fileFp

            }
            # Updating the ResourceElement
            resp = requests.post(url2, files=fileInfoDict, headers=vroheaders, verify=False)
            if resp.status_code == 200:
                print('Updating the resource element is completed ')
            else:
                print(resp.status_code)
            lock.release()
            return resourceNames

        else:
            print(apioutput.status_code)


    else:
        result = {
            'StatusCode': outp.status_code,
            'Reason': outp.reason
        }
        print(result)
    # Viewing the data inside the ResourceElement


