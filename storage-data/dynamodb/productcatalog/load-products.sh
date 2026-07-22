#!/bin/bash

set -euo pipefail

if [ -z "$1" ]; then
  echo "Usage: $0 <payload>"
  exit 1
fi

PAYLOAD=${1:-products.json}

echo "[-] Writing $PAYLOAD to DynamoDB"

aws dynamodb batch-write-item \
  --request-items file://$PAYLOAD
