import logging
from typing import Any, Dict, cast

import aws_cdk as cdk
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as events_targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_s3 as s3
from aws_cdk import CfnOutput, Stack
# from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
from constructs import Construct

import infra.cdk_utils as cdk_utils

"""
  This CloudFormation template is used to create the following: - S3 bucket - CloudFront distribution (s3 bucket is origin) - Lambda Function (triggered for Create/Delete events on S3 bucket to manage Amazon Q metadata)
"""

logger = logging.getLogger(__name__)
logger.info("Starting CDK Stack")

class QS3AccessStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        assert len(construct_id) <= 16, "Stack name must have 16 characters or less."

        self.python_runtime = config["lambda"].get("python_runtime", "PYTHON_3_12")
        if self.python_runtime == "PYTHON_3_10":
            self._runtime = _lambda.Runtime.PYTHON_3_10
        elif self.python_runtime == "PYTHON_3_11":
            self._runtime = _lambda.Runtime.PYTHON_3_11
        elif self.python_runtime == "PYTHON_3_12":
            self._runtime = _lambda.Runtime.PYTHON_3_12
        else:
            raise RuntimeError("Select a Python version >= PYTHON_3_10")

        lambda_architecture = config["lambda"].get("architecture", "x86_64")
        if lambda_architecture.lower() == "x86_64":
            architecture = _lambda.Architecture.X86_64
        elif lambda_architecture.lower() == "arm64":
            architecture = _lambda.Architecture.ARM_64

        # Create S3 buckets
        self.s3_buckets = []
        for bucket in config["s3"]["buckets"]:
            s3_bucket = s3.Bucket(
                self,
                bucket["name"],
                bucket_name=f"{bucket["name"]}-{cdk.Aws.ACCOUNT_ID}",
                public_read_access=False,
                event_bridge_enabled=True,
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            )

            self.s3_buckets.append(s3_bucket)

        # Create the Origin Access Control
        self.origin_access_control = cloudfront.CfnOriginAccessControl(
            self,
            "OriginAccessControl",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="MyOriginAccessControl",
                description="Origin Access Control for CloudFront",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4"
            )
        )

        edge_lambda = _lambda.Function(
            self,
            "EdgeLambdaFunction",
            code=_lambda.Code.from_asset("assets/lambda"),
            handler="edge_handler.handler",
            runtime=self._runtime,
            architecture=architecture,
            timeout=cdk.Duration.seconds(30),
        )

        # Create CloudFront distribution
        self.cf_distribution = cloudfront.Distribution(self, "CloudFrontDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.s3_buckets[0]),
            )
        )

        for bucket in self.s3_buckets:
            # print(f"Adding behavior for bucket: {bucket.bucket_name}, {i=}")
            self.cf_distribution.add_behavior(
                path_pattern=f"/{bucket.bucket_name}/*",
                origin=origins.S3Origin(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
                edge_lambdas=[cloudfront.EdgeLambda(
                    function_version=edge_lambda.current_version,
                    event_type=cloudfront.LambdaEdgeEventType.ORIGIN_REQUEST
                )]
            )

        cfnDistribution = self.cf_distribution.node.default_child
        for i in range(len(self.s3_buckets) + 1):
            # Update OriginAccessControl
            cfnDistribution.add_property_override(
                f'DistributionConfig.Origins.{i}.OriginAccessControlId',
                self.origin_access_control.get_att('Id'),
            )
            cfnDistribution.add_property_override(
                f'DistributionConfig.Origins.{i}.S3OriginConfig.OriginAccessIdentity',
                '',
            )


        logger.debug("Printing out stack details")
        logger.debug(cdk_utils.print_children(self, level=0))

        # Delete the S3 Origin Access Identity statements
        for bucket in self.s3_buckets:
            policy_node = bucket.node.find_child("Policy").node.default_child    # CfnBucketPolicy
            # print(f"{policy_node=}")
            # bucket_policy = bucket.policy
            # print(f"{bucket_policy=}")
            # policy_document = bucket_policy.document
            # print(f"{policy_document=}")
            # print(policy_document.to_json())
            policy_node.add_property_override("PolicyDocument.Statement.0", None)
            

        # Delete the CloudFrontOriginAccessIdentity resources
        # self.node.find_child("")

        # Add OriginAccessControl
        # print(f"Adding OriginAccessControl for: {bucket.bucket_name}")
        # cfnDistribution.add_property_override(
        #     f'DistributionConfig.Origins.{i}.OriginAccessControlId',
        #     self.origin_access_control.get_att('Id'),
        # )

        # # Remove OriginAccessIdentity
        # print(f"Removing OriginAccessIdentity for: {bucket.bucket_name}")
        # cfnDistribution.add_property_override(
        #     f'DistributionConfig.Origins.{i}.S3OriginConfig.OriginAccessIdentity',
        #     '',
        # )

        for bucket in self.s3_buckets:
            # Update bucket policy to pull in the origin access policy from CloudFront
            bucket.add_to_resource_policy(iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "aws:SourceArn": f"arn:aws:cloudfront::{cdk.Aws.ACCOUNT_ID}:distribution/{self.cf_distribution.distribution_id}"
                    }
                }
            ))
            
        # Create the Lambda function role
        self.lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        metadata_lambda = _lambda.Function(
            self,
            "MetadataLambdaFunction",
            code=_lambda.Code.from_asset("assets/lambda"),
            handler="metadata_handler.handler",
            runtime=self._runtime,
            architecture=architecture,
            timeout=cdk.Duration.seconds(300),
            environment={
                "CLOUDFRONT_DISTRIBUTION_DOMAIN": self.cf_distribution.distribution_domain_name,
            },
            role=self.lambda_role,
        )

        # Add policy
        for bucket in self.s3_buckets:
            bucket.grant_read_write(self.lambda_role)

        # Add an EventBridge rule to trigger the Lambda function when an object is created or deleted
        self.event_rule = events.Rule(
                        self,
            "ObjectCreatedOrDeletedRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created", "Object Deleted"],
                detail={"bucket": {"name": [bucket.bucket_name for bucket in self.s3_buckets]},
                        "object": {"key": [{"anything-but": {"suffix":".metadata.json"}}]}},
            ),
            targets=[events_targets.LambdaFunction(metadata_lambda)],
        )

        # Output the CloudFront distribution domain name
        CfnOutput(
            self,
            "CloudFrontDistributionDomain",
            value=self.cf_distribution.distribution_domain_name,
        )

        # Output the S3 bucket names
        for i, bucket in enumerate(self.s3_buckets):
            CfnOutput(
                self,
                f"S3Bucket{i+1}",
                value=bucket.bucket_arn,
            )
