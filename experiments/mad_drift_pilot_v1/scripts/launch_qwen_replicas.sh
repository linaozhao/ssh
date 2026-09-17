#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT/results/service_logs"
MODEL_PATH="/data/zla/mad_drift_benchmark/modelscope_models/Qwen/Qwen3-8B"
VLLM_BIN="/home/share/anaconda/bin/vllm"
mkdir -p "$STATE_DIR"

GPUS=(0 3 4 5 6 7)
PORTS=(8101 8102 8103 8104 8105 8106)

case "${1:-}" in
  serve)
    gpu="${2:?GPU index required}"
    port="${3:?port required}"
    export CUDA_VISIBLE_DEVICES="$gpu"
    exec "$VLLM_BIN" serve "$MODEL_PATH" \
      --served-model-name Qwen3-8B \
      --host 127.0.0.1 --port "$port" \
      --dtype bfloat16 \
      --gpu-memory-utilization 0.90 \
      --max-model-len 16384 \
      --max-num-seqs 8 \
      --enforce-eager \
      --disable-frontend-multiprocessing
    ;;
  start)
    for index in "${!GPUS[@]}"; do
      gpu="${GPUS[$index]}"
      port="${PORTS[$index]}"
      pid_file="$STATE_DIR/qwen_gpu${gpu}_port${port}.pid"
      log_file="$STATE_DIR/qwen_gpu${gpu}_port${port}.log"
      if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        echo "already running gpu=$gpu port=$port pid=$(cat "$pid_file")"
        continue
      fi
      CUDA_VISIBLE_DEVICES="$gpu" nohup "$VLLM_BIN" serve "$MODEL_PATH" \
        --served-model-name Qwen3-8B \
        --host 127.0.0.1 --port "$port" \
        --dtype bfloat16 \
        --gpu-memory-utilization 0.90 \
        --max-model-len 16384 \
        --max-num-seqs 8 \
        --enforce-eager \
        --disable-frontend-multiprocessing \
        >"$log_file" 2>&1 &
      echo "$!" >"$pid_file"
      echo "started gpu=$gpu port=$port pid=$!"
    done
    ;;
  stop)
    for pid_file in "$STATE_DIR"/*.pid; do
      [[ -e "$pid_file" ]] || continue
      pid="$(cat "$pid_file")"
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "stopped pid=$pid"
      fi
    done
    ;;
  status)
    for index in "${!GPUS[@]}"; do
      gpu="${GPUS[$index]}"
      port="${PORTS[$index]}"
      pid_file="$STATE_DIR/qwen_gpu${gpu}_port${port}.pid"
      if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        echo "running gpu=$gpu port=$port pid=$(cat "$pid_file")"
      else
        echo "stopped gpu=$gpu port=$port"
      fi
    done
    ;;
  *)
    echo "Usage: $0 {serve GPU PORT|start|stop|status}" >&2
    exit 2
    ;;
esac
