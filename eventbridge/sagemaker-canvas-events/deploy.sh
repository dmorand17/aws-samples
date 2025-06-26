#!/bin/bash

# SageMaker Canvas Events - CloudFormation Deployment Script

set -e

STACK_NAME="sagemaker-canvas-events"
TEMPLATE_FILE="template.yaml"

echo "🚀 Deploying SageMaker Canvas Events CloudFormation stack..."

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Error: Template file $TEMPLATE_FILE not found!"
    exit 1
fi

# Check if stack already exists
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" >/dev/null 2>&1; then
    echo "📝 Stack $STACK_NAME already exists. Updating..."
    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --capabilities CAPABILITY_NAMED_IAM
    
    echo "⏳ Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME"
    echo "✅ Stack updated successfully!"
else
    echo "📝 Creating new stack $STACK_NAME..."
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --capabilities CAPABILITY_NAMED_IAM
    
    echo "⏳ Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME"
    echo "✅ Stack created successfully!"
fi

# Display stack outputs
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "To monitor Lambda logs, run:"
echo "aws logs tail /aws/lambda/$STACK_NAME-event-handler --follow" 
