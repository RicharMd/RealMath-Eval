#!/bin/bash
# RealMath-Eval Judge Inference - Linux
# Run inference and evaluation on RealMath-Eval benchmark
# Usage: ./judge_realmath_eval.sh [dataset_name] [output_bucket] [method] [model] [max_samples]
#   max_samples: 0 = no limit, positive int for quick test

set -e

# Parameters (with defaults)
dataset_name="${1:-realmath_eval}"
output_bucket="${2:-realmath_eval}"
method="${3:-vanilla}"
model="${4:-gemini-3-pro-preview}"
max_samples="${5:-0}"

# UTF-8 for Python
export PYTHONIOENCODING="utf-8"
export PYTHONUTF8="1"

# Timestamp and paths
timestamp=$(date +%Y%m%d_%H%M%S)
output_dir="./outputs/${output_bucket}/${method}/${model}/${timestamp}"
log_file="${output_dir}/inference.log"

mkdir -p "$output_dir"

echo "========================================"
echo "RealMath-Eval $dataset_name  <->  $method $model Inference"
echo "========================================"
echo "Dataset: $dataset_name"
echo "Method: $method"
echo "Model: $model"
echo "Output directory: $output_dir"
echo "Log file: $log_file"
echo ""

# Run inference
echo "Starting inference..."
max_samples_args=""
if [[ "$max_samples" -gt 0 ]]; then
    max_samples_args="--max_samples $max_samples"
fi

if python inference.py \
    --test_dataset_name "$dataset_name" \
    --method_name "$method" \
    --model_name "$model" \
    --output_path "${output_dir}/results.jsonl" \
    --model_temperature 0.7 \
    --model_max_tokens 8192 \
    --model_timeout 600 \
    $max_samples_args \
    2>&1 | tee "$log_file"; then
    echo ""
    echo "Inference completed!"
    echo "Results saved to: $output_dir"
    echo "Log saved to: $log_file"
else
    echo "Inference failed!"
    exit 1
fi

# Auto-evaluate results
results_file="${output_dir}/results.jsonl"
if [[ -f "$results_file" ]]; then
    echo ""
    echo "=== Starting Evaluation ==="

    if python eval/scorer.py \
        --input-file "$results_file" \
        --output-dir "$output_dir" \
        --dataset_name "judge_benchmark"; then
        echo "Evaluation completed!"
    else
        echo "Evaluation failed!"
    fi

    echo ""
    echo "=== Quick Summary ==="

    if command -v python &>/dev/null; then
        count=$(python -c "import json; lines=[l for l in open('$results_file') if l.strip()]; print(len(lines))" 2>/dev/null || echo "?")
        echo "Total samples processed: $count"
        if [[ "$count" != "0" && "$count" != "?" ]]; then
            python -c "
import json
with open('$results_file') as f:
    items = [json.loads(l) for l in f if l.strip()]
if items:
    s = items[0]
    print('Sample GT:', s.get('gt'))
    r = s.get('response', '')[:150]
    print('Sample response preview:', r + ('...' if len(s.get('response','')) > 150 else ''))
" 2>/dev/null || true
        fi
    fi
else
    echo "Warning: Results file not found at $results_file"
fi

echo ""
echo "Script execution completed!"
