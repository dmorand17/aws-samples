#!/bin/bash
set -euo pipefail

: "${CLUSTER_NAME:?CLUSTER_NAME must be set}"

export VPC_ID=$(aws cloudformation describe-stacks --stack-name "$CLUSTER_NAME-vpc" --query 'Stacks[0].Outputs[?OutputKey==`VPC`].OutputValue' --output text)

export SUBNETS_IDS=$(aws cloudformation describe-stacks --stack-name "$CLUSTER_NAME-vpc" --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text)

aws cloudformation deploy \
    --stack-name "$CLUSTER_NAME-control-plane" \
    --template-file eks-control-plane.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    Name="$CLUSTER_NAME" \
    Vpc="$VPC_ID" \
    Subnets="$SUBNETS_IDS"
