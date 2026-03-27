#!/usr/bin/env bash
#
# list-instance-types.sh
#
# Lists EC2 instance types with vCPU and memory details, filtered by
# vCPU and memory range parameters.
#
# Usage:
#   ./list-instance-types.sh [options]
#
# Options:
#   -c, --vcpu-min NUM       Minimum vCPUs (default: 72)
#   -C, --vcpu-max NUM       Maximum vCPUs (default: 192)
#   -m, --mem-min NUM        Minimum memory in MiB (default: 144000)
#   -M, --mem-max NUM        Maximum memory in MiB (default: 256000)
#   -r, --region REGION      AWS region (default: us-east-1)
#   -a, --arch ARCH          Architecture: x86_64, arm64 (default: x86_64)
#   -h, --help               Show this help message
#

set -euo pipefail

VCPU_MIN=96
VCPU_MAX=192
MEM_MIN=144000
MEM_MAX=256000
REGION="us-east-1"
ARCH="x86_64"

usage() {
  grep '^#' "$0" | grep -v '^#!/' | sed 's/^# \{0,1\}//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--vcpu-min) VCPU_MIN="$2"; shift 2 ;;
    -C|--vcpu-max) VCPU_MAX="$2"; shift 2 ;;
    -m|--mem-min)  MEM_MIN="$2";  shift 2 ;;
    -M|--mem-max)  MEM_MAX="$2";  shift 2 ;;
    -r|--region)   REGION="$2";   shift 2 ;;
    -a|--arch)     ARCH="$2";     shift 2 ;;
    -h|--help)     usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

aws ec2 describe-instance-types \
  --region "$REGION" \
  --filters \
    "Name=processor-info.supported-architecture,Values=$ARCH" \
    "Name=bare-metal,Values=false" \
    "Name=burstable-performance-supported,Values=false" \
  --query "InstanceTypes[?VCpuInfo.DefaultVCpus>=\`$VCPU_MIN\` && VCpuInfo.DefaultVCpus<=\`$VCPU_MAX\` && MemoryInfo.SizeInMiB>=\`$MEM_MIN\` && MemoryInfo.SizeInMiB<=\`$MEM_MAX\`].{Type:InstanceType,VCpus:VCpuInfo.DefaultVCpus,MemoryMiB:MemoryInfo.SizeInMiB}" \
  --output json | jq -r '
    sort_by(.Type) |
    ["InstanceType","vCPUs","Memory(MiB)"],
    ["-----------","-----","----------"],
    (.[] | [.Type, (.VCpus|tostring), (.MemoryMiB|tostring)]) |
    @tsv' | column -t
