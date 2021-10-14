import requests
import json
import os
import base64

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def handler(context, inputs):
    # All the inputs saving to local variable
    prefix_name = inputs['prefix']
    startValue = inputs['startValue']
    endValue = inputs['endValue']
    username = inputs['username']
    password = inputs['password']
    fqdn = inputs['fqdn']

    # Making the Server Name list with provided Prefix , start and end value

    data = list(range(int(startValue), int(endValue)))
    prefix = []
    for i in data:
        i = prefix_name + str(i)
        prefix.append(i)

    print(prefix)
    # Creating the temp file to use in payload for VRO api

    with open(os.path.join('/tmp', 'VMwareCode.json'), 'w') as f:
        json.dump(prefix, f)

    url = f"https://{fqdn}/vco/api/resources"
    UserCredential = f"{username}:{password}"
    encode = base64.b64encode(UserCredential.encode())
    token = encode.decode("utf-8")
    vroheaders = {
        'accept': "application/xml",
        'authorization': "Basic " + token
    }

    fileFp = open('/tmp/VMwareCode.json', 'rb')
    fileInfoDict = {
        "file": fileFp
    }

    resp = requests.post(url, files=fileInfoDict, headers=vroheaders, verify=False)
    if resp.status_code == 202:
        print('VRO resource has been created with provided inputs by name VMwareCode.json')
        outputs = {}
        outputs['Results'] = 'VMwareCode.json is created'
        return outputs
    else:
        print(f'Please check the health of VRO server and provided credentials {resp.status_code}')
