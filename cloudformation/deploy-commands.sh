#!/bin/bash

TEMPLATE=vpc/vpc-default-security-group.yml
STACK_NAME=vpc-sample

aws cloudformation deploy \
--template-file $TEMPLATE \
--stack-name $STACK_NAME \
--capabilities CAPABILITY_NAMED_IAM \
--disable-rollback \
--parameter-overrides file://sandbox-deploy-parameters.json

aws cloudformation delete-stack \
--stack-name $STACK_NAME

aws cloudformation create-change-set \
--stack-name $STACK_NAME \
--change-set-name $STACK_NAME-changeset2 \
--template-body file://../cloudformation/openondemand.yml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters file://sandbox-deploy-parameters-rhel.json
