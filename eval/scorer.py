#!/usr/bin/env python3
"""
Pointwise Results Evaluation Script
Read inference JSONL, extract score labels, compare with ground truth, compute metrics and generate report.
"""

import json
import re
import os
import math
import argparse
from datetime import datetime
from pathlib import Path

DATASET_NAME=None

_OVERALL_SCORE_LABEL_PATTERNS = None


def _overall_score_label_patterns():
    """Labeled score patterns ordered for first-match extraction."""
    global _OVERALL_SCORE_LABEL_PATTERNS
    if _OVERALL_SCORE_LABEL_PATTERNS is not None:
        return _OVERALL_SCORE_LABEL_PATTERNS

    score_pattern = r'\d+(?:\.\d+)?'
    num_only = r'\d+'
    _OVERALL_SCORE_LABEL_PATTERNS = [
        # Gemini-style: **Overall Score:** 3 / **Overall Score:** 10/10
        rf'\*\*Overall Score:\*\*\s*({score_pattern})(?:\s*/\s*{score_pattern})?\b',
        rf'\*\*Overall Score:\*\*\s*\[\s*({score_pattern})(?:\s*/\s*{score_pattern})?\s*\]',
        rf'\*\*Overall Score\*\*\s*:\s*({score_pattern})(?:\s*/\s*{score_pattern})?\b',
        rf'\*\*Overall Score\*\*:\s*({score_pattern})(?:\s*/\s*{score_pattern})?\b',
        rf'Overall Score:\s*({score_pattern})\s*/\s*{score_pattern}\b',
        rf'Overall Score:\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        rf'Overall Score:\s*\[\s*({score_pattern})(?:\s*/\s*{score_pattern})?\s*\]',
        rf'Overall Score:\s*\[({score_pattern})\]',
        rf'Overall Score:\s*({score_pattern})\b',
        rf'Final Score:\s*({score_pattern})(?:\s*/\s*{score_pattern})?\b',
        rf'Total Score:\s*({score_pattern})(?:\s*/\s*{score_pattern})?\b',
        rf'(?:An\s+)?overall score of\s+({score_pattern})\s+out of\s+{score_pattern}\b',
        rf'(?:An\s+)?overall score of\s+({score_pattern})\b',
    ]
    return _OVERALL_SCORE_LABEL_PATTERNS


def _extract_first_labeled_score(text: str):
    """Return the earliest explicitly labeled overall score in the response."""
    best = None
    for pattern in _overall_score_label_patterns():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            try:
                score = float(match.group(1))
            except (ValueError, TypeError):
                continue
            if best is None or match.start() < best[0]:
                best = (match.start(), score)
    if best is not None:
        return best[1]
    return None


