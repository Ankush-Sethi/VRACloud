# $m = Get-Module -ListAvailable -Name VMware.VimAutomation.Core
# $impot = import-module -ModuleInfo $m
function handler($context, $inputs) {
    #_______________________Debug and Verbose Mode Off____________________________________
    Set-PSDebug -Off
    $DebugPreference="SilentlyContinue"
    $VerbosePreference="SilentlyContinue"
    #_______________________Debug and Verbose Mode Off____________________________________
    #_______________________Get Secrets and Inputs____________________________________'
    $vc = $inputs.vCentername
    $username = $inputs.vCenterusername
    $password = $inputs.Password
    $vdsname = $inputs.vDSName
    $vdsversion = $inputs.vdsversion
    $dc= $inputs.datacenter_name
    $mtu = $inputs.mtu
    #_______________________Get Secrets and Inputs____________________________________'
    $connection = Connect-VIServer -Server $vc -User $username -Password $password -Force
    $location=Get-Datacenter -Name $dc
    $vds= New-VDSwitch -Name $vdsname -Location $location -Mtu $mtu -Version $vdsversion
    $output = @{"vdsname"=$vds.name}
    return $output

}
