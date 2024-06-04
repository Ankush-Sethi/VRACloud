/*
 * Copyright (c) 2022 VMware, Inc. All Rights Reserved.
 */

const axios = require('axios');
const https = require('https');


/**
 * Soft-un-delete vRA Deployments. This is effectively performing the reverse operation of soft-deleting,
 * i.e. deleting the lease and day 2 policies, reseting the deployment expiration and powering on the deployment.
 * This action waits for any in-progress deployment requests to complete first before starting to
 * modify the deployment and its resoruces. This is required as there can't be two requests on the
 * deployment happening at the same time.
 *
 * @abx_type            abx
 * @abx_name            Soft Un-Delete
 * @abx_project         ref:name:Development
 * @abx_entrypoint      handler
 * @abx_input           {string} deploymentId
 * @abx_input           {constant} vraHostname
 * @abx_input           {encryptedConstant} vraApiKey
 * @abx_input           {string} minSoftDeleteOffset
 * @abx_dependencies    { "dependencies": { "axios": "^0.24.0", "tunnel": "^0.0.6" } }
 * @abx_configuration   { "const_azure-resource_group": "acoe-rg", "const_azure-storage_account": "vmwareacoe", "const_azure-system_managed_identity": false }
 * @abx_shared
 */
async function handler(context, inputs, cb) {
  try {
    const { deploymentId } = inputs;

    const vraClient = await getVraClient(context, inputs);

    // wait for the deployment to settle
    await assertDeploymentIsOperatable(vraClient, deploymentId);

    let isSoftDeletedDeployment = false;

    let existingLease = '';

    // clean lease policy
    const leasePolicy = await getExistingPolicy(vraClient, getLeasePolicyName(deploymentId));
    if (leasePolicy) {
      console.log('Capturing existing lease of deployment from description of Lease Policy');
      existingLease = leasePolicy.description || '';
      console.log(`Deleting policy: ${leasePolicy.name}...`);
      await vraClient.delete(`/policy/api/policies/${leasePolicy.id}`);
      isSoftDeletedDeployment = true;
    } else {
      console.log('No lease policy to clean up.');
    }

    // clean day2 policy
    const day2Policy = await getExistingPolicy(vraClient, getDay2PolicyName(deploymentId));
    if (day2Policy) {
      console.log(`Deleting policy: ${day2Policy.name}...`);
      await vraClient.delete(`/policy/api/policies/${day2Policy.id}`);
      isSoftDeletedDeployment = true;
    } else {
      console.log('No day 2 policy to clean up.');
    }

    if (!isSoftDeletedDeployment) {
      console.log('This is not a soft-deleted deployment. Bailing out...');
      return cb(null, {});
    }

    // use static sleep of 30s to allow policy to no longer be in effect
    console.log('Waiting for 30s before resetting the deployment expiration');
    await sleep(30000);

    const now = new Date();
    const minSoftDeleteOffset = parseInt(inputs.minSoftDeleteOffset);

    // Creating Date with offset , It will take Current date + offset value
    const minOffset = new Date(now.getFullYear(), now.getMonth(), now.getDate() + minSoftDeleteOffset);
    const currentExpiry = existingLease === '' ? null : new Date(existingLease);

    console.log(`Existing Lease is ${currentExpiry}`);
    console.log(`New Lease with Offset is ${minOffset}`);

    if (!currentExpiry) {
      // If existing lease is set to never expire , we return {}, then we directly assign never expire

      await resetDeploymentExpiration(vraClient, deploymentId, null);
      await powerOnDeployment(vraClient, deploymentId);
    } else if (currentExpiry < now) {
      // when existing lease Date is in past

      if (minSoftDeleteOffset >= 0) {
        const newLease = minOffset;
        // reset deployment expiration
        await resetDeploymentExpiration(vraClient, deploymentId, newLease);
        // power on the deployment
        await powerOnDeployment(vraClient, deploymentId);
      } else {
        // Since minoffset delete is in Negative and existing lease in past and deployment is already expired
        console.log(
          `Since Offset value is negative ${minSoftDeleteOffset} , Only Policies are clean and Deployment remain in current state`
        );
        return {};
      }
    }
    // when existing lease Date is in Future
    else if (currentExpiry > now) {
      // here existing_lease is in future so minoffset won't have affect , because we set the existing lease to deployment
      const newLease = currentExpiry;
      // reset deployment expiration
      await resetDeploymentExpiration(vraClient, deploymentId, newLease);
      // power on the deployment
      await powerOnDeployment(vraClient, deploymentId);
    }

    cb(null, {});
  } catch (err) {
    console.error(err);
    cb(err);
  }
}

