#!/usr/bin/env python3
"""
Compute logit length between adjacent steps in segment step-split results.

For each segment with steps [step_0, step_1, ..., step_N-1]:
- For each k from 0 to N-2:
  - Context: step_0 + step_1 + ... + step_k (concatenated)
  - Forward pass with Qwen3-8B → get logits at last token position
  - Tokenize step_k+1
  - For each token t in step_k+1: compute softmax(logits[-1])[t]
  - Take maximum of these probabilities → logit_length_max (max probability) for step_k → step_k+1

Output: JSONL with original fields + logit_lengths (list of floats, length = num_steps - 1)
"""

import json
import argparse
import torch
import torch.nn.functional as F
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict, Any
import sys

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    print("Error: transformers not installed. Install with: pip install transformers")
    sys.exit(1)

try:
    import bitsandbytes
    from transformers import BitsAndBytesConfig
    BITSANDBYTES_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    BITSANDBYTES_AVAILABLE = False


def _should_download_from_hf(model_path: str) -> bool:
    """Check if model_path is a HuggingFace ID (will need download)."""
    from pathlib import Path
    p = Path(model_path)
    if p.exists():
        return False
    # HF IDs look like "org/model-name" (no absolute path, no drive)
    return "/" in model_path and not p.is_absolute()


def load_model_with_quantization(model_path: str, device: str, use_quantization: bool = True, allow_download: bool = True):
    """Load Qwen3-8B with optional 4-bit quantization.
    If model_path does not exist locally and allow_download=True, downloads from HuggingFace.
    """
    print(f"Loading model from: {model_path}")
    print(f"Target device: {device}")

    local_only = not (allow_download and _should_download_from_hf(model_path))
    if not local_only:
        print("Model not found locally. Will download from HuggingFace (first run may take a few minutes).")

    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=local_only,
    )

    load_kwargs = dict(
        device_map=device,
        trust_remote_code=True,
        local_files_only=local_only,
        torch_dtype=torch.bfloat16,
    )

    if use_quantization and BITSANDBYTES_AVAILABLE:
        print("Attempting 4-bit quantization...")
        try:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=quantization_config,
                **load_kwargs,
            ).eval()
            print("✓ Loaded with 4-bit quantization")
            return model, tokenizer
        except Exception as e:
            print(f"Warning: 4-bit quantization failed: {e}")
            print("Falling back to bfloat16 without quantization...")

    # Fallback: bfloat16 without quantization
    print("Loading with bfloat16 (no quantization)...")
    model = AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs).eval()
    print("✓ Loaded with bfloat16")
    return model, tokenizer


