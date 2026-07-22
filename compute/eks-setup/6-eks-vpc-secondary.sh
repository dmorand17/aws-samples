#!/bin/bash
set -euo pipefail

: "${CLUSTER_NAME:?CLUSTER_NAME must be set}"
: "${VPC_ID:?VPC_ID must be set}"

export NGW1=$(aws cloudformation describe-stacks --stack-name "$CLUSTER_NAME-vpc" --query 'Stacks[0].Outputs[?OutputKey==`NatGateway1`].OutputValue' --output text)

export NGW2=$(aws cloudformation describe-stacks --stack-name "$CLUSTER_NAME-vpc" --query 'Stacks[0].Outputs[?OutputKey==`NatGateway2`].OutputValue' --output text)

export NGW3=$(aws cloudformation describe-stacks --stack-name "$CLUSTER_NAME-vpc" --query 'Stacks[0].Outputs[?OutputKey==`NatGateway3`].OutputValue' --output text)

aws cloudformation deploy \
    --stack-name "$CLUSTER_NAME-vpc-secondary" \
    --template-file eks-vpc-secondary.yaml \
    --parameter-overrides \
    EnvironmentName="$CLUSTER_NAME" \
    VpcId="$VPC_ID" \
    NatGateway1="$NGW1" \
    NatGateway2="$NGW2" \
    NatGateway3="$NGW3"
