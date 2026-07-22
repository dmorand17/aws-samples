import json
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info("Loading function")

"""
This function is to remove the first portion of the path to properly map tot he location in S3

example uri:
qs3-awsdocs-872771682304/well-architected/wellarchitected-serverless-applications-lens.pdf -> 
/well-architected/wellarchitected-serverless-applications-lens.pdf
"""


def handler(event, context):
    logging.info(f"Received event: {json.dumps(event, indent=2)}")
    request = event["Records"][0]["cf"]["request"]
    request["uri"] = re.sub(r"^\/[^/]*\/", "/", request["uri"])
    return request