def compute_logit_length_for_transition(
    model,
    tokenizer,
    context_steps: List[str],
    next_step: str,
    device: str,
    verbose: bool = False,
    transition_idx: int = None,
) -> float:
    """
    Compute logit length (max probability) for step_k → step_k+1.
    
    Args:
        context_steps: List of steps [step_0, ..., step_k] (concatenated as context)
        next_step: step_k+1 (the step to predict)
        device: device string (e.g., "cuda:5")
        verbose: Whether to print detailed logs
        transition_idx: Index of this transition (for logging)
    
    Returns:
        Max logit length (maximum probability among next_step tokens given context)
    """
    # Concatenate context steps (with newlines as separators)
    context_text = "\n".join(context_steps)
    
    # Tokenize context
    context_tokens = tokenizer(context_text, return_tensors="pt", add_special_tokens=True)
    context_input_ids = context_tokens["input_ids"].to(device)
    context_length = context_input_ids.shape[1]
    
    # Check sequence length (avoid OOM)
    if context_length > 4096:
        raise ValueError(f"Context too long: {context_length} tokens (max 4096)")
    
    # Forward pass (no grad)
    with torch.no_grad():
        outputs = model(context_input_ids, output_hidden_states=False)
        logits = outputs.logits  # [1, seq_len, vocab_size]
    
    # Get logits at the last token position
    last_logits = logits[0, -1, :]  # [vocab_size]
    
    # Apply softmax to get probabilities
    probs = F.softmax(last_logits, dim=-1)  # [vocab_size]
    vocab_size = probs.shape[0]
    
    # Get top-k probabilities for reference
    top_k = 10
    top_probs, top_indices = torch.topk(probs, k=min(top_k, vocab_size))
    top_probs_list = top_probs.cpu().tolist()
    top_indices_list = top_indices.cpu().tolist()
    
    # Tokenize next_step (without special tokens, as it's a continuation)
    next_tokens = tokenizer(next_step, return_tensors="pt", add_special_tokens=False)
    next_token_ids = next_tokens["input_ids"][0]  # [num_tokens]
    next_step_length = len(next_token_ids)
    
    # Filter out invalid token IDs (should be in [0, vocab_size))
    valid_token_ids = next_token_ids[(next_token_ids >= 0) & (next_token_ids < vocab_size)]
    
    if len(valid_token_ids) == 0:
        if verbose:
            prefix = f"  Transition {transition_idx}" if transition_idx is not None else "  Transition"
            print(f"{prefix}: ⚠️  No valid tokens in next_step")
        return 0.0
    
    # Get probability for each valid token in next_step
    valid_token_ids_device = valid_token_ids.to(device)
    token_probs = probs[valid_token_ids_device].cpu().tolist()  # List of probabilities
    
    # Statistics
    max_prob = max(token_probs)
    min_prob = min(token_probs)
    mean_prob = sum(token_probs) / len(token_probs)
    
    # Check if any actual token is in top-k
    actual_in_topk = any(tid.item() in top_indices_list for tid in valid_token_ids)
    
    if verbose:
        prefix = f"  Transition {transition_idx}" if transition_idx is not None else "  Transition"
        print(f"{prefix}:")
        print(f"    Context length: {context_length} tokens ({len(context_steps)} steps)")
        print(f"    Next step length: {next_step_length} tokens ({len(valid_token_ids)} valid)")
        print(f"    Token probabilities: min={min_prob:.8f} ({min_prob*100:.6f}%), "
              f"max={max_prob:.8f} ({max_prob*100:.6f}%), "
              f"mean={mean_prob:.8f} ({mean_prob*100:.6f}%)")
        print(f"    Top-{top_k} prob range: {top_probs_list[-1]:.8f} ({top_probs_list[-1]*100:.6f}%) - "
              f"{top_probs_list[0]:.8f} ({top_probs_list[0]*100:.6f}%)")
        print(f"    Actual tokens in top-{top_k}: {'✓ Yes' if actual_in_topk else '✗ No'}")
        if not actual_in_topk and len(token_probs) > 0:
            # Show a few actual tokens and their probabilities
            print(f"    Sample actual tokens (first 5):")
            for i, (tid, prob) in enumerate(zip(valid_token_ids[:5], token_probs[:5])):
                try:
                    token_text = tokenizer.decode([tid.item()])
                    token_text = repr(token_text[:30]) if len(token_text) > 30 else repr(token_text)
                    print(f"      [{tid.item():6d}] {prob:.8f} ({prob*100:.6f}%) {token_text}")
                except:
                    print(f"      [{tid.item():6d}] {prob:.8f} ({prob*100:.6f}%)")
    
    # Return max logit length (maximum probability among next_step tokens)
    return max_prob