def extract_score_from_response(response_text):
    """
    Extract score label from response text.
    Supports multiple formats, tries in priority order.

    Args:
        response_text: Response text or dict
    """
    if not response_text:
        return None
    

    
    # Score pattern (supports decimals). Use non-capturing group (?:...) to avoid re.findall returning tuples
    score_pattern = r'\d+(?:\.\d+)?'
    
    # If dict, try to extract choice/score field
    if isinstance(response_text, dict):
        if 'score' in response_text:
            score = str(response_text['score']).strip()
            if re.fullmatch(score_pattern, score):
                return float(score)
        # If has response field, recurse
        if 'response' in response_text:
            return extract_score_from_response(response_text['response'])
    
    # Convert to string
    text = str(response_text)

    labeled_score = _extract_first_labeled_score(text)
    if labeled_score is not None:
        return labeled_score
    
    # Priority 1: Strict labeled score (most reliable, avoids matching problem numbers, step numbers, etc.)
    # e.g. Overall Score: [6] / Overall Score: 6 / **Overall Score: [6]**
    # Also support common markdown formats and fraction-like scores:
    # - **Overall Score:** [13/13] / **Overall Score: 9/10** / Overall Score: **9/10** / Overall Score: **[10/10]**
    # - GPT-5.2-style: Overall Score: **9/10**, Overall Score: 10/10, **Overall Score: [10/10]**
    num_only = r'\d+'  # numerator for fraction (integer)
    patterns_label_strict = [
        # ----- Fraction forms (num/denom): capture numerator; label must be "Overall Score" / "Score" to avoid false hits -----
        rf'Overall Score:\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        rf'Overall Score:\s*\*\*\[\s*({num_only})\s*/\s*\d+\s*\]\*\*',
        rf'\*\*Overall Score:\*\*\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        rf'\*\*Overall Score\*\*:\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        rf'Overall Score:\s*({num_only})\s*/\s*\d+\b',
        rf'\*\*Overall Score\*\*:\s*({num_only})\s*/\s*\d+\b',
        rf'Final Score:\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        rf'Total Score:\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        rf'Score:\s*\*\*\s*({num_only})\s*/\s*\d+\s*\*\*',
        # Markdown/bold label with colon INSIDE bold: **Overall Score:** [13/13]
        rf'\*\*Overall Score:\*\*\s*\[\s*({score_pattern})(?:\s*/\s*{score_pattern})?\s*\]',
        # Markdown/bold label with colon OUTSIDE bold: **Overall Score**: [14/14]
        rf'\*\*Overall Score\*\*\s*:\s*\[\s*({score_pattern})(?:\s*/\s*{score_pattern})?\s*\]',
        # Cases where stars appear before the colon: Overall Score**: [14/14]
        rf'Overall Score\*+\s*:\s*\[\s*({score_pattern})(?:\s*/\s*{score_pattern})?\s*\]',
        # Plain label with bracketed fraction: Overall Score: [14/14]
        rf'Overall Score:\s*\[\s*({score_pattern})(?:\s*/\s*{score_pattern})?\s*\]',

        rf'Overall Score:\s*\[({score_pattern})\]',
        rf'Overall Score:\s*({score_pattern})\b',
        rf'\*\*Overall Score\*\*:\s*\[({score_pattern})\]',
        rf'\*\*Overall Score\*\*:\s*({score_pattern})\b',
        rf'Final Score:\s*\[({score_pattern})\]',
        rf'Final Score:\s*({score_pattern})\b',
        rf'Total Score:\s*\[({score_pattern})\]',
        rf'Total Score:\s*({score_pattern})\b',
        rf'Score:\s*\[({score_pattern})\]',
        rf'Score:\s*({score_pattern})\b',
    ]

    for pattern in patterns_label_strict:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))

    # Priority 2: Standard XML format
    patterns_high_priority = [
        rf'<score>({score_pattern})</score>',  
        rf'<SCORE>({score_pattern})</SCORE>',
        rf'<score>({score_pattern})</score>',
        rf'<total_score>({score_pattern})</total_score>',
        rf'<final_score>({score_pattern})</final_score>',
        rf'<overall_score>({score_pattern})</overall_score>',
        rf'<grade>({score_pattern})</grade>',
        rf'<rating>({score_pattern})</rating>',
        rf'<assessment>({score_pattern})</assessment>',
        rf'<evaluation>({score_pattern})</evaluation>',
        rf'<result>({score_pattern})</result>',
        rf'<final_result>({score_pattern})</final_result>',
        rf'<overall_assessment>({score_pattern})</overall_assessment>',
        rf'<final_assessment>({score_pattern})</final_assessment>',
        rf'<answer>({score_pattern})</answer>',
        rf'<ANSWER>({score_pattern})</ANSWER>',
        rf'<Score>({score_pattern})</Score>',
        rf'<TotalScore>({score_pattern})</TotalScore>',
        rf'<FinalScore>({score_pattern})</FinalScore>',
        rf'<OverallScore>({score_pattern})</OverallScore>',
        rf'<Grade>({score_pattern})</Grade>',
        rf'<Rating>({score_pattern})</Rating>',
        rf'<Assessment>({score_pattern})</Assessment>',
        rf'<Evaluation>({score_pattern})</Evaluation>',
        rf'<Result>({score_pattern})</Result>',
        rf'<FinalResult>({score_pattern})</FinalResult>',
        rf'<OverallAssessment>({score_pattern})</OverallAssessment>',
        rf'<FinalAssessment>({score_pattern})</FinalAssessment>',
    ]
    
    for pattern in patterns_high_priority:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    
    # Priority 3: Standard label format
    patterns_medium_priority = [
        rf'Score:\s*({score_pattern})\b',
        rf'Total Score:\s*({score_pattern})\b',
        rf'Final Score:\s*({score_pattern})\b',
        rf'Overall Score:\s*({score_pattern})\b',
        rf'Grade:\s*({score_pattern})\b',
        rf'Rating:\s*({score_pattern})\b',
        rf'Assessment:\s*({score_pattern})\b',
        rf'Evaluation:\s*({score_pattern})\b',
        rf'Result:\s*({score_pattern})\b',
        rf'Final Result:\s*({score_pattern})\b',
        rf'Overall Assessment:\s*({score_pattern})\b',
        rf'Final Assessment:\s*({score_pattern})\b',
        rf'Score\s*=\s*({score_pattern})\b',
        rf'Total\s*=\s*({score_pattern})\b',
        rf'Grade\s*=\s*({score_pattern})\b',
        rf'Rating\s*=\s*({score_pattern})\b',
        rf'\*\*Score\*\*:\s*({score_pattern})\b',
        rf'\*\*Total Score\*\*:\s*({score_pattern})\b',
        rf'\*\*Final Score\*\*:\s*({score_pattern})\b',
        rf'\*\*Overall Score\*\*:\s*({score_pattern})\b',
        rf'\*\*Grade\*\*:\s*({score_pattern})\b',
        rf'\*\*Rating\*\*:\s*({score_pattern})\b',
        rf'\*\*Assessment\*\*:\s*({score_pattern})\b',
        rf'\*\*Evaluation\*\*:\s*({score_pattern})\b',
        rf'\*\*Result\*\*:\s*({score_pattern})\b',
        rf'\*\*Final Result\*\*:\s*({score_pattern})\b',
        rf'\*\*Overall Assessment\*\*:\s*({score_pattern})\b',
        rf'\*\*Final Assessment\*\*:\s*({score_pattern})\b',
        rf'## Score:\s*({score_pattern})\b',
        rf'## Total Score:\s*({score_pattern})\b',
        rf'## Final Score:\s*({score_pattern})\b',
        rf'## Grade:\s*({score_pattern})\b',
        rf'## Rating:\s*({score_pattern})\b',
        rf'## Assessment:\s*({score_pattern})\b',
        rf'## Evaluation:\s*({score_pattern})\b',
        rf'## Result:\s*({score_pattern})\b',
    ]
    
    for pattern in patterns_medium_priority:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    
    # Priority 4: Bracket format
    patterns_bracket = [
        rf'\(({score_pattern})\)',
        rf'\[({score_pattern})\]',
        rf'"({score_pattern})"',
        rf"'({score_pattern})'",
        rf'「({score_pattern})」',
        rf'『({score_pattern})』',
        rf'【({score_pattern})】',
        rf'《({score_pattern})》',
    ]
    
    for pattern in patterns_bracket:
        matches = re.findall(pattern, text)
        if matches:
            try:
                # Brackets may contain unrelated numbers (problem IDs, step numbers, etc.);
                # use last match as fallback; labeled scores above take priority
                match_val = matches[-1]
                return float(match_val)
            except ValueError:
                continue
    
    # Priority 5: Explicit sentence expressions
    sentence_patterns = [
        rf'(?:score|rating|grade|assessment|evaluation)\s+(?:is|equals?|=\s*)\s*({score_pattern})\b',
        rf'(?:the\s+)?(?:score|rating|grade|assessment|evaluation)\s+(?:is|equals?|=\s*)\s*({score_pattern})\b',
        rf'({score_pattern})\s+(?:points?|score|rating|grade)\b',
        rf'(?:total|final|overall)\s+(?:score|rating|grade)\s+(?:is|equals?|=\s*)\s*({score_pattern})\b',
        rf'(?:I\s+)?(?:give|assign|rate)\s+(?:a\s+)?(?:score|rating|grade)\s+of\s+({score_pattern})\b',
        rf'(?:My\s+)?(?:score|rating|grade|assessment|evaluation)\s+(?:is|equals?|=\s*)\s*({score_pattern})\b',
        rf'(?:This\s+)?(?:response|answer|solution)\s+(?:receives?|gets?|earns?)\s+(?:a\s+)?(?:score|rating|grade)\s+of\s+({score_pattern})\b',
        rf'(?:The\s+)?(?:response|answer|solution)\s+(?:deserves?|merits?)\s+(?:a\s+)?(?:score|rating|grade)\s+of\s+({score_pattern})\b',
        rf'(?:Based\s+on\s+)?(?:my\s+)?(?:evaluation|assessment|analysis),\s+(?:the\s+)?(?:score|rating|grade)\s+(?:is|equals?|=\s*)\s*({score_pattern})\b',
        rf'(?:Therefore|Thus|Hence|So),\s+(?:the\s+)?(?:score|rating|grade)\s+(?:is|equals?|=\s*)\s*({score_pattern})\b',
    ]
    
    for pattern in sentence_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    # Priority 6: Standalone at line start/end
    line_patterns = [
        rf'^({score_pattern})\s*$',
        rf'^({score_pattern})\s*[.:]',
        rf'[.:]\s*({score_pattern})\s*$',
    ]
    
    for line in text.split('\n'):
        for pattern in line_patterns:
            match = re.search(pattern, line.strip())
            if match:
                return float(match.group(1))
    
    # Priority 7: Last standalone score within word boundary
    score_matches = re.findall(rf'\b({score_pattern})\b', text)
    if score_matches:
        try:
            return float(score_matches[-1])
        except (ValueError, IndexError):
            pass
    
    # No fuzzy fallback to avoid false positives
    
    return None



