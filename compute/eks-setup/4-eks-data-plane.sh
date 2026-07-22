#!/bin/bash
set -euo pipefail

: "${CLUSTER_NAME:?CLUSTER_NAME must be set}"
: "${KEY_NAME:?KEY_NAME must be set}"
: "${VPC_ID:?VPC_ID must be set}"
: "${SUBNETS_IDS:?SUBNETS_IDS must be set}"

export CLUSTER_SG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text)

export ADDITIONAL_SG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --query 'cluster.resourcesVpcConfig.securityGroupIds[0]' --output text)

aws cloudformation deploy \
    --stack-name "$CLUSTER_NAME-data-plane" \
    --template-file eks-data-plane.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    ClusterControlPlaneSecurityGroup="$CLUSTER_SG" \
    ClusterName="$CLUSTER_NAME" \
    NodeGroupName="$CLUSTER_NAME-nodegroup" \
    KeyName="$KEY_NAME" \
    VpcId="$VPC_ID" \
    Subnets="$SUBNETS_IDS" \
    ProvidedSecurityGroup="$ADDITIONAL_SG"
