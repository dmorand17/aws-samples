#!/usr/bin/env bash
#
# request-spot-fleet.sh
#
# Requests a Spot Fleet using attribute-based instance selection, matching
# the parameters from spot-scores-by-attributes.yaml.
#
# NOTE: request-spot-fleet is a legacy API. For production use, prefer
# ec2 create-fleet with instant mode and price-capacity-optimized strategy.
#
# Usage:
#   ./request-spot-fleet.sh --iam-fleet-role ARN --subnet-id ID [options]
#
# Options:
#   -f, --iam-fleet-role ARN  IAM fleet role ARN (required)
#   -s, --subnet-id ID        Subnet ID to launch into (required)
#   -i, --ami-id ID           AMI ID (default: latest Amazon Linux 2023 x86_64)
#   -r, --region REGION       AWS region (default: us-east-1)
#   -n, --count NUM           Target capacity (default: 1)
#   -k, --key-name NAME       SSH key pair name (optional)
#   -d, --dry-run             Validate without launching
#   -h, --help                Show this help message
#

set -euo pipefail

IAM_FLEET_ROLE=""
SUBNET_ID=""
AMI_ID=""
REGION="us-east-1"
COUNT=1
KEY_NAME=""
DRY_RUN=""

usage() {
  grep '^#' "$0" | grep -v '^#!/' | sed 's/^# \{0,1\}//'
  exit 0
}

log() { echo "[$(date '+%H:%M:%S')] $*" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--iam-fleet-role) IAM_FLEET_ROLE="$2"; shift 2 ;;
    -s|--subnet-id)      SUBNET_ID="$2";      shift 2 ;;
    -i|--ami-id)         AMI_ID="$2";          shift 2 ;;
    -r|--region)         REGION="$2";          shift 2 ;;
    -n|--count)          COUNT="$2";           shift 2 ;;
    -k|--key-name)       KEY_NAME="$2";        shift 2 ;;
    -d|--dry-run)        DRY_RUN="--dry-run";  shift ;;
    -h|--help)           usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

if [[ -z "$IAM_FLEET_ROLE" ]]; then
  echo "Error: --iam-fleet-role is required." >&2
  exit 1
fi
if [[ -z "$SUBNET_ID" ]]; then
  echo "Error: --subnet-id is required." >&2
  exit 1
fi

# Resolve AMI if not provided
if [[ -z "$AMI_ID" ]]; then
  log "Looking up latest Amazon Linux 2023 x86_64 AMI..."
  AMI_ID=$(aws ec2 describe-images \
    --region "$REGION" \
    --owners amazon \
    --filters \
      "Name=name,Values=al2023-ami-2023.*-x86_64" \
      "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text)
  log "Using AMI: $AMI_ID"
fi

# Build spot fleet config matching spot-scores-by-attributes.yaml:
#   ArchitectureTypes: x86_64, VirtualizationTypes: hvm
#   VCpuCount: 72-192, MemoryMiB: 144000-256000
#   BurstablePerformance: excluded, BareMetal: excluded
FLEET_CONFIG=$(jq -n \
  --arg role "$IAM_FLEET_ROLE" \
  --arg ami "$AMI_ID" \
  --arg subnet "$SUBNET_ID" \
  --arg key "$KEY_NAME" \
  --argjson count "$COUNT" \
  '{
    IamFleetRole: $role,
    AllocationStrategy: "priceCapacityOptimized",
    TargetCapacity: $count,
    Type: "request",
    TerminateInstancesWithExpiration: true,
    LaunchSpecifications: [
      {
        ImageId: $ami,
        SubnetId: $subnet,
        InstanceRequirements: {
          VCpuCount: { Min: 72, Max: 192 },
          MemoryMiB: { Min: 144000, Max: 256000 },
          BurstablePerformance: "excluded",
          BareMetal: "excluded"
        }
      } + (if $key != "" then { KeyName: $key } else {} end)
    ]
  }')

log "Requesting Spot Fleet: capacity=$COUNT region=$REGION"

RESPONSE=$(aws ec2 request-spot-fleet \
  --region "$REGION" \
  --spot-fleet-request-config "$FLEET_CONFIG" \
  $DRY_RUN \
  --output json)

echo "$RESPONSE" | jq .

FLEET_ID=$(echo "$RESPONSE" | jq -r '.SpotFleetRequestId // empty')
if [[ -n "$FLEET_ID" ]]; then
  log "Fleet request ID: $FLEET_ID"
  echo ""
  log "Check status:    aws ec2 describe-spot-fleet-requests --region $REGION --spot-fleet-request-ids $FLEET_ID"
  log "List instances:  aws ec2 describe-spot-fleet-instances --region $REGION --spot-fleet-request-id $FLEET_ID"
  log "Cancel fleet:    aws ec2 cancel-spot-fleet-requests --region $REGION --spot-fleet-request-ids $FLEET_ID --terminate-instances"
fi
