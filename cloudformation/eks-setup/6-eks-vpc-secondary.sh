export NGW1=$(aws cloudformation describe-stacks --stack-name $CLUSTER_NAME-vpc --query 'Stacks[0].Outputs[?OutputKey==`NatGateway1`].OutputValue' --output text) 

export NGW2=$(aws cloudformation describe-stacks --stack-name $CLUSTER_NAME-vpc --query 'Stacks[0].Outputs[?OutputKey==`NatGateway2`].OutputValue' --output text) 

export NGW3=$(aws cloudformation describe-stacks --stack-name $CLUSTER_NAME-vpc --query 'Stacks[0].Outputs[?OutputKey==`NatGateway3`].OutputValue' --output text) 

aws cloudformation create-stack --stack-name $CLUSTER_NAME-vpc-secondary \
 --template-body file://eks-vpc-secondary.yaml \
 --parameters \ ParameterKey=EnvironmentName,ParameterValue=$CLUSTER_NAME \
 ParameterKey=VpcId,ParameterValue=$VPC_ID \
 ParameterKey=NatGateway1,ParameterValue=$NGW1 \
 ParameterKey=NatGateway2,ParameterValue=$NGW2 \
 ParameterKey=NatGateway3,ParameterValue=$NGW3