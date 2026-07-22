#!/bin/bash
set -euo pipefail

[[ $# -ge 1 ]] || { echo "Usage: $0 <parameters-file>"; exit 1; }

aws cloudformation deploy \
  --template-file keycloak-ec2.yml \
  --stack-name keycloak-ec2 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides file://$1 \
  #--disable-rollback
