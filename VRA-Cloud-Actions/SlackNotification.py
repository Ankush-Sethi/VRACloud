import requests
import json


def handler(context, inputs):
    if inputs['eventType'] == 'CREATE_DEPLOYMENT' and inputs['requestInputs']['Notification'] == 'Slack':
        # Taking the value from secret into local Variable
        vraurl = context.getSecret(inputs['VRAURL'])
        token = context.getSecret(inputs['token'])
        slackwebhook = context.getSecret(inputs['slack_webhook'])
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

                    # Sending the data to notification to slack
                    payload = {
                        "username": "VMwareCodeBot",
                        "channel": f"#{channelname}",
                        "icon_emoji": ":ironman-7316:",
                        "color": "Blue",
                        "type": "home",
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": f"Triggered  {eventType.capitalize()} {deployment_name}  request is {deployment_status.capitalize()} :python3: :vrac: :vmware_logo:"
                                }
                            },
                            {
                                "type": "divider"
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Deployment Name:*\n{deployment_name}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Deployment Description:*\n{deployment_description}"
                                    }
                                ]
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Creation Date: *\n{created_at}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*CreatedBy:*\n{createdBy}"
                                    }
                                ]
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Deployment Owner:*\n{ownedBy}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Deployment Status:*\n{deployment_status}"
                                    }
                                ]
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Last Updated By :*\n{lastUpdatedBy}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Last Updated At:*\n{lastUpdatedAt}"
                                    }
                                ]

                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Project Name :*\n{projectname}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Deployment ID:*\n{deployment_id}"
                                    }
                                ]
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*Failure Message*\n{failuremessage}"
                                }
                            },
                            {
                                "type": "divider"
                            }
                        ]

                    }
                    slackheaders = {
                        'content-type': "application/json",
                        'accept': "application/json"
                    }

                    result = requests.post(url=slackwebhook, data=json.dumps(payload), headers=slackheaders)
                    if result.status_code == 200:
                        print('Please check the slack for notification')
                    else:
                        print(result.status_code)
                        print(result.json())



                else:
                    print(deployment_apioutput.status_code)



            else:
                print(iaasApiOutput)
        else:
            print(output.status_code)
            print(output.json())

    else:
        print(inputs['eventType'])
