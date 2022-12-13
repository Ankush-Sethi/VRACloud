import json
import requests
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def handler(context,inputs):
    Outputs = {}
    deploymentid = inputs['deploymentId']
    cloudurl =  context.getSecret(inputs['VRAURL'])
    url = cloudurl
    api_version_url = f'{url}/iaas/api/about'
    print(f'Deployment ID from EBS fetched: {deploymentid}')
    start = time.time()
    
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    output = requests.get(url=api_version_url, headers=headers, verify=False)
    if output.status_code == 200:
        latest_api_version = output.json()['latestApiVersion']
        apiversion = latest_api_version
        iaasUrl = f"{url}/iaas/api/login?apiVersion={apiversion}"
        print(iaasUrl)
        refreshtoken = context.getSecret(inputs['token'])
        iaasPayload = f'{{"refreshToken": "{refreshtoken}"}}'
        iaasApiOutput = requests.post(iaasUrl, data=iaasPayload, headers=headers, verify=False)
        if iaasApiOutput.status_code == 200:
            print('Authentication to CLoud instance Completed \n')
            jsondata = iaasApiOutput.json()['token']
            bearerToken = "Bearer " + jsondata
            bearertoken = bearerToken

            headers = {
                'accept': "application/json",
                'content-type': "application/json",
                'authorization': bearertoken
            }
            deployment_url = f'{cloudurl}/deployment/api/deployments/{deploymentid}' \
                             f'/resources?resourceTypes=Cloud.vSphere.Machine&apiVersion={apiversion}'
            print(deployment_url)
            deployment_output = requests.get(deployment_url, headers=headers, verify=False)
            if deployment_output.status_code == 200:
                print('Deploymnet details API response is success, starting the payload reading ....')
                data = deployment_output.json()['content']
                data_dict = {}
                data_list = []
                for i in data:
                    data_dict['id'] = i['id']
                    data_dict['name'] = i['name']
                    data_dict['VMIP'] = i['properties']['networks'][0]['address']
                    data_dict['resourceName'] = i['properties']['resourceName']
                    data_dict['EndPoint'] = i['properties']['accounts']
                    data_dict['zone'] = i['properties']['zone']
                    data_dict['region'] = i['properties']['region']
                    data_list.append(data_dict.copy())
                Outputs['deployment_details']= data_list
                end = time.time()
                timetaken = end - start
                print(f'Time taken to collect the data: {timetaken}')
                return Outputs
            else:
                print(f'Deployment API result is : {deployment_output.status_code}')
                if deployment_output.json():
                    print(deployment_output.json())
                    raise Exception("Check the API result")

        else:
            print(f'Authentication API result is: {iaasApiOutput.status_code}')
            if iaasApiOutput.json():
                return iaasApiOutput.json()
                raise Exception("Check the API result")
    else:
        print(output.status_code)