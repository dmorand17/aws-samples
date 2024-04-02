aws cloudformation create-stack --stack-name -vpc \
      --template-body file://eks-vpc.yaml \
      --parameters \
ParameterKey=EnvironmentName,ParameterValue=$CLUSTER_NAME