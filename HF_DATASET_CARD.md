---
license: mit
language:
  - en
pretty_name: RealMath-Eval
size_categories:
  - n<1K
tags:
  - llm-as-a-judge
  - math-reasoning
  - education
  - benchmark
  - evaluation
---

# RealMath-Eval

RealMath-Eval is a benchmark for evaluating LLM judges on authentic human mathematical reasoning.

## Repository Links

- arXiv preprint: [XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX) *(replace with final arXiv ID after posting)*
- <img src="GitHub_Mark.png" alt="GitHub" width="16"/> GitHub repository: [RicharMd/RealMath-Eval](https://github.com/RicharMd/RealMath-Eval)
- <img src="hf-logo.png" alt="Hugging Face" width="16"/> Hugging Face dataset: [RicharMd/RealMath-Eval](https://huggingface.co/datasets/RicharMd/RealMath-Eval)


## Dataset Summary

This release contains the processed benchmark and selected derived artifacts used in the paper *RealMath-Eval: The Evaluation Gap in Judging Human Mathematical Reasoning*.

The current Hugging Face dataset includes:

- `realmath_eval.json`: the main processed benchmark containing `224` curated real student solutions.
- `realmath_eval_llm_answer.json`: the synthetic control set containing `219` LLM-generated solutions.
- `realmath_eval_gemini3pro_hard_cases_ge2_style_transferred_72.json`: a style-transfer ablation artifact derived from a `72`-case Gemini 3 Pro hard subset (`\Delta >= 2`).

## Release Scope

This dataset release focuses on the processed benchmark and a small number of released derived artifacts needed to support reproducibility. It does not include the full raw candidate pool from which the benchmark subset was selected, nor raw answer-sheet images.

The main codebase, prompts, scripts, and auxiliary analysis artifacts are maintained in the GitHub repository. In particular, the `64`-case meta-evaluation artifact and additional prompt-conditioned files are released through the repository rather than bundled into the Hugging Face dataset.

## Data Fields

The benchmark JSON files include fields such as:

- `student_id`
- `problem_statement`
- `student_response`
- `reference_answer`
- `gt`
- `question_location`
- `question_type`
- `question_level`

Derived artifacts may additionally include prompt-conditioned text, rewritten responses, or analysis-specific metadata.

## Intended Use

This dataset is intended for:

- benchmarking LLM-as-a-Judge systems on authentic human mathematical reasoning
- comparing judge performance on human versus synthetic solutions
- reproducing the ablation and analysis results reported in the paper

## Limitations

- The benchmark is limited to `14` mathematical problems and `224` processed student solutions.
- The public release includes processed benchmark artifacts rather than the full raw candidate pool.
- The style-transfer file is an auxiliary derived artifact and should not be confused with the core benchmark itself.

## Citation

If you use this dataset, please cite:

```bibtex
@article{realmath_eval_2026,
  title={RealMath-Eval: Why SOTA Judges Struggle with Real Human Reasoning},
  author={Yiteng Mao and Kenan Xu and Yijia Lyu and Wenhao Li and Jianlong Chen and Xiangfeng Wang},
  journal={arXiv preprint},
  year={2026}
}
```
