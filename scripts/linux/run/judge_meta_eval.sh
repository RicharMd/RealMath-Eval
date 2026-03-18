#!/bin/bash
# RealMath-Eval Meta-Evaluation - Linux
# Run inference on meta_eval_data (requires prior realmath_eval results)
# Usage: ./judge_meta_eval.sh [method] [model]

set -e

method="${1:-cot}"
model="${2:-gemini-3-pro-preview}"

export PYTHONIOENCODING="utf-8"
export PYTHONUTF8="1"

timestamp=$(date +%Y%m%d_%H%M%S)
output_dir="./outputs/realmath_eval/${method}/${model}/${timestamp}"
mkdir -p "$output_dir"

echo "========================================"
echo "RealMath-Eval Meta-Evaluation  <->  $method $model"
echo "========================================"

python inference.py \
    --test_dataset_name meta_eval_data \
    --method_name "$method" \
    --model_name "$model" \
    --output_path "${output_dir}/results.jsonl" \
    --model_temperature 0.7 \
    --model_max_tokens 8192 \
    --model_timeout 600

echo ""
echo "Meta-evaluation completed! Results: $output_dir"
