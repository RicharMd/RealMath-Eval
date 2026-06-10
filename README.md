# RealMath-Eval: The Evaluation Gap in Judging Human Mathematical Reasoning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**RealMath-Eval** is a rigorous benchmark designed to evaluate the capability of Large Language Models (LLMs) to judge authentic human mathematical reasoning.

This repository contains the official implementation and data for the paper:  
**"RealMath-Eval: The Evaluation Gap in Judging Human Mathematical Reasoning"**

Release scope: this repository releases the processed benchmark and analysis artifacts used in the paper, including the curated `224` real student solutions, the `224` synthetic control solutions, and the derived files used in the ablation and probe analyses. It does not include the full raw candidate pool from which the benchmark subset was selected. For public release, the core benchmark JSON files are the main dataset artifacts, while prompt-conditioned robustness variants and meta-evaluation artifacts are auxiliary reproducibility materials.

## Links

- [arXiv preprint] : [arXiv:2606.10254](https://arxiv.org/abs/2606.10254)
- <img src="hf-logo.png" alt="Hugging Face" width="16"/> Hugging Face dataset: [RicharMd/RealMath-Eval](https://huggingface.co/datasets/RicharMd/RealMath-Eval)

The GitHub repository is the primary home for code, prompts, scripts, and auxiliary analysis artifacts. The Hugging Face dataset hosts the core benchmark files together with selected released derived data artifacts.

> **Abstract:** While LLMs have achieved near-perfect performance in *solving* math problems, their ability to *evaluate* diverse human reasoning remains unproven. Our research identifies a stark **"Evaluation Gap"**: SOTA judges (e.g., Gemini 3 Pro, GPT-5) are remarkably accurate on synthetic LLM text (MSE ~1.17) but struggle significantly with real student solutions (MSE ~2.96). Through semantic embedding and generative probability probes, we reveal that this is due to a "Structural Collapse" in synthetic data versus the high-entropy "Cloud" of human thought.

## 🏗️ Codebase Origin: MASLab

This project is built upon **[MASLab](https://github.com/Unified-MAS/MASLab)** (Multi-Agent System Laboratory), a unified and comprehensive codebase for LLM-based multi-agent systems. We leverage MASLab's modular architecture to implement our Chain-of-Thought (CoT) judges and evaluation protocols.

## 📂 Repository Structure

The repository is organized to support the reproduction of the main benchmark results and the deep analytical probes described in the paper.

```text
RealMath-Eval/
├── data/                       # 📊 Benchmark Datasets
│   ├── realmath_eval.json                 # [Main] Real Student Responses (N=224)
│   ├── realmath_eval_llm_answer.json      # [Control] Synthetic LLM Responses (N=224)
│   ├── realmath_eval_gemini3pro_hard_cases_ge2_style_transfer_input_72.json
│   │                                      # [Ablation Input] 72 Gemini 3 Pro hard cases used as style-transfer inputs
│   ├── realmath_eval_gemini3pro_hard_cases_ge2_style_transferred_72.json
│   │                                      # [Ablation Output] 72 style-transferred hard cases used in the style ablation
│   ├── VF_realmath_eval.json              # [Robustness] Verification-First Prompting Data
│   ├── realmath_eval_fewshot.json         # [Few-Shot] 196 eval items (224 − 28 hold-out demos)
│   ├── realmath_eval_fewshot_manifest.json # Build manifest for the few-shot set
│   ├── realmath_eval_llm_answer_fewshot.json      # [Few-Shot] Same setup on synthetic LLM answers (196 items)
│   ├── realmath_eval_llm_answer_fewshot_manifest.json
│   └── realmath_eval_gemini3pro_hard_cases_ge2_meta_eval_input_64.json
│                                          # [Analysis Input] 64-case prompt-ready meta-evaluation task file
├── methods/                    # 🤖 Judge Implementations (based on MASLab)
│   ├── cot/                    # Chain-of-Thought Judge (Baseline)
│   └── ...
├── scripts/
│   ├── windows/run/            # PowerShell scripts (judge_realmath_eval.ps1, etc.)
│   └── linux/run/              # Bash scripts (judge_realmath_eval.sh, etc.)
├── analysis/                   # 🔬 Analytical Probes (Section 5)
│   ├── data/error_segment_bundle/  # Error segments + step splits (macro & micro inputs)
│   ├── macro_embedding/        # "The Crystal vs The Cloud" (Embedding & Clustering)
│   ├── meta_eval/             # Meta-evaluation result artifacts for the 64-case analysis
│   ├── micro_probability/      # "Generative Surprisal" (Logical Likelihood / LL)
│   ├── analyze_results.py      # Basic Metrics (MSE, Failure Rate)
│   └── requirements_analysis.txt
├── eval/                       # 📝 Scoring Scripts
│   └── scorer.py               # Robust Score Extraction & Calculation
├── assets/                     # 🖼️ Paper Figures (Heatmaps, PCA, etc.)
├── inference.py                # 🚀 Main Entry Point (from MASLab)
└── requirements.txt            # Dependencies
```

## Public Release Layout

For public release, we distinguish between core benchmark files and auxiliary reproducibility artifacts.

- Core benchmark files:
  - `realmath_eval.json`
  - `realmath_eval_llm_answer.json`
- Released derived artifact currently mirrored on Hugging Face:
  - `realmath_eval_gemini3pro_hard_cases_ge2_style_transferred_72.json`
- Auxiliary reproducibility artifacts kept in the GitHub repository:
  - `realmath_eval_gemini3pro_hard_cases_ge2_style_transfer_input_72.json`
  - `realmath_eval_gemini3pro_hard_cases_ge2_meta_eval_input_64.json`
  - `analysis/meta_eval/realmath_eval_gemini3pro_hard_cases_ge2_meta_eval_labels_64.json`

The `72`-case style-transfer set and the `64`-case meta-evaluation set are distinct Gemini 3 Pro hard-case subsets released separately rather than as a single pooled split.

## 🚀 Quick Start

### 1. Installation

**Option A: pip**
```bash
pip install -r requirements.txt
```

**Option B: conda**
```bash
conda env create -f environment.yml
conda activate realmath-eval  # or the env name specified in environment.yml
```

**Windows users:** Set UTF-8 encoding before running Python (e.g., in PowerShell):
```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

### 2. Configuration (MASLab Style)

Configure your model endpoints and API keys in `model_api_configs/model_api_config.json`. 
The checked-in config file is a placeholder template only. Replace the placeholder values locally with your own credentials, and do not commit real API keys.
Example format:

```json
"gpt-4o-mini": {
    "model_list": [
        {"model_name": "gpt-4o-mini", "model_url": "https://api.openai.com/v1", "api_key": "sk-..."}
    ],
    "max_workers_per_model": 10
}
```

### 3. Reproducing Experiments

All scripts write to `outputs/realmath_eval/{method}/{model}/{timestamp}/`. Run from the RealMath-Eval root directory.
Generated files under `outputs/` and `results/` are not part of the benchmark release package and should be reproduced locally.

#### 3.1 Main Evaluation Gap (Table 1 & 2)

**Option A: Scripts**

*Windows (PowerShell):*
```powershell
.\scripts\windows\run\judge_realmath_eval.ps1 -method cot -model gemini-3-pro-preview
.\scripts\windows\run\judge_realmath_eval.ps1 -dataset_name realmath_eval_llm_answer -method cot -model gemini-3-pro-preview
.\scripts\windows\run\judge_realmath_eval.ps1 -max_samples 1  # quick test
```

*Linux (Bash):*
```bash
chmod +x scripts/linux/run/*.sh
./scripts/linux/run/judge_realmath_eval.sh realmath_eval realmath_eval cot gemini-3-pro-preview 0
./scripts/linux/run/judge_realmath_eval.sh realmath_eval_llm_answer realmath_eval cot gemini-3-pro-preview 0
./scripts/linux/run/judge_realmath_eval.sh realmath_eval realmath_eval cot gemini-3-pro-preview 1  # quick test
# Args: dataset_name output_bucket method model max_samples
```

**Option B: Direct Python**

```bash
# Human data
python inference.py --method_name cot --model_name gpt-4o-mini --test_dataset_name realmath_eval --output_path outputs/realmath_eval/human_results.jsonl

# Synthetic data
python inference.py --method_name cot --model_name gpt-4o-mini --test_dataset_name realmath_eval_llm_answer --output_path outputs/realmath_eval/synthetic_results.jsonl

# Calculate MSE
python eval/scorer.py --input-file outputs/realmath_eval/human_results.jsonl
python eval/scorer.py --input-file outputs/realmath_eval/synthetic_results.jsonl

# Score-difference breakdown (same role as analyze_score_differences.py)
python analysis/analyze_results.py --report outputs/realmath_eval/cot/gemini-3-pro-preview/<timestamp>/results_realmath_evaluation_report.json
```

After **Option A** (judge script), `eval/scorer.py` runs automatically; then run:

```bash
python analysis/analyze_results.py --report outputs/realmath_eval/cot/<model>/<timestamp>/results_realmath_evaluation_report.json
```

#### 3.2 Style Transfer (Section 4 Ablation)

*Windows:* `.\scripts\windows\run\judge_style_transfer.ps1`

*Linux:* `./scripts/linux/run/judge_style_transfer.sh`

Uses `realmath_eval_gemini3pro_hard_cases_ge2_style_transfer_input_72.json`, CoT method; then runs `extract_style_transfer_response.py` to produce the corresponding style-transferred file.

#### 3.3 Robustness: Verification First (Section 4)

*Windows:* `.\scripts\windows\run\judge_realmath_eval.ps1 -dataset_name VF_realmath_eval -method vanilla -model gemini-3-pro-preview`

*Linux:* `./scripts/linux/run/judge_realmath_eval.sh VF_realmath_eval realmath_eval vanilla gemini-3-pro-preview 0`

#### 3.4 Robustness: Follow-Through First (Section 4)

*Windows:* `.\scripts\windows\run\judge_realmath_eval.ps1 -dataset_name write_through_first_realmath_eval -method vanilla -model gemini-3-pro-preview`

*Linux:* `./scripts/linux/run/judge_realmath_eval.sh write_through_first_realmath_eval realmath_eval vanilla gemini-3-pro-preview 0`

#### 3.5 Meta-Evaluation (Attribution Analysis)

Requires prior inference results. Run inference on `realmath_eval` first, then:

*Windows:* `.\scripts\windows\run\judge_meta_eval.ps1` (if implemented)

*Linux:* `./scripts/linux/run/judge_meta_eval.sh cot gemini-3-pro-preview`

*Direct Python:*
```bash
python inference.py --method_name cot --model_name gpt-4o-mini --test_dataset_name realmath_eval_gemini3pro_hard_cases_ge2_meta_eval_input_64 --output_path outputs/realmath_eval/meta_eval_results.jsonl
```

The file `data/realmath_eval_gemini3pro_hard_cases_ge2_meta_eval_input_64.json` is a prompt-ready task input for the attribution pipeline rather than part of the main benchmark release. The finalized category assignments used in the paper are stored separately as analysis artifacts under `analysis/meta_eval/realmath_eval_gemini3pro_hard_cases_ge2_meta_eval_labels_64.json`.

#### 3.6 Few-Shot Calibration Set (`realmath_eval_fewshot.json`)

Derived from `realmath_eval.json` (224 items) **without modifying the source file**.

- **196** evaluation items = 224 − **28** hold-out calibration demos (14 problems × 1 GOOD + 1 WEAK pair each).
- Hold-out demos are **not** separate rows in the few-shot file; they appear inside each item's `query` as calibration examples with gold scores.
- **`realmath_eval_fewshot_manifest.json`** records hold-out `source_index` values and per-problem high/mid `gt` pairs.

**Construction** (run from the parent `lean_eval` repo):

1. Stratified demo selection → `rebuttal_annotation/data/score_stratified_samples.json`  
   (script: `rebuttal_annotation/extract_score_stratified_samples.py`; percentile-based high/mid pick per `problem_statement`).
2. Build few-shot JSON:

```powershell
python datasets/build_judge_dataset.py `
  --input-file RealMath-Eval/data/realmath_eval.json `
  --output-name realmath_eval_fewshot `
  --dataset_name pointing_benchmark_fewshot `
  --stratified-file rebuttal_annotation/data/score_stratified_samples.json `
  --output-file RealMath-Eval/data/realmath_eval_fewshot.json
```

Each evaluation item's `query` contains: GOOD example + WEAK example (same problem, with `gt`) → reference rubric → target `student_response` to score.

The synthetic control corpus has a parallel few-shot set, `realmath_eval_llm_answer_fewshot.json` (196 items, built from `realmath_eval_llm_answer.json` with the same calibration demos; see `realmath_eval_llm_answer_fewshot_manifest.json`).

## 🔬 Deep Analysis (Section 5)

These scripts run on a **remote GPU machine**; the main benchmark (API-based) does not require them locally.

### Setup (Remote Machine)

Install analysis-specific dependencies (not in main `requirements.txt`):

```bash
pip install -r analysis/requirements_analysis.txt
```

Or with conda: `conda create -n realmath-analysis python=3.10 && conda activate realmath-analysis && pip install -r analysis/requirements_analysis.txt`

**Models**: Both scripts auto-download from HuggingFace on first run if the model path does not exist locally. To use a pre-downloaded model, pass `--model-path /path/to/model`.

| Script | Model | Size | HuggingFace ID |
|--------|-------|------|----------------|
| run_analysis.py | Embedding | ~16GB | `Qwen/Qwen3-Embedding-8B` |
| compute_metrics.py | Causal LM | ~16GB | `Qwen/Qwen3-8B` |

For `compute_metrics.py`, use `--use-quantization` for 4-bit loading if GPU memory is limited.

### Macro-Level: "The Crystal vs. The Cloud"
Analyze the semantic geometry of error types using embeddings (Section 5.1).

```bash
cd analysis/macro_embedding
python run_analysis.py --model-path Qwen/Qwen3-Embedding-8B --output-dir ../../assets
# Or use local path: --model-path /path/to/Qwen-Qwen3-Embedding-8B
# Default --data-dir: ../data/error_segment_bundle (human_error_segments.jsonl, llm_error_segments.jsonl)
```

*   **Input** (default): `analysis/data/error_segment_bundle/human_error_segments.jsonl`, `llm_error_segments.jsonl`
*   **Output**: Heatmaps, PCA plots, Silhouette scores (saved to `--output-dir`).

### Micro-Level: Generative Surprisal
Measure the information-theoretic "surprise" of human reasoning steps via Logical Likelihood (LL) (Section 5.2).

```bash
python analysis/micro_probability/compute_metrics.py \
  --model-path Qwen/Qwen3-8B \
  --use-quantization  # optional, for 4-bit if GPU memory limited
# Override input: --input-file analysis/data/error_segment_bundle/human_error_steps_step_split.jsonl
```

*   **Input** (default): `analysis/data/error_segment_bundle/human_error_steps_step_split.jsonl` (must include `steps` field)
*   **Method**: Computes the Logical Likelihood (LL) of the ground-truth next step given the context.
*   **Output**: Writes JSONL with `logical_likelihoods` and `logical_likelihood_max` fields. Legacy `logit_length` aliases are still included for backward compatibility.
*   **Note**: Use `--no-download` to require a local model path only (no HuggingFace download).

## 📄 Citation

If you use RealMath-Eval in your research, please cite our paper:

```bibtex
@article{realmath_eval_2026,
  title={RealMath-Eval: The Evaluation Gap in Judging Human Mathematical Reasoning},
  author={RealMath-Eval Team},
  journal={arXiv preprint},
  year={2026}
}
```

Please also cite the underlying **MASLab** framework:

```bibtex
@article{ye2025maslab,
  title={MASLab: A Unified and Comprehensive Codebase for LLM-based Multi-Agent Systems},
  author={Ye, Rui and Huang, Keduan and Wu, Qimin and Cai, Yuzhu and Jin, Tian and Pang, Xianghe and Liu, Xiangrui and Su, Jiaqi and Qian, Chen and Tang, Bohan and others},
  journal={arXiv preprint arXiv:2505.16988},
  year={2025}
}
```
