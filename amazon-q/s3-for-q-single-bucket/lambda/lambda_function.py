import json
import logging
import os

import boto3

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info("Loading function")

METADATA_PREFIX = "metadata"


# Create metadata when new object is uploaded to S3
def create_metadata(bucket_name, object_key):
    logger.info(f"Creating metadata for '{object_key}'")
    # Add CLOUDFRONT_DISTRIBUTION_DOMAIN to _source_uri
    metadata = {
        "Attributes": {
            "_source_uri": f'https://{os.environ["CLOUDFRONT_DISTRIBUTION_DOMAIN"]}/{object_key}',
        },
    }

    metadata_object_key = f"{METADATA_PREFIX}/{object_key}.metadata.json"
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=metadata_object_key,
            Body=json.dumps(metadata, indent=2),
        )
        logger.info(f"Uploaded metadata file: {metadata_object_key}")
    except Exception as e:
        logger.error(f"Error uploading metadata file: {e}")
        return 500

    return 200


# Delete metadata when object is deleted from S3
def delete_metadata(bucket_name, object_key):
    # Delete the metadata file
    metadata_object_key = f"{METADATA_PREFIX}/{object_key}.metadata.json"

    try:
        s3.delete_object(Bucket=bucket_name, Key=metadata_object_key)
        logger.info(f"Deleted metadata file: {metadata_object_key}")
    except Exception as e:
        logger.error(f"Error deleting metadata file: {e}")
        return 500

    return 200


def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event, indent=2)}")
    bucket_name = event["detail"]["bucket"]["name"]
    object_key = event["detail"]["object"]["key"]

    status_code = {
        "Object Created": create_metadata,
        "Object Deleted": delete_metadata,
    }.get(event["detail-type"], lambda x: (500))(bucket_name, object_key)

    return {"status_code": status_code}
