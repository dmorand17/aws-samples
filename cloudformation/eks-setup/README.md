# eks-setup

CloudFormation templates credited to -> https://aws.amazon.com/blogs/containers/optimize-ip-addresses-usage-by-pods-in-your-amazon-eks-cluster/

# Start Here

# Run these first
export CLUSTER_NAME=eks-cluster
export KEY_NAME=<an existing Keypair>

# Additional commands
# ===================================
# Check for nodes deploying
kubectl get nodes --watch


5
kubectl create -f deployment.yaml
kubectl get Pods --all-namespaces
kubectl get service -o wide


7
kubectl get nodes --watch
# Command to cordon all the nodes running on 10.0.0.0/16 CIDR block.
kubectl get nodes --no-headers=true | awk '/ip-10-0/{print $1}' | xargs kubectl cordon

# Command to drain all the nodes running on 10.0.0.0/16 CIDR block. You need to use –ignore-daemonsets flag in order to drain nodes with daemonsets and use –delete-local-data flag to overide and delete any pods that utilize an emptyDir volume.
kubectl get nodes --no-headers=true | awk '/ip-10-0/{print $1}' | xargs kubectl drain --force --ignore-daemonsets --delete-local-data

kubectl get service -o wide