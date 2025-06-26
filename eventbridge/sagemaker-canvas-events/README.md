# SageMaker Canvas Events - EventBridge Rule with Lambda Trigger

This CloudFormation template creates an EventBridge rule that monitors SageMaker Canvas events and other AWS events, triggering a Python Lambda function to log the events.

## Components

### EventBridge Rule

The rule uses a complex event pattern with `$or` logic that matches:

1. **SageMaker Canvas Events**:

   - Source: `aws.sagemaker`
   - Detail-type: `AWS API Call via CloudTrail`
   - Event source: `sagemaker.amazonaws.com`
   - Event names: `CreateApp`, `DeleteApp`

2. **Other Events** (excluding specific sources):
   - Detail-type: anything except `AWS API Call via CloudTrail`
   - Source: anything except `aws-config`, `aws-cloudtrail`, `aws-ssm`, `aws-tag`
   - Account: matches the current AWS account ID

### Lambda Function

- **Runtime**: Python 3.12 (latest)
- **Functionality**: Logs all received events to CloudWatch
- **Timeout**: 30 seconds
- **Memory**: 128 MB

## Deployment

### Prerequisites

- AWS CLI configured with appropriate permissions
- CloudFormation deployment permissions

### Deploy the Stack

```bash
# Deploy the CloudFormation stack
aws cloudformation create-stack \
  --stack-name sagemaker-canvas-events \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for deployment to complete
aws cloudformation wait stack-create-complete \
  --stack-name sagemaker-canvas-events
```

### Verify Deployment

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name sagemaker-canvas-events

# List stack outputs
aws cloudformation describe-stacks \
  --stack-name sagemaker-canvas-events \
  --query 'Stacks[0].Outputs'
```

## Testing

### Test the EventBridge Rule

1. **Create a SageMaker Canvas App** (if you have SageMaker Canvas access):

   - This will trigger the first condition in the event pattern

2. **Send a test event**:
   ```bash
   aws events put-events --entries '[
     {
       "Source": "aws.sagemaker",
       "DetailType": "AWS API Call via CloudTrail",
       "Detail": "{\"eventSource\":\"sagemaker.amazonaws.com\",\"eventName\":\"CreateApp\"}",
       "EventBusName": "default"
     }
   ]'
   ```

### Monitor Lambda Logs

```bash
# Get the Lambda function name
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name sagemaker-canvas-events \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
  --output text)

# View recent logs
aws logs tail /aws/lambda/$FUNCTION_NAME --follow
```

## Cleanup

```bash
# Delete the stack
aws cloudformation delete-stack --stack-name sagemaker-canvas-events

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name sagemaker-canvas-events
```

## Event Pattern Logic

The EventBridge rule uses the following logic:

```json
{
  "$or": [
    {
      "source": ["aws.sagemaker"],
      "detail-type": ["AWS API Call via CloudTrail"],
      "detail": {
        "eventSource": ["sagemaker.amazonaws.com"],
        "eventName": ["CreateApp", "DeleteApp"]
      }
    },
    {
      "detail-type": [
        {
          "anything-but": "AWS API Call via CloudTrail"
        }
      ],
      "source": [
        {
          "anything-but": ["aws-config", "aws-cloudtrail", "aws-ssm", "aws-tag"]
        }
      ],
      "account": ["CURRENT_AWS_ACCOUNT_ID"]
    }
  ]
}
```

This pattern will trigger the Lambda function for:

- SageMaker Canvas app creation/deletion events
- Any other AWS events except those from excluded sources (Config, CloudTrail, SSM, Tag)
- Events that are not CloudTrail API calls
