import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def handler(context, inputs):
    vraurl = context.getSecret(inputs['VRAURL'])
    token = context.getSecret(inputs['token'])
    deploymentid = inputs['deploymentId']
    id = '4d0f75d5-8855-481b-a78d-2e5957fd8cc4'
    email = inputs['requestInputs']['email']
    role = inputs['requestInputs']['role']
    type = inputs['requestInputs']['type']
    api_version_url = f'{vraurl}/iaas/api/about'
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    output = requests.get(url=api_version_url, headers=headers, verify=False)
    if output.status_code == 200:
        latest_api_version = output.json()['latestApiVersion']
        apiversion = latest_api_version
        # Getting the Bearer token

        # Getting the bearer token
        iaasUrl = f"{vraurl}/iaas/api/login?apiVersion={apiversion}"
        refreshtoken = token
        iaasPayload = f'{{"refreshToken": "{refreshtoken}"}}'
        iaasApiOutput = requests.post(iaasUrl, data=iaasPayload, headers=headers, verify=False)
        if iaasApiOutput.status_code == 200:
            print('Authentication completed with VRA Cloud')
            jsondata = iaasApiOutput.json()['token']
            bearerToken = "Bearer " + jsondata
            bearertoken = bearerToken
            headers = {
                'accept': "application/json",
                'content-type': "application/json",
                'authorization': bearertoken
            }

            # adding the New User to Project
            url = f'{vraurl}/project-service/api/projects/{id}/principals'
            payload_schema = {
                "modify": [
                    {
                        "email": "",
                        "type": "",
                        "role": ""
                    }
                ],
                "remove": [
                    {
                        "email": "",
                        "type": ""
                    }
                ]
            }
            user_inputs = {
                "email": email,
                "type": type,
                "role": role
            }
            payload_schema['modify'][0].update(user_inputs)
            apioutput2 = requests.patch(url, headers=headers, data=json.dumps(payload_schema), verify=False)
            if apioutput2.status_code == 200:
                # Changing the owner
                print(f'User {email} has been added to Project')
                url2 = f'{vraurl}/deployment/api/deployments/{deploymentid}/requests'
                data = {
                    "actionId": "Deployment.ChangeOwner",
                    "inputs": {
                        'New Owner': email
                    }
                }
                apioutput3 = requests.post(url2, headers=headers, data=json.dumps(data), verify=False)
                print(apioutput3)
            else:
                print(apioutput2)
                print(apioutput2.json())
        else:
            print(iaasApiOutput.status_code)
            print(iaasApiOutput.json())
    else:
        print(output.status_code)
        print(output.json())