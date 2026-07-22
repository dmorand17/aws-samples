#!/bin/bash
set -euo pipefail

: "${CLUSTER_NAME:?CLUSTER_NAME must be set}"

aws cloudformation deploy \
    --stack-name "$CLUSTER_NAME-vpc" \
    --template-file eks-vpc.yaml \
    --parameter-overrides \
    EnvironmentName="$CLUSTER_NAME"