/**
 * Make sure that there are no currently executing actions on a deployment.
 * This is needed to properly time and sequence deployment operations.
 * @param {AxiosInstance} vraClient
 * @param {string} deploymentId
 * @param {number} interval
 * @param {number} maxRetries
 * @returns {Promise<void>}
 */
async function assertDeploymentIsOperatable(vraClient, deploymentId, interval = 1000, maxRetries = 120) {
  console.log(`Asserting that deployment "${deploymentId}" has no in-progress actions for up to ${maxRetries} retries...`);

  const url = `/deployment/api/deployments/${deploymentId}/requests?inprogressRequests=true`;
  let deploymentRequests = await vraClient.get(url);

  let hasInProgressRequets = deploymentRequests.data.content.length > 0;
  let retry = 0;

  while (hasInProgressRequets && retry < maxRetries) {
    await sleep(interval);
    retry++;
    console.log(`Waiting for in-progress actions to complete (retry: ${retry})...`);
    deploymentRequests = await vraClient.get(url);
    console.log(`  -> Requets in progress: ${deploymentRequests.data.content.length}`);
    hasInProgressRequets = deploymentRequests.data.content.length > 0;
  }

  if (hasInProgressRequets) {
    throw new Error(`Timed out while waiting for in-progress requests to complete after ${retry} retries`);
  }

  console.log(`Deployment has no in-progress requests and can be safely operated on!`);
}

/**
 * Reset the deployment expiration.
 * @param {AxiosInstance} vraClient
 * @param {string} deploymentId
 * @param {Date} leaseDate (optional) new leased date
 * @returns {Promise<void>}
 */
async function resetDeploymentExpiration(vraClient, deploymentId, leaseDate) {
  console.log(`Resetting expiration of deployment "${deploymentId}"...`);
  console.log(`New lease date: ${leaseDate}`);
  let body;
  if (!leaseDate) {
    body = {
      actionId: 'Deployment.ChangeLease',
      inputs: {},
    };
  } else {
    body = {
      actionId: 'Deployment.ChangeLease',
      inputs: {
        'Lease Expiration Date': leaseDate.toISOString(),
      },
    };
  }

  // build and send expiration request
  console.log(body);
  const expireRequest = await vraClient.post(`/deployment/api/deployments/${deploymentId}/requests?apiVersion=2020-08-25`, body);

  // monitor expiration request progress
  const requestId = expireRequest.data.id;
  console.log(`  -> Request ID: ${requestId}`);
  await monitorRequestProgress(vraClient, requestId);
}

/**
 * Power on a deployment. This will power on all VMs part of the deployment.
 * @param {AxiosInstance} vraClient
 * @param {string} deploymentId
 * @returns {Promise<void>}
 */
async function powerOnDeployment(vraClient, deploymentId) {
  console.log(`Powering on deployment "${deploymentId}"...`);

  // Get availability of the power on action on the deployment
  const powerOnAction = await vraClient.get(`/deployment/api/deployments/${deploymentId}/actions/Deployment.PowerOn?apiVersion=2020-08-25`);

  if (!powerOnAction.data.valid) {
    console.log('-> Power on action is not available for this deployment. Skipping power on!');
    return;
  }

  // Build and send power on request
  const body = {
    actionId: powerOnAction.data.id,
    inputs: {},
  };
  const powerOnRequest = await vraClient.post(`/deployment/api/deployments/${deploymentId}/requests?apiVersion=2020-08-25`, body);

  // monitor power on request progress
  const requestId = powerOnRequest.data.id;
  console.log(`  -> Request ID: ${requestId}`);
  await monitorRequestProgress(vraClient, requestId);
}

/**
 * Monitor the request execution progress.
 * @param {AxiosInstance} vraClient
 * @param {string} requestId
 * @param {number} interval
 * @param {number} maxRetries
 * @returns {Promise<void>}
 */
async function monitorRequestProgress(vraClient, requestId, interval = 1000, maxRetries = 120) {
  // const PROGRESS_STATUSES = [
  //   'CREATED',
  //   'PENDING',
  //   'INITIALIZATION',
  //   'CHECKING_APPROVAL',
  //   'APPROVAL_PENDING',
  //   'USER_INTERACTION_PENDING',
  //   'INPROGRESS',
  //   'COMPLETION',
  // ];
  const FAILURE_STATUSES = ['APPROVAL_REJECTED', 'ABORTED', 'FAILED'];
  const SUCCESS_STATUSES = ['SUCCESSFUL'];

  console.log(`Monitoring progress of request "${requestId}" for up to ${maxRetries} retries...`);

  let requestCompleted = false;
  let retry = 0;
  let requestInfo;

  while (!requestCompleted && retry < maxRetries) {
    await sleep(interval);
    retry++;
    console.log(`Monitoring request progress (retry: ${retry})...`);
    requestInfo = await vraClient.get(`/deployment/api/requests/${requestId}`);
    console.log(`  -> ${requestInfo.data.status}`);
    requestCompleted = SUCCESS_STATUSES.includes(requestInfo.data.status) || FAILURE_STATUSES.includes(requestInfo.data.status);
  }

  if (!requestCompleted) {
    throw new Error(`Timed out while waiting for request to complete after ${retry} retries`);
  } else if (FAILURE_STATUSES.includes(requestInfo.data.status)) {
    throw new Error(`Error while running request: ${requestInfo.data.status}`);
  }

  console.log(`Request completed with status: ${requestInfo.data.status}`);
}

