#!/bin/bash
set -euo pipefail

: "${CLUSTER_NAME:?CLUSTER_NAME must be set}"

aws eks update-kubeconfig --name "$CLUSTER_NAME"
