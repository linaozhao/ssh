#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 GPU_INDEX PORT" >&2
  exit 2
fi

GPU_INDEX="$1"
PORT="$2"
MODEL_PATH="/data/zla/mad_drift_benchmark/modelscope_models/Qwen/Qwen3-8B"

CUDA_VISIBLE_DEVICES="${GPU_INDEX}" exec python -m vllm.entrypoints.openai.api_server \
  --model "${MODEL_PATH}" \
  --served-model-name Qwen3-8B \
  --host 127.0.0.1 \
  --port "${PORT}" \
  --dtype bfloat16 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 8 \
  --enable-prefix-caching \
  --enforce-eager
