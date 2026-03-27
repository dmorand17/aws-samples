# Spot Instance Placement Scores

Query the EC2 [Spot Placement Score](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html) API to find the best availability zones for launching Spot instances. Automatically discovers compute-optimized x86_64 instance types matching a vCPU range, then shows the top N best-scored types per AZ.

## Prerequisites

- AWS CLI v2
- `jq`
- IAM permissions: `ec2:GetSpotPlacementScores`, `ec2:DescribeInstanceTypes`

## Usage

```bash
./get-spot-placement-scores.sh [options]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --target-capacity NUM` | Target number of instances | `1` |
| `-u, --capacity-unit TYPE` | Capacity unit: `units`, `vcpu`, or `memory-mib` | `units` |
| `-r, --regions REGION,...` | Comma-separated list of regions to score | all regions |
| `-c, --vcpu-min NUM` | Minimum vCPUs | `72` |
| `-C, --vcpu-max NUM` | Maximum vCPUs | `96` |
| `-n, --top NUM` | Top N instance types per AZ | `3` |
| `-a, --az AZ,...` | Comma-separated AZ IDs to filter output | all AZs |
| `-h, --help` | Show help | |

### Examples

```bash
# Default: top 3 types per AZ for 72-96 vCPU compute instances
./get-spot-placement-scores.sh

# Score specific regions with a higher capacity target
./get-spot-placement-scores.sh -t 10 -r us-east-1,us-west-2,eu-west-1

# Custom vCPU range, top 5 per AZ
./get-spot-placement-scores.sh -c 48 -C 64 -n 5 -r us-east-1

# Filter to specific AZs
./get-spot-placement-scores.sh -r us-east-1 -a use1-az1,use1-az2
```

### Output

Shows the top N instance types per AZ, sorted by Region → AZ → Score:

```
Score: 9  |  Type: c6a.24xlarge   |  Region: us-east-1  |  AZ: use1-az1
Score: 8  |  Type: c7i.24xlarge   |  Region: us-east-1  |  AZ: use1-az1
Score: 8  |  Type: c5a.24xlarge   |  Region: us-east-1  |  AZ: use1-az1
Score: 9  |  Type: c7a.24xlarge   |  Region: us-east-1  |  AZ: use1-az2
...
```

Raw JSON results are saved to `spot-placement-scores-result.json`.

## How It Works

1. Uses `ec2 describe-instance-types` to discover all compute-optimized (`c*`) x86_64 instance types matching the vCPU range
2. Queries `get-spot-placement-scores` individually per type with `--single-availability-zone`
3. Groups results by AZ and shows the top N types by score

## Spot Placement Score

A [Spot placement score](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-placement-score.html) indicates how likely a Spot request will succeed in a given Region or Availability Zone, scored from 1 to 10 (10 = highly likely to succeed). It does not guarantee capacity or predict interruption risk — it's a point-in-time recommendation.

Use cases:
- Identify optimal AZs for single-AZ workloads
- Relocate or scale Spot capacity to a different Region when current capacity decreases
- Simulate future capacity needs to pick the best Region for expansion

Limitations:
- Target capacity limit is based on your recent Spot usage
- Request configuration rate limits apply within a 24-hour window
- You must specify at least 3 different instance types, otherwise scores will always be low
- No additional cost to use

## Spot Best Practices

From the AWS [Spot best practices guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html):

1. **Prepare for interruptions** — Architect for fault tolerance. Use [EC2 rebalance recommendations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/rebalance-recommendations.html) and the 2-minute [interruption notice](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html). Create EventBridge rules to capture these signals and checkpoint or gracefully handle interruptions.

2. **Be flexible on instance types and AZs** — A good rule of thumb is to be flexible across at least 10 instance types per workload. Include older generations (less On-Demand demand) and larger sizes (if vertically scalable). Use all AZs in your VPC.

3. **Use attribute-based instance type selection** — Specify attributes (vCPUs, memory, storage) instead of explicit instance types. This automatically includes new instance types as they launch.

4. **Use placement scores** — Use this script (or the console) to find the Regions/AZs most likely to have capacity before launching.

5. **Use Auto Scaling groups or EC2 Fleet** — Manage aggregate capacity rather than individual instances. These services automatically replace interrupted instances.

6. **Use `price-capacity-optimized` allocation strategy** — Provisions from the most-available pools at the lowest price, reducing interruption likelihood.

7. **Use integrated AWS services** — EMR, ECS, EKS, Batch, SageMaker, Elastic Beanstalk, and GameLift all have built-in Spot support.

### Recommended Spot request methods

| Method | Recommended? | Notes |
|--------|:---:|-------|
| `CreateAutoScalingGroup` | ✅ | Best for managed lifecycle + auto scaling |
| `CreateFleet` (instant mode) | ✅ | Best for self-managed lifecycle without auto scaling |
| `RunInstances` | ⚠️ | Single instance type only, no mixed configurations |
| `RequestSpotFleet` | ❌ | Legacy, no planned investment |
| `RequestSpotInstances` | ❌ | Legacy, no planned investment |
