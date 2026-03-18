# RealMath-Eval: The Evaluation Gap in Judging Human Mathematical Reasoning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**RealMath-Eval** is a rigorous benchmark designed to evaluate the capability of Large Language Models (LLMs) to judge authentic human mathematical reasoning.

This repository contains the official implementation and data for the paper:  
**"RealMath-Eval: The Evaluation Gap in Judging Human Mathematical Reasoning"**

> **Abstract:** While LLMs have achieved near-perfect performance in *solving* math problems, their ability to *evaluate* diverse human reasoning remains unproven. Our research identifies a stark **"Evaluation Gap"**: SOTA judges (e.g., Gemini 3 Pro, GPT-5) are remarkably accurate on synthetic LLM text (MSE ~1.17) but struggle significantly with real student solutions (MSE ~2.96). Through semantic embedding and generative probability probes, we reveal that this is due to a "Structural Collapse" in synthetic data versus the high-entropy "Cloud" of human thought.

## 🏗️ Codebase Origin: MASLab

This project is built upon **[MASLab](https://github.com/Unified-MAS/MASLab)** (Multi-Agent System Laboratory), a unified and comprehensive codebase for LLM-based multi-agent systems. We leverage MASLab's modular architecture to implement our Chain-of-Thought (CoT) judges and evaluation protocols.

## 📂 Repository Structure

The repository is organized to support the reproduction of the main benchmark results and the deep analytical probes described in the paper.

```text
RealMath-Eval/
├── data/                       # 📊 Benchmark Datasets
│   ├── realmath_eval.json                 # [Main] Real Student Responses (N=224)
│   ├── realmath_eval_llm_answer.json      # [Control] Synthetic LLM Responses (N=219)
│   ├── realmath_eval_style_transfer.json   # [Ablation] Style-Normalized Human Data
│   ├── VF_realmath_eval.json              # [Robustness] Verification-First Prompting Data
│   └── meta_eval_data.json                 # [Analysis] Meta-Evaluation Attribution Data
├── methods/                    # 🤖 Judge Implementations (based on MASLab)
│   ├── cot/                    # Chain-of-Thought Judge (Baseline)
│   └── ...
├── scripts/
│   ├── windows/run/            # PowerShell scripts (judge_realmath_eval.ps1, etc.)
│   └── linux/run/              # Bash scripts (judge_realmath_eval.sh, etc.)
├── analysis/                   # 🔬 Analytical Probes (Section 5)
│   ├── macro_embedding/        # "The Crystal vs The Cloud" (Embedding & Clustering)
│   ├── micro_probability/      # "Generative Surprisal" (Logit Probability)
│   └── analyze_results.py      # Basic Metrics (MSE, Failure Rate)
├── eval/                       # 📝 Scoring Scripts
│   └── scorer.py               # Robust Score Extraction & Calculation
├── assets/                     # 🖼️ Paper Figures (Heatmaps, PCA, etc.)
├── inference.py                # 🚀 Main Entry Point (from MASLab)
└── requirements.txt            # Dependencies
```

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

#### 3.1 Main Evaluation Gap (Table 1 & 2)

**Option A: Scripts**

*Windows (PowerShell):*
```powershell
.\scripts\windows\run\judge_realmath_eval.ps1 -method vanilla -model gemini-3-pro-preview
.\scripts\windows\run\judge_realmath_eval.ps1 -dataset_name realmath_eval_llm_answer -method vanilla -model gemini-3-pro-preview
.\scripts\windows\run\judge_realmath_eval.ps1 -max_samples 1  # quick test
```

*Linux (Bash):*
```bash
chmod +x scripts/linux/run/*.sh
./scripts/linux/run/judge_realmath_eval.sh realmath_eval realmath_eval vanilla gemini-3-pro-preview 0
./scripts/linux/run/judge_realmath_eval.sh realmath_eval_llm_answer realmath_eval vanilla gemini-3-pro-preview 0
./scripts/linux/run/judge_realmath_eval.sh realmath_eval realmath_eval vanilla gemini-3-pro-preview 1  # quick test
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
```

#### 3.2 Style Transfer (Section 4 Ablation)

*Windows:* `.\scripts\windows\run\judge_style_transfer.ps1`

*Linux:* `./scripts/linux/run/judge_style_transfer.sh`

Uses `realmath_eval_style_transfer.json`, CoT method; then runs `extract_style_transfer_response.py`.

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
python inference.py --method_name cot --model_name gpt-4o-mini --test_dataset_name meta_eval_data --output_path outputs/realmath_eval/meta_eval_results.jsonl
```

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
```

*   **Input**: `clustering_final_human.jsonl`, `clustering_segments_review_llm.jsonl` (in `analysis/macro_embedding/`)
*   **Output**: Heatmaps, PCA plots, Silhouette scores (saved to `--output-dir`).

### Micro-Level: Generative Surprisal
Measure the information-theoretic "surprise" of human reasoning steps (Section 5.2).

```bash
python analysis/micro_probability/compute_metrics.py \
  --input-file path/to/results_step_extracted.jsonl \
  --model-path Qwen/Qwen3-8B \
  --use-quantization  # optional, for 4-bit if GPU memory limited
```

*   **Method**: Computes the Logical Likelihood (LL) of the ground-truth next step given the context.
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
