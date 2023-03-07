function handler($context, $inputs) {
    #_______________________Debug and Verbose Mode Off____________________________________
    Set-PSDebug -Off
    $DebugPreference="SilentlyContinue"
    $VerbosePreference="SilentlyContinue"
    #_______________________Debug and Verbose Mode Off____________________________________
    
    #_______________________Get Secrets and Inputs____________________________________'
    $vc = $context.getSecret($inputs.vc_155_name)
    $username = $context.getSecret($inputs.vC_155_username)
    $password = $context.getSecret($inputs.vc_155_password)
    $application_name = $inputs.customProperties.application
    $owner_name = $inputs.customProperties.owner
    $backup = $inputs.customProperties.backup
    $data = $inputs['deployment_details']
    #_______________________Get Secrets and Inputs____________________________________'
    
    $connection = Connect-VIServer -Server $vc -User $username -Password $password  -force
    $application_ca = Get-CustomAttribute -TargetType VirtualMachine -Name 'Application'
    $owner_ca = Get-CustomAttribute -TargetType VirtualMachine -Name 'owner'
    $backup_ca = Get-CustomAttribute -TargetType VirtualMachine -Name 'backup'
    foreach($item in $data){
        Write-Host "Setting Custom Attribute to Application :"  -NoNewline
        $result = get-vm $item.resourceName|Set-Annotation -CustomAttribute $application_ca -Value $application_name
        if ($result.value -match $application_name )
        {
        Write-Host "Done"    
        }
        Write-Host "Setting Custom Attribute to Owner :"  -NoNewline
        $result1 = get-vm $item.resourceName|Set-Annotation -CustomAttribute $owner_ca -Value $owner_name
        if($result1.value -match $owner_name){
            Write-Host "Done"
        }
        Write-Host "Setting CUstom Attribute to Backp: " -NoNewline
        $result3 = get-vm $item.resourceName|Set-Annotation -CustomAttribute $backup_ca -Value $backup
        if($result3.value -match $backup){
            Write-Host "Done"
        }
         
    }
    
    
    
    
    
}