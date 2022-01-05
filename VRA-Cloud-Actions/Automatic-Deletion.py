import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def handler(context, inputs):
    vraurl = context.getSecret(inputs['VRAURL'])
    token = context.getSecret(inputs['token'])
    id = inputs['deploymentId']
    api_version_url = f'{vraurl}/iaas/api/about'
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    output = requests.get(url=api_version_url, headers=headers, verify=False)
    if output.status_code == 200:
        latest_api_version = output.json()['latestApiVersion']
        apiversion = latest_api_version
    else:
        print(output.status_code)
    iaasUrl = f"{vraurl}/iaas/api/login?apiVersion={apiversion}"
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    refreshtoken = token
    iaasPayload = f'{{"refreshToken": "{refreshtoken}"}}'
    iaasApiOutput = requests.post(iaasUrl, data=iaasPayload, headers=headers, verify=False)
    if iaasApiOutput.status_code == 200:
        jsondata = iaasApiOutput.json()['token']
        bearerToken = "Bearer " + jsondata
        bearertoken = bearerToken
        url = f'{vraurl}/iaas/api/deployments/{id}?forceDelete=true&apiVersion={apiversion}'
        headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'authorization': bearertoken
        }
        apioutput = requests.delete(url,headers=headers,verify=False)
        if apioutput.status_code == 202:
            print(f'Deployment delete request has been handled for deployment id {id}')
        else:
            print(f'API out is {apioutput.status_code} and reason is {apioutput.json()}')
    else:
        print(iaasApiOutput)