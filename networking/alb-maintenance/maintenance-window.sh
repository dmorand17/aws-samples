#!/bin/bash
set -euo pipefail

[[ $# -ge 1 ]] || { echo "Usage: $0 <listener-arn>"; exit 1; }

aws elbv2 create-rule \
  --listener-arn $1 \
  --priority 1 \
  --conditions file://conditions.json \
  --actions file://actions.json
