#!/bin/bash

aws cloudformation deploy \
  --template-file keycloak-ec2.yml \
  --stack-name keycloak-ec2 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides file://$1 \
  #--disable-rollback
