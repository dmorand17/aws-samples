export VPC_ID=$(aws cloudformation describe-stacks --stack-name $CLUSTER_NAME-vpc --query 'Stacks[0].Outputs[?OutputKey==`VPC`].OutputValue' --output text)

export SUBNETS_IDS=$(aws cloudformation describe-stacks --stack-name $CLUSTER_NAME-vpc --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text)

aws cloudformation create-stack --stack-name $CLUSTER_NAME-control-plane \
    --template-body file://eks-control-plane.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters \
    ParameterKey=Name,ParameterValue=$CLUSTER_NAME \
    ParameterKey=Vpc,ParameterValue=$VPC_ID \    
'ParameterKey=Subnets,ParameterValue="'"$SUBNETS_IDS"'"'
