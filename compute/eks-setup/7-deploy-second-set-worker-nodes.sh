export SECONDARY_SUBNETS_IDS=$(aws cloudformation describe-stacks --stack-name $CLUSTER_NAME-vpc-secondary --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text)

aws cloudformation create-stack --stack-name $CLUSTER_NAME-data-plane-secondary \
--template-body file://eks-data-plane.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=ClusterControlPlaneSecurityGroup,ParameterValue=$CLUSTER_SG \
ParameterKey=ClusterName,ParameterValue=$CLUSTER_NAME \
ParameterKey=NodeGroupName,ParameterValue=$CLUSTER_NAME-nodegroup-secondary \
ParameterKey=KeyName,ParameterValue=$KEY_NAME \
ParameterKey=VpcId,ParameterValue=$VPC_ID \
'ParameterKey=Subnets,ParameterValue="'"$SECONDARY_SUBNETS_IDS"'"' \
ParameterKey=ProvidedSecurityGroup,ParameterValue=$ADDITIONAL_SG