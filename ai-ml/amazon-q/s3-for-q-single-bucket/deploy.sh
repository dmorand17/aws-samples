#!/bin/bash

set -eou pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <bucket-name> <stack-name>"
  exit 1
fi

BUCKET_NAME=$1
STACK_NAME=${2:-enable-q-s3-access}
DEPLOYMENT_BUCKET=${STACK_NAME}-$(aws sts get-caller-identity --query Account --output text)

# Create the deployment bucket if it doesn't exist
if ! aws s3 ls ${DEPLOYMENT_BUCKET} 2>/dev/null; then
  echo "[i] Creating deployment bucket ${DEPLOYMENT_BUCKET}"
  aws s3 mb s3://${DEPLOYMENT_BUCKET}
fi  

echo "[i] Using deployment bucket '${DEPLOYMENT_BUCKET}'"
echo "[i] Using stack name '${STACK_NAME}'"
echo "[i] Using bucket name '${BUCKET_NAME}'"

echo "[i] Packaging..."
aws cloudformation package \
  --template-file ./template.yml \
  --s3-bucket ${DEPLOYMENT_BUCKET} \
  --output-template-file ./template.packaged.yml

echo "[i] Deploying..."
aws cloudformation deploy \
  --template-file ./template.packaged.yml \
  --stack-name ${STACK_NAME} \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    BucketName=${BUCKET_NAME} \

echo "[i] Done!"
