#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  printf 'usage: %s CONFIG_JSON NEW_SERVICE_MANIFEST_JSON\n' "$0" >&2
  exit 2
fi

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
# The Python gate verifies the authorized physical device and its CUDA UUID.
exec "${PYTHON:-python}" -m cbm_drift_v3.runtime --config "$1" --manifest "$2" --launch
