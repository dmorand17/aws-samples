# Create Bedrock Model Import job
import argparse
import boto3

REGION_NAME = 'us-east-1'


def main():
    parser = argparse.ArgumentParser(
        description="Create a Bedrock custom model import job."
    )
    parser.add_argument(
        "--model-name",
        required=True,
        help="Base name for the import job and imported model.",
    )
    parser.add_argument(
        "--s3-model-uri",
        required=True,
        help="S3 URI of the model data (e.g. s3://bucket/prefix/).",
    )
    parser.add_argument(
        "--role-arn",
        required=True,
        help="IAM role ARN that Bedrock assumes for the import job.",
    )
    args = parser.parse_args()

    bedrock = boto3.client(service_name='bedrock', region_name=REGION_NAME)

    job_name = f"{args.model_name}-import-job"
    imported_model_name = f"{args.model_name}-bedrock"

    # createModelImportJob API
    create_job_response = bedrock.create_model_import_job(
        jobName=job_name,
        importedModelName=imported_model_name,
        roleArn=args.role_arn,
        modelDataSource={
            "s3DataSource": {
                "s3Uri": args.s3_model_uri
            }
        },
    )
    job_arn = create_job_response.get("jobArn")
    print(job_arn)


if __name__ == "__main__":
    main()
