# Spot Instance Placement Scores

Tools for querying the EC2 [Spot Placement Score](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html) API to find the best availability zones for launching Spot instances.

## Prerequisites

- AWS CLI v2
- `jq`
- IAM permissions: `ec2:GetSpotPlacementScores`, `ec2:DescribeInstanceTypes`

## Project Structure

```
scripts/
  get-spot-scores.sh             # Scores using a cli-input-yaml config file
  list-instance-types.sh         # Lists instance types filtered by vCPU/memory range
  request-spot-fleet.sh          # Requests a Spot Fleet (legacy API)
configs/
  spot-scores-by-type.yaml       # Config: score specific instance types
  spot-scores-by-attributes.yaml # Config: score by instance attributes
  get-spot-placement-scores-skeleton.yaml  # Full API input skeleton reference
```

## Scripts

### get-spot-scores.sh

Queries the Spot Placement Score API using a `--cli-input-yaml` config file. Works with both instance-type-based and attribute-based configs.

```bash
./scripts/get-spot-scores.sh <config.yaml> [-n TOP] [-a AZ,...]
```

| Flag              | Description                              | Default |
| ----------------- | ---------------------------------------- | ------- |
| `config.yaml`     | Path to cli-input-yaml config (required) |         |
| `-n, --top NUM`   | Top N results per AZ                     | `3`     |
| `-a, --az AZ,...` | Filter to specific AZ IDs                | all     |

```bash
# Score by explicit instance types
./scripts/get-spot-scores.sh configs/spot-scores-by-type.yaml

# Score by instance attributes, top 5
./scripts/get-spot-scores.sh configs/spot-scores-by-attributes.yaml -n 5
```

### list-instance-types.sh

Lists EC2 instance types with vCPU and memory details, filtered by range parameters.

```bash
./scripts/list-instance-types.sh [options]
```

| Flag                  | Description           | Default     |
| --------------------- | --------------------- | ----------- |
| `-c, --vcpu-min NUM`  | Minimum vCPUs         | `96`        |
| `-C, --vcpu-max NUM`  | Maximum vCPUs         | `192`       |
| `-m, --mem-min NUM`   | Minimum memory in MiB | `144000`    |
| `-M, --mem-max NUM`   | Maximum memory in MiB | `256000`    |
| `-r, --region REGION` | AWS region            | `us-east-1` |
| `-a, --arch ARCH`     | `x86_64` or `arm64`   | `x86_64`    |

### request-spot-fleet.sh

Requests a Spot Fleet using attribute-based instance selection.

> **Note:** `request-spot-fleet` is a legacy API. For production use, prefer `ec2 create-fleet` with instant mode and `price-capacity-optimized` strategy.

```bash
./scripts/request-spot-fleet.sh --iam-fleet-role ARN --subnet-id ID [options]
```

| Flag                       | Description                   | Default              |
| -------------------------- | ----------------------------- | -------------------- |
| `-f, --iam-fleet-role ARN` | IAM fleet role ARN (required) |                      |
| `-s, --subnet-id ID`       | Subnet ID (required)          |                      |
| `-i, --ami-id ID`          | AMI ID                        | latest AL2023 x86_64 |
| `-r, --region REGION`      | AWS region                    | `us-east-1`          |
| `-n, --count NUM`          | Target capacity               | `1`                  |
| `-k, --key-name NAME`      | SSH key pair name             |                      |
| `-d, --dry-run`            | Validate without launching    |                      |

## Configs

| File                                      | Description                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| `spot-scores-by-type.yaml`                | Scores specific instance types (c5a, c6a, c6i, c7a, c7i .24xlarge) in us-east-1 |
| `spot-scores-by-attributes.yaml`          | Scores by attributes: x86_64, 96-192 vCPUs, 196-256 GiB memory, us-east-1       |
| `get-spot-placement-scores-skeleton.yaml` | Full `get-spot-placement-scores` API input skeleton with all available fields   |

## Spot Placement Score

A [Spot placement score](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html) indicates how likely a Spot request will succeed in a given Region or AZ, scored 1-10 (10 = highly likely). It's a point-in-time recommendation, not a capacity guarantee.

Use cases:

- Identify optimal AZs for single-AZ workloads
- Relocate or scale Spot capacity when current capacity decreases
- Simulate future capacity needs to pick the best Region

Limitations:

- Target capacity limit is based on your recent Spot usage
- Rate limits apply within a 24-hour window
- At least 3 instance types required, otherwise scores will be low

## Spot Best Practices

From the [Spot best practices guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html):

1. **Prepare for interruptions** — Use [rebalance recommendations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/rebalance-recommendations.html) and the 2-minute [interruption notice](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html). Create EventBridge rules to capture these signals.
2. **Be flexible** — Target at least 10 instance types. Include older generations and larger sizes. Use all AZs.
3. **Use attribute-based selection** — Specify attributes (vCPUs, memory) instead of explicit types. New types are included automatically.
4. **Use placement scores** — Find the best Regions/AZs before launching.
5. **Use Auto Scaling groups or EC2 Fleet** — Manage aggregate capacity, not individual instances.
6. **Use `price-capacity-optimized`** — Provisions from the most-available pools at the lowest price.
7. **Use integrated AWS services** — EMR, ECS, EKS, Batch, SageMaker, Elastic Beanstalk, and GameLift all have built-in Spot support.

### Recommended Spot request methods

| Method                       | Recommended? | Notes                                   |
| ---------------------------- | :----------: | --------------------------------------- |
| `CreateAutoScalingGroup`     |      ✅      | Managed lifecycle + auto scaling        |
| `CreateFleet` (instant mode) |      ✅      | Self-managed lifecycle, no auto scaling |
| `RunInstances`               |      ⚠️      | Single instance type only               |
| `RequestSpotFleet`           |      ❌      | Legacy, no planned investment           |
| `RequestSpotInstances`       |      ❌      | Legacy, no planned investment           |