def evaluate_judge_results(jsonl_file_path):
    """
    Evaluate judge task results.
    """
    results = []
    
    # Read JSONL file
    with open(jsonl_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line.strip())
                results.append(item)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}")
                continue
    
    if not results:
        print("No valid results found in the file.")
        return None
    
    # Infer valid score range
    print(f"Inferred valid score range: 0-10")

    # Statistics
    total_samples = len(results)
    correct_predictions = 0
    failed_extractions = 0
    error_samples = 0
    invalid_score_range_count = 0
    
    detailed_results = []
    
    for i, item in enumerate(results):
        sample_result = {
            'sample_id': i + 1,
            'gt': item.get('gt', ''),
            'predicted_score': None,
            'has_error': False,
            'extraction_failed': False,
            'invalid_score_range': False
        }
        
        # Check for errors
        if 'error' in item:
            sample_result['has_error'] = True
            sample_result['error_message'] = item['error']
            error_samples += 1
        else:
            # Extract predicted score
            response = item.get('response', '')
            predicted_score = extract_score_from_response(response)
            
            if predicted_score is None:
                sample_result['extraction_failed'] = True
                sample_result['raw_response'] = str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
                failed_extractions += 1
            else:
                sample_result['predicted_score'] = predicted_score
                gt_raw = item.get('gt', '')
                
                # Pointing Benchmark allows max 25 points
                if predicted_score > 25 or predicted_score < 0:
                    sample_result['invalid_score_range'] = True
                    sample_result['original_predicted_score'] = predicted_score
                    invalid_score_range_count += 1
                    detailed_results.append(sample_result)
                    continue
                
                sample_result['gt'] = gt_raw
                # Skip is_correct for compatibility

        detailed_results.append(sample_result)
    
    # Compute accuracy
    valid_samples = total_samples - error_samples - failed_extractions - invalid_score_range_count
    mse_loss = MSE_LOSS(detailed_results)
    accuracy = round(MSE_TO_SCORE(mse_loss), 2)
    
    # Generate evaluation report
    report = {
        'evaluation_time': datetime.now().isoformat(),
        'input_file': str(jsonl_file_path),
        'dataset_type': DATASET_NAME,
        'summary': {
            'total_samples': total_samples,
            'valid_samples': valid_samples,
            'correct_predictions': correct_predictions,
            'error_samples': error_samples,
            'failed_extractions': failed_extractions,
            'invalid_score_range': invalid_score_range_count,
            'performance_score': accuracy,
            'performance_percentage': f"{accuracy:.2f}%",
            'mse_loss': round(mse_loss, 2)
        },
        'detailed_results': detailed_results
    }
    
    return report




