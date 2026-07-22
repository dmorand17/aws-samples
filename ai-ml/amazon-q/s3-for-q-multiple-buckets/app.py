#!/usr/bin/env python3
import logging
import os
from pathlib import Path

import aws_cdk as cdk
import yaml
from yaml.loader import SafeLoader

from infra.q_s3_access_stack import QS3AccessStack


def configure_logging(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % log_level)
    logging.basicConfig(level=numeric_level)


with open(os.path.join(Path(__file__).parent, "config.yml"), "r") as yaml_file:
    stack_config = yaml.load(yaml_file, Loader=SafeLoader)

log_level = stack_config.get("LogLevel", logging.INFO)
configure_logging(log_level)

# Add logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# set logger to use date and time in the output

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Starting CDK Stack")

app = cdk.App()
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
)

vpc_stack = QS3AccessStack(
    scope=app,
    construct_id="q-s3-access",
    env=env,
    config=stack_config,
)

# Tags are applied to all tagable resources in the stack
tags = app.node.try_get_context("tags")
if tags:
    for key, value in tags.items():
        cdk.Tags.of(vpc_stack).add(key=key, value=value)

# cdk.Tags.of(vpc_stack).add("ProjectName", config["ProjectName"])
cdk.Tags.of(vpc_stack).add("App", "QS3Access")

app.synth()
