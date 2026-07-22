#!/bin/bash
set -euo pipefail

STACK_NAME="sagemaker-canvas-events"
TEMPLATE_FILE="template.yaml"

echo "Deploying SageMaker Canvas Events CloudFormation stack..."

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file $TEMPLATE_FILE not found!" >&2
    exit 1
fi

aws cloudformation deploy \
    --stack-name "$STACK_NAME" \
    --template-file "$TEMPLATE_FILE" \
    --capabilities CAPABILITY_NAMED_IAM

echo "Stack deployed successfully!"
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "Deployment completed successfully!"
echo ""
echo "To monitor Lambda logs, run:"
echo "aws logs tail /aws/lambda/$STACK_NAME-event-handler --follow"
