# Create Bedrock Model Import job
import boto3
import json

bedrock = boto3.client(service_name='bedrock')

JOB_NAME = f"{model_name}-import-job"
IMPORTED_MODEL_NAME = f"{model_name}-bedrock"
ROLE = sagemaker.get_execution_role() # Replace with custom IAM role if not using Amazon SageMaker for development

# createModelImportJob API
create_job_response = bedrock.create_model_import_job(
    jobName=JOB_NAME,
    importedModelName=IMPORTED_MODEL_NAME,
    roleArn=ROLE,
    modelDataSource={
        "s3DataSource": {
            "s3Uri": s3_model_uri
        }
    },
)
job_arn = create_job_response.get("jobArn")
