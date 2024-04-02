export CLUSTER_SG=$(aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId')

export ADDITIONAL_SG=$(aws eks describe-cluster --name $CLUSTER_NAME --query 'cluster.resourcesVpcConfig.securityGroupIds[0]')

aws cloudformation create-stack --stack-name $CLUSTER_NAME-data-plane \
--template-body file://eks-data-plane.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=ClusterControlPlaneSecurityGroup,ParameterValue=$CLUSTER_SG \
ParameterKey=ClusterName,ParameterValue=$CLUSTER_NAME \
ParameterKey=NodeGroupName,ParameterValue=$CLUSTER_NAME-nodegroup \
ParameterKey=KeyName,ParameterValue=$KEY_NAME \
ParameterKey=VpcId,ParameterValue=$VPC_ID \
'ParameterKey=Subnets,ParameterValue="'"$SUBNETS_IDS"'"' \
ParameterKey=ProvidedSecurityGroup,ParameterValue=$ADDITIONAL_SG