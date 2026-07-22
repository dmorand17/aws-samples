#!/bin/bash

aws elbv2 create-rule \
  --listener-arn $1 \
  --priority 1 \
  --conditions file://conditions.json \
  --actions file://actions.json
