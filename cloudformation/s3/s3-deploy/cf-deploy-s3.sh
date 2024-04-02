#!/bin/bash

set -euo pipefail

#aws cloudformation describe-stacks --stack-name $MY_STACK_NAME 

aws cloudformation create-stack \
    --stack-name $MY_STACK_NAME \
    --template-body file://cf-deploy-s3.yaml \
    --parameters ParameterKey=BucketName,ParameterValue=$MY_S3_BUCKET_NAME
