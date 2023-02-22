$m = Get-Module -ListAvailable -Name VMware.VimAutomation.Core
$impot = import-module -ModuleInfo $m
function handler($context, $inputs)
{
    #_______________________Debug and Verbose Mode Off____________________________________
    Set-PSDebug -Off
    $DebugPreference = "SilentlyContinue"
    $VerbosePreference = "SilentlyContinue"
    #_______________________Debug and Verbose Mode Off____________________________________
    #------------------------Getting endpoint and VMName ID --------------------------------------
    $endpointid = $inputs.endpointid
    $vmname = $inputs.vmname
    #------------------------Getting endpoint and VMName ID --------------------------------------
    $url = '/provisioning/uerp/resources/endpoints/' + $endpointid
    $endpoint_data = $context.request($url, 'GET', '')
    $data = $endpoint_data.content|ConvertFrom-Json
    $cred_raw = $context.request($data.authCredentialsLink, 'GET', '')
    $cred_data = $cred_raw.content|ConvertFrom-Json
    $viserver = $cred_data.customProperties.hostname
    $viusername = $cred_data.privateKeyId
    $vipsswd = $cred_data.privateKey
    $connection = connect-viserver -server $viserver -user $viusername -password $vipsswd -force
    write-host $connection
    try
    {
        $vm = Get-VM $vmname -ErrorAction Stop
        $ServiceInstance = Get-View -Id ServiceInstance
        $SessionManager = Get-View -Id $ServiceInstance.Content.SessionManager
        $vmrcURI = "vmrc://clone:" + ($SessionManager.AcquireCloneTicket()) + "@" + $global:DefaultVIServer.Name + "/?moid=" + $vm.ExtensionData.MoRef.Value
        write-host $vmrcURI
        $Outputs = @{'result'= $vmrcURI}
        return $Outputs
    }
    catch
    {
        Write-Error -Message "Entered VM  does not exist in  $global:DefaultVIServer"
    }

}
