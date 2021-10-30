import requests
import json


def handler(context, inputs):
    if inputs['eventType'] == 'CREATE_DEPLOYMENT' and inputs['requestInputs']['Notification'] == 'Teams':
        # Taking the value from secret into local Variable
        vraurl = context.getSecret(inputs['VRAURL'])
        token = context.getSecret(inputs['token'])
        Teams_Code_channel = context.getSecret(inputs['Teams_Code_channel'])
        VmwareCode_Demo = context.getSecret(inputs['VmwareCode-Demo'])
        deploymentid = inputs['deploymentId']
        eventType = inputs['eventType']
        channelname = inputs['requestInputs']['NotificationChanel']
        if inputs['status'] == 'FAILED':
            failuremessage = inputs['failureMessage']
        else:
            failuremessage = 'No Errors'
        # Taking the value from secret into local Variable

        # getting the latest version of API
        api_version_url = f'{vraurl}/iaas/api/about'
        headers = {
            'accept': "application/json",
            'content-type': "application/json"
        }
        output = requests.get(url=api_version_url, headers=headers, verify=False)
        # getting the latest version of API

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
                # Getting the deployment details.

                depurl = f'{vraurl}/deployment/api/deployments/{deploymentid}?apiVersion={apiversion}'
                headers = {
                    'accept': "application/json",
                    'content-type': "application/json",
                    'authorization': bearertoken
                }
                deployment_apioutput = requests.get(depurl, headers=headers, verify=False)
                if deployment_apioutput.status_code == 200:
                    jdata = deployment_apioutput.json()
                    deployment_name = jdata['name']
                    deployment_description = jdata['description']
                    deployment_id = jdata['id']
                    created_at = jdata['createdAt']
                    createdBy = jdata['createdBy']
                    ownedBy = jdata['ownedBy']
                    lastUpdatedAt = jdata['lastUpdatedAt']
                    lastUpdatedBy = jdata['lastUpdatedBy']
                    deployment_status = inputs['status']
                    projectname = inputs['projectName']

                    # Sending the data to notification to Teams
                    if channelname == 'code':
                        url = Teams_Code_channel
                    elif channelname == 'vmwarewcode-demo':
                        url = VmwareCode_Demo
                    headers = {
                        'content-type': "application/json",
                        'accept': "application/json"
                    }
                    payload = {
                        "@type": "MessageCard",
                        "themeColor": "0076D7",
                        "summary": "Create Deployments",
                        "sections": [{
                            "activityTitle": f"Task: {eventType} ",
                            "activitySubtitle": f"Project: {projectname}",
                            "facts": [{
                                "name": "Owner",
                                "value": f"{ownedBy}"
                            }, {
                                "name": "Deployment Name",
                                "value": f"{deployment_name}"
                            },
                                {
                                    "name": "Description",
                                    "value": f" {deployment_description}"
                                }, {
                                    "name": "Creation Date",
                                    "value": f"{created_at}"
                                }, {
                                    "name": "Last Updated at",
                                    "value": f"{lastUpdatedAt}"
                                }, {
                                    "name": "Last Updated By",
                                    "value": f"{lastUpdatedBy}"
                                }, {
                                    "name": "Created By",
                                    "value": f"{createdBy}"
                                }, {
                                    "name": "Deployment ID",
                                    "value": f"{deployment_id}"
                                },
                                {
                                    "name": "Status",
                                    "value": f"{deployment_status}"
                                }, {
                                    "name": "Failure Message",
                                    "value": f"{failuremessage}"
                                }],
                            "markdown": "true"
                        }]
                    }

                    teamsresult = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)
                    if teamsresult.status_code == 200:
                        print('Notification has been sent to teams channel')
                    else:
                        teamsresult.status_code
                else:
                    print(deployment_apioutput.status_code)
            else:
                print(iaasApiOutput)
        else:
            print(output.status_code)
            print(output.json())
    else:
        print(inputs['eventType'])
