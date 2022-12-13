import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def handler(context, inputs):
    vrafqdn = inputs['vrafqdn']
    username = inputs['username']
    password = inputs['password']
    domain =inputs['domain']
    refreshtokenurl = f"https://{vrafqdn}/csp/gateway/am/api/login?access_token"
    iaasUrl = f"https://{vrafqdn}/iaas/api/login"
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    payload = {
        "username": username,
        "password": password,
        "domain": domain
        }
    apioutput = requests.post(refreshtokenurl, data=json.dumps(payload), verify=False, headers=headers)
    if apioutput.status_code == 200:
        refreshtoken = apioutput.json()['refresh_token']
        iaasPayload = f'{{"refreshToken": "{refreshtoken}"}}'
        iaasApiOutput = requests.post(iaasUrl, data=iaasPayload, headers=headers, verify=False).json()['token']
        bearerToken = "Bearer " + iaasApiOutput
        outputs = {}
        outputs['vratoken'] = bearerToken
        return outputs
    else:
        print(apioutput.status_code)
        print(apioutput.json())