/**
 * Retrieve existing policy for deployment. The policy is uniquely identified by
 * the deployment id contained within its name.
 * As the /policy API is not accessible using context.request() method, a separate REST client
 * (axios-based) is provided to make the necessary calls.
 * @param {AxiosInstance} vraClient
 * @param {string} deploymentId
 * @returns {Promise<any>}
 */
async function getExistingPolicy(vraClient, policyName) {
  const params = new URLSearchParams({ search: policyName });
  const url = `/policy/api/policies?${params.toString()}`;
  const policies = await vraClient.get(url);
  return policies.data.content.find((policy) => policy.name === policyName);
}

/**
 * Generate a new lease policy name using the deployment id
 * @param {string} deploymentId
 * @returns {string} policy name
 */
function getLeasePolicyName(deploymentId) {
  return `soft-delete-lease-${deploymentId}`;
}

/**
 * Generate a new day2 policy name using the deployment id
 * @param {string} deploymentId
 * @returns {string} policy name
 */
function getDay2PolicyName(deploymentId) {
  return `soft-delete-day2-${deploymentId}`;
}

/**
 * Create a new authenticated vRA client
 * @param {InvocationContext} context
 * @param {any} inputs
 * @returns {Promise<AxiosInstance>} client
 */
async function getVraClient(context, inputs) {
  console.log('Creating a new vRA REST client...');

  let apiKey = context.getSecret(inputs.vraApiKey);

  // infer the vRA hostname
  let hostname;
  if (context.context) {
    // context.context is available in Azure
    const callbackUrl = new URL(context.context.bindingData['__system.inputs']['__callback.url']);
    hostname = callbackUrl.hostname;
  } else {
    // resort to action constants if the hostname cannot be inferred
    hostname = context.getSecret(inputs.vraHostname);
  }
  console.log(`Resolved vRA hostname: ${hostname}`);

  // client options
  const options = {
    baseURL: `https://${hostname}`,
  };

  const proxy = process.env.HTTP_PROXY || process.env.http_proxy || process.env.HTTPS_PROXY || process.env.https_proxy;
  if (proxy) {
    // setup proxy
    const proxyUrl = new URL(proxy);
    const baseURL = new URL(options.baseURL);
    const agentConfig = {
      rejectUnauthorized: false,
      proxy: {
        host: proxyUrl.hostname,
        port: proxyUrl.port,
      },
    };
    console.log(`Using proxy settings: ${JSON.stringify(agentConfig)}`);

    // setup tunnel
    const tunnel = require('tunnel');
    if (baseURL.protocol === 'https:') {
      options.httpsAgent = tunnel.httpsOverHttp(agentConfig);
    } else {
      options.httpAgent = tunnel.httpOverHttp(agentConfig);
    }
    // disable axios proxy as tunnel with do the work
    options.proxy = false;
  } else {
    // do not use proxy
    console.log('Not using proxy');
    options.httpsAgent = new https.Agent({ rejectUnauthorized: false });
  }

  // create the client instance
  const client = axios.create(options);

  // add interceptor for error formatting
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.isAxiosError && error.response) {
        const errorMessage = `${error.response.request.method} ${error.response.request.path} -> ${error.response.status} ${
          error.response.statusText
        }: ${JSON.stringify(error.response.data)}`;
        throw new Error(errorMessage);
      } else {
        throw error;
      }
    }
  );

  // get access token and store it in a default authorization header of the client instance
  const accessResponse = await client.post('/iaas/api/login', { refreshToken: apiKey });
  client.defaults.headers.common['Authorization'] = `Bearer ${accessResponse.data.token}`;

  console.log(`Successfully authenticated a vRA client`);

  return client;
}

/**
 * Perform async sleep
 * @param {number} time
 * @returns {Promise<void>} a promise that resolves after <time> ms.
 */
async function sleep(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

exports.handler = handler;