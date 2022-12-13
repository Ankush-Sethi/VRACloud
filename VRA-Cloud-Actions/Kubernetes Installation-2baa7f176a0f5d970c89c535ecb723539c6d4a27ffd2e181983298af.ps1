$m = Get-Module -ListAvailable -Name VMware.VimAutomation.Core
$impot = import-module -ModuleInfo $m
function handler($context, $inputs) {
    #_______________________Debug and Verbose Mode Off____________________________________
    Set-PSDebug -Off
    $DebugPreference="SilentlyContinue"
    $VerbosePreference="SilentlyContinue"
    #_______________________Debug and Verbose Mode Off____________________________________
    
    #_______________________Get Secrets and Inputs____________________________________'
    $vc = $context.getSecret($inputs.vCenterIP)
    $username = $context.getSecret($inputs.vCenterUsername)
    $password = $context.getSecret($inputs.Password)
    $template_username = $context.getSecret($inputs.template_username)
    $template_password = $context.getSecret($inputs.template_password)
    #_______________________Get Secrets and Inputs____________________________________'
    
    $connection = Connect-VIServer -Server $vc -User $username -Password $password -Force
    $data = $inputs['deployment_details']
    foreach($item in $data){
        $asd += @($item|select @{n='VMNAME';E={$item.hostname}})
        
    }
    $k8masterip = $asd|?{$_.VMNAME -match "k8master"}
    $master_vm = Get-VM $k8masterip.VMNAME
 

    # '_________________________________________________________________________________________'
    if($inputs.customProperties.role -match "k8master"){
        $master_script = @'
    sudo apt-get update -y
    sudo apt-get install jq -y
    sudo apt install docker.io -y
    sudo systemctl enable docker
    sudo systemctl start  docker
    sudo ufw disable
    sudo swapoff -a
    sudo apt-get update && sudo apt-get install -y apt-transport-https
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    sudo bash -c 'echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list'
    sudo apt-get update && sudo apt-get install -y kubelet kubeadm kubectl
    sudo systemctl enable kubelet
    sudo systemctl start kubelet
    masterip=$(hostname -I | cut -d' ' -f1)
    sudo kubeadm init --apiserver-advertise-address=$masterip
    mkdir -p /root/.kube
    sudo cp -i /etc/kubernetes/admin.conf /root/.kube/config
    sudo chown $(id -u):$(id -g) /root/.kube/config
    wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
    kubectl apply -f kube-flannel.yml
'@
        $result =Invoke-VMScript -VM $master_vm -ScriptType bash -ScriptText $master_script -GuestUser $template_username -GuestPassword $template_password
        Write-Host $result.ScriptOutput
    }
    elseif($inputs.customProperties.role -match "k8worker"){
        $worker_vms = Get-VM $inputs.resourceNames
        Write-Host $worker_vms
        $worker_script = @'
    sudo apt-get update -y
    sudo apt-get install jq -y
    sudo apt install docker.io -y
    sudo systemctl enable docker
    sudo systemctl start  docker
    sudo ufw disable
    sudo swapoff -a
    sudo apt-get update && sudo apt-get install -y apt-transport-https
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    sudo bash -c 'echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list'
    sudo apt-get update && sudo apt-get install -y kubelet kubeadm kubectl
    sudo systemctl enable kubelet
    sudo systemctl start kubelet
'@
        $Cluster_join = @'
    CERT_HASH=$(openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null| openssl dgst -sha256 -hex | sed 's/^.* //')
    TOKEN=$(kubeadm token list -o json | jq -r '.token' | head -1)
    PORT=6443
    IP=$(kubectl get nodes -lnode-role.kubernetes.io/control-plane -o json | jq -r '.items[0].status.addresses[] | select(.type=="InternalIP") | .address')
    echo "sudo kubeadm join $IP:$PORT --token=$TOKEN --discovery-token-ca-cert-hash sha256:$CERT_HASH"
'@
        $result2 =Invoke-VMScript -VM $master_vm -ScriptType bash -ScriptText $Cluster_join -GuestUser root -GuestPassword VMware123!
        $hash = @{“k8join” = $result2.ScriptOutput}
        $worker_result = Invoke-VMScript -VM $worker_vms -ScriptType bash -ScriptText $worker_script -GuestUser root -GuestPassword VMware123!
        #'____________________________________Worker Node Result_____________________________________________________'
        Write-Host $worker_result.ScriptOutput
        #'____________________________________Worker Node Result_____________________________________________________'
        $worker_script2= $hash.k8join
        $worker_result2 = Invoke-VMScript -VM $worker_vms -ScriptType bash -ScriptText $worker_script2 -GuestUser root -GuestPassword VMware123!
        Write-Host $worker_result2.ScriptOutput
        # '____________________________________Worker Node Result_____________________________________________________'
    }
    
    
    
    
    
    
}