def process_segment(
    item: Dict[str, Any],
    model,
    tokenizer,
    device: str,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Process one segment: compute logit lengths for all adjacent step pairs."""
    steps = item.get("steps", [])
    num_steps = len(steps)
    
    if num_steps < 2:
        # Need at least 2 steps to compute a transition
        item["logit_lengths"] = []
        item["logit_length_max"] = None
        item["logit_length_computation_ok"] = False
        item["logit_length_note"] = "insufficient_steps"
        return item
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"Processing segment: row_id={item.get('row_id')}, num_steps={num_steps}")
        print(f"{'='*80}")
    
    logit_lengths = []
    
    # For each k from 0 to num_steps-2: step_k → step_k+1
    for k in range(num_steps - 1):
        context_steps = steps[:k+1]  # step_0 to step_k
        next_step = steps[k+1]  # step_k+1
        
        try:
            logit_length = compute_logit_length_for_transition(
                model, tokenizer, context_steps, next_step, device,
                verbose=verbose, transition_idx=k
            )
            logit_lengths.append(logit_length)
            if verbose:
                print(f"    ✓ Result: {logit_length:.8f} ({logit_length*100:.6f}%)")
        except Exception as e:
            if verbose:
                print(f"    ✗ Error: {e}")
            print(f"Warning: Failed to compute logit length for step {k}→{k+1}: {e}")
            logit_lengths.append(None)
    
    # Add results to item
    item["logit_lengths"] = logit_lengths
    valid_lengths = [x for x in logit_lengths if x is not None]
    # Segment-level statistic: maximum transition logit length in this segment
    item["logit_length_max"] = (
        max(valid_lengths) if valid_lengths else None
    )
    item["logit_length_computation_ok"] = all(x is not None for x in logit_lengths)
    item["logit_length_note"] = "ok" if item["logit_length_computation_ok"] else "partial_failure"
    
    return item


def _default_step_split_input() -> str:
    """Default: human step-split JSONL under analysis/data/error_segment_bundle."""
    return str(
        Path(__file__).resolve().parent.parent
        / "data"
        / "error_segment_bundle"
        / "human_error_steps_step_split.jsonl"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Compute logit length between adjacent steps using Qwen3-8B."
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Input JSONL with 'steps' field (e.g. human_error_steps_step_split.jsonl). "
             "Default: analysis/data/error_segment_bundle/human_error_steps_step_split.jsonl",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Output JSONL file (default: input_file with _logit_length suffix)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="Qwen/Qwen3-8B",
        help="Path to Qwen3-8B model directory, or HuggingFace ID (e.g. Qwen/Qwen3-8B). "
             "If path does not exist, downloads from HuggingFace (see --no-download to disable).",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Disable auto-download from HuggingFace; require local model path only.",
    )
    parser.add_argument(
        "--gpu-id",
        type=int,
        default=5,
        help="GPU ID to use (default: 5)",
    )
    parser.add_argument(
        "--use-quantization",
        action="store_true",
        default=False,
        help="Use 4-bit quantization (default: False, 80GB GPU doesn't need it)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print detailed logs for each transition (default: False)",
    )
    parser.add_argument(
        "--verbose-samples",
        type=int,
        default=0,
        help="Number of samples to show verbose logs for (0 = all, default: 0)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size for processing (default: 1, sequential processing)",
    )
    
    args = parser.parse_args()

    if args.input_file is None:
        args.input_file = _default_step_split_input()

    # Determine device
    device = f"cuda:{args.gpu_id}" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Check GPU availability
    if device.startswith("cuda"):
        gpu_id = int(device.split(":")[1])
        if gpu_id >= torch.cuda.device_count():
            print(f"Error: GPU {gpu_id} not available. Available GPUs: 0-{torch.cuda.device_count()-1}")
            return 1
        print(f"GPU {gpu_id} memory: {torch.cuda.get_device_properties(gpu_id).total_memory / 1e9:.1f} GB")
    
    # Load model (default: no quantization for 80GB GPU)
    if args.use_quantization and not BITSANDBYTES_AVAILABLE:
        print("Warning: --use-quantization specified but bitsandbytes not available. Using bfloat16 instead.")
        args.use_quantization = False
    
    model, tokenizer = load_model_with_quantization(
        args.model_path, device,
        use_quantization=args.use_quantization,
        allow_download=not args.no_download,
    )
    
    # Read input JSONL
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    print(f"\nReading input: {input_path}")
    items = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line.strip()))
    
    print(f"Loaded {len(items)} segments")
    
    # Process each segment
    print("\nComputing logit lengths...")
    processed = []
    verbose_samples = args.verbose_samples
    # Enable verbose if --verbose-samples is specified (even without --verbose)
    show_verbose = args.verbose or (verbose_samples > 0)
    
    if show_verbose:
        print(f"Verbose mode enabled (showing details for {'all' if verbose_samples == 0 else f'first {verbose_samples}'} samples)")
    
    for idx, item in enumerate(tqdm(items, desc="Processing segments")):
        # Determine if we should show verbose logs for this sample
        sample_verbose = show_verbose and (verbose_samples == 0 or idx < verbose_samples)
        processed_item = process_segment(item, model, tokenizer, device, verbose=sample_verbose)
        processed.append(processed_item)
    
    # Determine output path
    if args.output_file:
        output_path = Path(args.output_file)
    else:
        output_path = input_path.parent / f"{input_path.stem}_logit_length{input_path.suffix}"
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in processed:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # Summary
    total = len(processed)
    ok_count = sum(1 for x in processed if x.get("logit_length_computation_ok"))
    max_values = [x.get("logit_length_max") for x in processed if x.get("logit_length_max") is not None]
    avg_logit_length = sum(max_values) / len(max_values) if max_values else None
    
    print(f"\n{'='*60}")
    print("LOGIT LENGTH COMPUTATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total segments:        {total}")
    print(f"Successfully computed:  {ok_count}")
    print(f"Failed/partial:         {total - ok_count}")
    if avg_logit_length is not None:
        print(f"Average logit length:   {avg_logit_length:.6f}")
    print(f"\nOutput saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