def MSE_LOSS(detailed_results):
    """Compute MSE loss, considering only valid predictions."""
    valid_predictions = []
    for result in detailed_results:
        # Only count samples with valid prediction and ground truth
        if (result.get('predicted_score') is not None and 
            not result.get('has_error', False) and 
            not result.get('extraction_failed', False) and
            not result.get('invalid_score_range', False)):
            
            try:
                gt = float(result['gt'])
                pred = float(result['predicted_score'])
                valid_predictions.append((pred, gt))
            except (ValueError, TypeError):
                continue
    
    if not valid_predictions:
        return float('inf')  # No valid predictions
    
    mse_loss = sum((pred - gt) ** 2 for pred, gt in valid_predictions)
    mse_loss /= len(valid_predictions)
    return mse_loss


def MSE_TO_SCORE(mse_loss, base=2, scale=100):
    """
    Convert MSE to 0-100 score using log function.
    100 = perfect (MSE=0), 0 = very large error.

    Args:
    - mse_loss: Mean squared error
    - base: Log base (default 10, or 2 or e)
    - scale: Score scale factor (default 100)

    Formula: score = scale * (1 - log(1 + mse_loss) / log(1 + max_expected_mse))
    """
    if mse_loss <= 0:
        return scale  # Perfect prediction
    
    # Expected max MSE (adjust as needed)
    max_expected_mse = 25  # ~5 points average error

    # Compute score using log
    log_mse = math.log(1 + mse_loss, base)
    log_max = math.log(1 + max_expected_mse, base)
    
    # Compute score
    score = scale * (1 - log_mse / log_max)
    
    # Clamp to 0-100
    return max(0.0, min(scale, score))


