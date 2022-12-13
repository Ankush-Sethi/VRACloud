# $m = Get-Module -ListAvailable -Name VMware.VimAutomation.Core
# $impot = import-module -ModuleInfo $m
function handler($context, $inputs) {
    #_______________________Debug and Verbose Mode Off____________________________________
    Set-PSDebug -Off
    $DebugPreference="SilentlyContinue"
    $VerbosePreference="SilentlyContinue"
    #_______________________Debug and Verbose Mode Off____________________________________
    #_______________________Get Secrets and Inputs____________________________________'
    $vc = $inputs.vc
    $username = $inputs.username
    $password = $inputs.password
    $vdsname = $inputs.vDSName
    #_______________________Get Secrets and Inputs____________________________________'
    $connection = Connect-VIServer -Server $vc -User $username -Password $password -Force
    $vdsname = Get-VDSwitch -Name $vdsname 
    write-host $vdsname
    $output = @{"vdsname"=$vdsname.name}
    return $output

}
