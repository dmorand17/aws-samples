# Enable Amazon Q for Business for S3

This is an improved version of https://gitlab.aws.dev/domorand/enable-q-for-s3 to allow for handling of multiple S3 buckets.

This solution creates the infrastructure to allow Amazon Q for Business to open S3 objects from sources.
The solution leverages an [s3 metadata file](https://docs.aws.amazon.com/amazonq/latest/qbusiness-ug/s3-metadata.html)
to update the S3 object url to reference a CloudFront distribution.

- S3 bucket
- CloudFront distribution (uses S3 bucket(s) as origin)
- Lambda function (triggered from Create events on S3 bucket to generate Amazon Q metadata)

## Getting Started

1. Deploy this solution via the deployment steps [below](#deploy)
2. Setup Amazon Q for Business chat application with a data source pointing to the S3 bucket(s) created by the deployment
   1. When adding the data source make sure to define the metadata path as `metadata` (example below)
   2. ![Metadata](images/metadata.png)

## 🚀 <a href="#deploy">Deploy</a>

1/ Copy [config.yml.sample](config.yml.sample) and configure the s3 buckets. Add `buckets` to deploy multiple S3 buckets to enable for Amazon Q.

_Sample config below_

```
s3:
  buckets:
    - name: bucket1
    - name: bucket2
```

```bash
cdk deploy
```

## Development

Create virtual environment and install requirements

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CDK useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation

Enjoy!
