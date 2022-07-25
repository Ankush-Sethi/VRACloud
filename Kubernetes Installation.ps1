$m = Get-Module -ListAvailable -Name VMware.VimAutomation.Core
$impot = import-module -ModuleInfo $m
function handler($context, $inputs) {
    $vc = $context.getSecret($inputs.vCenterIP)
    $username = $context.getSecret($inputs.vCenterUsername)
    $password = $context.getSecret($inputs.Password)
    $data = $inputs['deployment_details']
    $k8masterip = $data|?{$_.values -contains "k8master"}
    Set-PSDebug -Off
    $DebugPreference="SilentlyContinue"
    $VerbosePreference="SilentlyContinue"
    $connection = Connect-VIServer -Server $vc -User $username -Password $password -Force
    $vm = Get-VM -name $k8masterip.hostname
    $script = @'
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
    $result =Invoke-VMScript -VM $vm -ScriptType bash -ScriptText $script -GuestUser root -GuestPassword VMware123!
    Write-Host $result.ScriptOutput
    $script2 = @'
    CERT_HASH=$(openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null| openssl dgst -sha256 -hex | sed 's/^.* //')
    TOKEN=$(kubeadm token list -o json | jq -r '.token' | head -1)
    PORT=6443
    IP=$(kubectl get nodes -lnode-role.kubernetes.io/control-plane -o json | jq -r '.items[0].status.addresses[] | select(.type=="InternalIP") | .address')
    echo "sudo kubeadm join $IP:$PORT --token=$TOKEN --discovery-token-ca-cert-hash sha256:$CERT_HASH"
'@
    Write-Host '_________________________________________________________________________________________'
    $result2 =Invoke-VMScript -VM $vm -ScriptType bash -ScriptText $script2 -GuestUser root -GuestPassword VMware123!
    $hash = @{“k8join” = $result2.ScriptOutput}
    return $hash
    Write-Host '_________________________________________________________________________________________'
    
}
