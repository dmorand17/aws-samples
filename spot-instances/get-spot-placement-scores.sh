#!/usr/bin/env bash
#
# get-spot-placement-scores.sh
#
# Discovers compute-optimized x86_64 instance types matching a vCPU range,
# then queries the EC2 Spot Placement Score API per type to find the top 3
# best-scored instance types per AZ.
#
# Usage:
#   ./get-spot-placement-scores.sh [options]
#
# Options:
#   -t, --target-capacity NUM    Target number of instances (default: 1)
#   -u, --capacity-unit          Use "vcpu" or "memory-mib" instead of "units" (default: units)
#   -r, --regions REGION,...     Comma-separated list of regions to score (default: all regions)
#   -c, --vcpu-min NUM           Minimum vCPUs (default: 72)
#   -C, --vcpu-max NUM           Maximum vCPUs (default: 96)
#   -n, --top NUM                Top N instance types per AZ (default: 3)
#   -a, --az AZ,...              Comma-separated AZ IDs to filter output (e.g. use1-az1,use1-az2)
#   -h, --help                   Show this help message
#
# Requirements:
#   - AWS CLI v2
#   - jq
#   - Permissions: ec2:GetSpotPlacementScores, ec2:DescribeInstanceTypes
#

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
TARGET_CAPACITY=1
CAPACITY_TYPE="units"
REGIONS_FILTER=""
VCPU_MIN=72
VCPU_MAX=96
TOP_N=3
AZ_FILTER=""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
usage() {
  grep '^#' "$0" | grep -v '^#!/' | sed 's/^# \{0,1\}//'
  exit 0
}

log() { echo "[$(date '+%H:%M:%S')] $*" >&2; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--target-capacity)  TARGET_CAPACITY="$2"; shift 2 ;;
    -u|--capacity-unit)    CAPACITY_TYPE="$2";   shift 2 ;;
    -r|--regions)          REGIONS_FILTER="$2";  shift 2 ;;
    -c|--vcpu-min)         VCPU_MIN="$2";        shift 2 ;;
    -C|--vcpu-max)         VCPU_MAX="$2";        shift 2 ;;
    -n|--top)              TOP_N="$2";            shift 2 ;;
    -a|--az)               AZ_FILTER="$2";        shift 2 ;;
    -h|--help)             usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

# ---------------------------------------------------------------------------
# Build the CLI arguments
# ---------------------------------------------------------------------------
REGION_ARGS=()
if [[ -n "$REGIONS_FILTER" ]]; then
  IFS=',' read -ra REGION_LIST <<< "$REGIONS_FILTER"
  for r in "${REGION_LIST[@]}"; do
    REGION_ARGS+=(--region-names "$r")
  done
fi

# ---------------------------------------------------------------------------
# Discover matching instance types
# ---------------------------------------------------------------------------
log "Discovering compute-optimized x86_64 instance types with ${VCPU_MIN}-${VCPU_MAX} vCPUs..."

INSTANCE_TYPES=$(aws ec2 describe-instance-types \
  --filters \
    "Name=processor-info.supported-architecture,Values=x86_64" \
    "Name=vcpu-info.default-vcpus,Values=$(seq -s, "$VCPU_MIN" "$VCPU_MAX")" \
    "Name=instance-type,Values=c*" \
    "Name=bare-metal,Values=false" \
  --query 'InstanceTypes[].InstanceType' \
  --output text)

IFS=$'\n' read -r -d '' -a TYPES <<< "$(echo "$INSTANCE_TYPES" | tr '\t' '\n' | sort)" || true

if [[ ${#TYPES[@]} -eq 0 ]]; then
  echo "No instance types found matching criteria." >&2
  exit 1
fi

log "Found ${#TYPES[@]} types: ${TYPES[*]}"

# ---------------------------------------------------------------------------
# Query scores per instance type
# ---------------------------------------------------------------------------
log "Querying Spot Placement Scores (${#TYPES[@]} types)..."
log "  Target capacity: $TARGET_CAPACITY ($CAPACITY_TYPE)"
[[ -n "$REGIONS_FILTER" ]] && log "  Regions filter : $REGIONS_FILTER"
[[ -n "$AZ_FILTER" ]] && log "  AZ filter      : $AZ_FILTER"

ALL_RESULTS="[]"

for ITYPE in "${TYPES[@]}"; do
  log "  Querying: $ITYPE"
  RESPONSE=$(aws ec2 get-spot-placement-scores \
    --instance-types "$ITYPE" \
    --target-capacity "$TARGET_CAPACITY" \
    --target-capacity-unit-type "$CAPACITY_TYPE" \
    --single-availability-zone \
    "${REGION_ARGS[@]}" \
    --output json)

  TAGGED=$(echo "$RESPONSE" | jq --arg itype "$ITYPE" \
    '[.SpotPlacementScores[] | . + {InstanceType: $itype}]')
  ALL_RESULTS=$(jq -s '.[0] + .[1]' <(echo "$ALL_RESULTS") <(echo "$TAGGED"))
done

# ---------------------------------------------------------------------------
# Display top N per AZ, sorted by Region → AZ → Score desc
# ---------------------------------------------------------------------------
# Build AZ filter list for jq
if [[ -n "$AZ_FILTER" ]]; then
  AZ_JQ_FILTER=$(echo "$AZ_FILTER" | jq -R 'split(",")')
else
  AZ_JQ_FILTER="null"
fi

echo ""
echo "Top ${TOP_N} Instance Types per AZ (by score):"
echo "-------------------------------------------------------------"
echo "$ALL_RESULTS" | jq -r --argjson n "$TOP_N" --argjson azf "$AZ_JQ_FILTER" '
  (if $azf then map(select(.AvailabilityZoneId as $az | $azf | index($az))) else . end)
  | group_by(.Region, .AvailabilityZoneId)
  | map(sort_by(-.Score) | .[:$n])
  | flatten
  | sort_by(.Region, .AvailabilityZoneId, -.Score)
  | .[]
  | [
      ("Score: " + (.Score | tostring)),
      ("Type: " + .InstanceType),
      ("Region: " + .Region),
      (if .AvailabilityZoneId != "" then "AZ: " + .AvailabilityZoneId else "" end)
    ]
  | map(select(. != ""))
  | join("  |  ")
'

echo ""
echo "Raw JSON response saved to: spot-placement-scores-result.json"
echo "$ALL_RESULTS" > spot-placement-scores-result.json
