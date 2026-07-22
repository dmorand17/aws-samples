#!/bin/bash
set -euo pipefail

: "${CLUSTER_NAME:?CLUSTER_NAME must be set}"
: "${CLUSTER_SG:?CLUSTER_SG must be set}"
: "${KEY_NAME:?KEY_NAME must be set}"
: "${VPC_ID:?VPC_ID must be set}"
: "${SUBNETS_IDS:?SUBNETS_IDS must be set}"
: "${ADDITIONAL_SG:?ADDITIONAL_SG must be set}"

export SECONDARY_SUBNETS_IDS=$(aws cloudformation describe-stacks --stack-name "$CLUSTER_NAME-vpc-secondary" --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnets`].OutputValue' --output text)

aws cloudformation deploy \
    --stack-name "$CLUSTER_NAME-data-plane-secondary" \
    --template-file eks-data-plane.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    ClusterControlPlaneSecurityGroup="$CLUSTER_SG" \
    ClusterName="$CLUSTER_NAME" \
    NodeGroupName="$CLUSTER_NAME-nodegroup-secondary" \
    KeyName="$KEY_NAME" \
    VpcId="$VPC_ID" \
    Subnets="$SECONDARY_SUBNETS_IDS" \
    ProvidedSecurityGroup="$ADDITIONAL_SG"