def main():
    parser = argparse.ArgumentParser(description="Evaluate judge task results from JSONL file")
    parser.add_argument("--input-file", type=str, required=True, 
                       help="Path to the input JSONL file containing results")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Output directory for the report (default: same as input file)")
    parser.add_argument("--debug", action="store_true",
                       help="Show detailed debug information for failed extractions")
    parser.add_argument("--show-samples", type=int, default=3,
                       help="Number of sample failures to show in reports (default: 3)")
    parser.add_argument("--dataset_name", type=str, default="judge_benchmark", help="""dataset name:
                        - judge_benchmark
                        - ppe_human_preference
                        """)
        
    args = parser.parse_args()


    DATASET_NAME=args.dataset_name


    if not DATASET_NAME:

        raise ValueError("dataset_name is required")
    


    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist")
        return
    
    print(f"Evaluating results from: {input_file}")
    
    # Evaluate results
    report = evaluate_judge_results(input_file)
    if report is None:
        return
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_file.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed report (RealMath-Eval naming)
    report_file = output_dir / "results_realmath_evaluation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Generate concise text report
    summary_file = output_dir / "results_realmath_evaluation_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("JUDGE TASK EVALUATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Input File: {input_file}\n")
        f.write(f"Evaluation Time: {report['evaluation_time']}\n\n")
        
        f.write("SUMMARY:\n")
        f.write("-" * 30 + "\n")
        summary = report['summary']
        f.write(f"Total Samples: {summary['total_samples']}\n")
        f.write(f"Valid Samples: {summary['valid_samples']}\n")
        f.write(f"Correct Predictions: {summary['correct_predictions']}\n")
        f.write(f"Error Samples: {summary['error_samples']}\n")
        f.write(f"Failed Extractions: {summary['failed_extractions']}\n")
        f.write(f"Invalid Score Range: {summary['invalid_score_range']}\n")
        f.write(f"Performance Score: {summary['performance_percentage']}\n\n")
        
        # Show error samples
        error_samples = [r for r in report['detailed_results'] if r['has_error']]
        if error_samples:
            f.write("ERROR SAMPLES:\n")
            f.write("-" * 30 + "\n")
            for sample in error_samples[:args.show_samples]:
                f.write(f"Sample {sample['sample_id']}: {sample['error_message'][:100]}...\n")
            f.write("\n")
        
        # Show extraction failure samples
        failed_samples = [r for r in report['detailed_results'] if r['extraction_failed']]
        if failed_samples:
            f.write("FAILED EXTRACTION SAMPLES:\n")
            f.write("-" * 30 + "\n")
            for sample in failed_samples[:args.show_samples]:
                f.write(f"Sample {sample['sample_id']}: GT={sample['gt']}\n")
                if args.debug and 'raw_response' in sample:
                    f.write(f"  Raw Response: {sample['raw_response']}\n")
            f.write("\n")
        
        # Show GT format anomaly samples
        invalid_gt_samples = [r for r in report['detailed_results'] if r.get('invalid_gt', False)]
        if invalid_gt_samples:
            f.write("INVALID GROUND TRUTH SAMPLES:\n")
            f.write("-" * 30 + "\n")
            for sample in invalid_gt_samples[:args.show_samples]:
                f.write(f"Sample {sample['sample_id']}: Original GT='{sample.get('original_gt', '')}'\n")
            f.write("\n")
    
    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION COMPLETED")
    print("=" * 60)
    print(f"📊 Performance Score: {report['summary']['performance_score']}")
    print(f"🎛️  MSE_LOSS: {report['summary']['mse_loss']}")
    print(f"❌ Errors: {report['summary']['error_samples']}")
    print(f"⚠️  Failed Extractions: {report['summary']['failed_extractions']}")
    
    # Show GT format anomaly count
    invalid_score_range_count = sum(1 for r in report['detailed_results'] if r.get('invalid_score_range', False))
    if invalid_score_range_count > 0:
        print(f"🔄 Invalid Predicted Score: {invalid_score_range_count}")
    
    print(f"📁 Detailed Report: {report_file}")
    print(f"📄 Summary Report: {summary_file}")
    
    # Show failure samples in debug mode
    if args.debug:
        failed_samples = [r for r in report['detailed_results'] if r['extraction_failed']]
        if failed_samples:
            print(f"\n🔍 DEBUG: First {min(3, len(failed_samples))} failed extraction samples:")
            for i, sample in enumerate(failed_samples[:3]):
                print(f"  Sample {sample['sample_id']}: GT={sample['gt']}")
                if 'raw_response' in sample:
                    print(f"    Response: {sample['raw_response'][:100]}...")
                print()

if __name__ == "__main__":
    main() 