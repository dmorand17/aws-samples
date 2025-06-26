import json
import boto3
from botocore.config import Config

# Configuration
REGION_NAME = 'us-east-1'
MODEL_ID = 'arn:aws:bedrock:us-east-1:{account-id}:model-import-job/{job-id}'  # Replace with your model ARN

# Configure retry settings
config = Config(
    retries={
        'total_max_attempts': 10, 
        'mode': 'standard'
    }
)

# Test message
message = "What is the color of the sky?"

# Initialize Bedrock Runtime client
session = boto3.session.Session()
br_runtime = session.client(
    service_name='bedrock-runtime', 
    region_name=REGION_NAME, 
    config=config
)

# Invoke the model
try:
    invoke_response = br_runtime.invoke_model(
        modelId=MODEL_ID, 
        body=json.dumps({'prompt': message}), 
        accept="application/json", 
        contentType="application/json"
    )
    
    # Parse and print the response
    invoke_response["body"] = json.loads(invoke_response["body"].read().decode("utf-8"))
    print(json.dumps(invoke_response, indent=4))
except Exception as e:
    print(e)
    print(e.__repr__())

