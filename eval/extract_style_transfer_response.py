#!/usr/bin/env python3
"""
Style Transfer Response Extraction Script
Read style transfer inference JSONL, extract rewritten student responses, and write new JSONL.
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime


def extract_rewritten_response(response_text):
    """
    Extract rewritten student response from LLM response text.
    Simplified: use response field directly since prompt asks for rewritten answer only.

    Args:
        response_text: LLM response text or dict

    Returns:
        Rewritten text, or None if empty
    """
    if not response_text:
        return None
    
    # If dict, try to get response field
    if isinstance(response_text, dict):
        if 'response' in response_text:
            response_text = response_text['response']
        elif 'rewritten_response' in response_text:
            return response_text['rewritten_response']
        else:
            return None
    
    # Convert to string and strip
    text = str(response_text).strip()
    
    # Return None if empty
    if not text:
        return None
    
    # Return full response; prompt asks for "Output ONLY the rewritten solution text"
    return text


def extract_style_transfer_responses(jsonl_file_path, output_file_path=None):
    """
    Extract rewritten student responses from style transfer inference results.

    Args:
        jsonl_file_path: Input JSONL path (LLM responses to style transfer prompt)
        output_file_path: Output JSONL path (auto-generated if None)

    Returns:
        Dict with extraction stats
    """
    input_path = Path(jsonl_file_path)
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        return None
    
    # Determine output path
    if output_file_path is None:
        output_path = input_path.parent / f"{input_path.stem}_extracted_rewritten.jsonl"
    else:
        output_path = Path(output_file_path)
    
    results = []
    stats = {
        'total_samples': 0,
        'successful_extractions': 0,
        'failed_extractions': 0,
        'error_samples': 0,
    }
    
    # Read input JSONL
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            stats['total_samples'] += 1
            
            try:
                item = json.loads(line.strip())
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}")
                stats['error_samples'] += 1
                continue
            
            # Extract rewritten response
            response = item.get('response', '')
            rewritten_response = extract_rewritten_response(response)
            
            # Build output item, order fields for comparison
            output_item = {}
            
            # Base fields
            output_item['query'] = item.get('query', '')
            output_item['problem_statement'] = item.get('problem_statement', '')
            output_item['reference_answer'] = item.get('reference_answer', '')
            
            # Original and rewritten responses
            output_item['student_response'] = item.get('student_response', '')
            if rewritten_response is None:
                output_item['rewritten_response'] = None
                output_item['extraction_failed'] = True
                output_item['raw_response_preview'] = str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
                stats['failed_extractions'] += 1
            else:
                output_item['rewritten_response'] = rewritten_response
                output_item['extraction_failed'] = False
                stats['successful_extractions'] += 1
            
            # Scoring fields
            output_item['gt'] = item.get('gt')
            output_item['sub_question_scores'] = item.get('sub_question_scores', {})
            output_item['full_score'] = item.get('full_score', 0)
            
            # Metadata fields
            output_item['student_id'] = item.get('student_id', '')
            output_item['question_location'] = item.get('question_location', '')
            output_item['question_type'] = item.get('question_type', '')
            output_item['question_level'] = item.get('question_level', '')
            output_item['task_description'] = item.get('task_description', '')
            output_item['source'] = item.get('source', 'style_transfer')
            output_item['tag'] = item.get('tag', [])
            
            # Keep raw response for debugging
            output_item['response'] = item.get('response', '')
            
            results.append(output_item)
    
    # Write output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n{'='*60}")
    print("EXTRACTION COMPLETED")
    print(f"{'='*60}")
    print(f"📊 Total Samples: {stats['total_samples']}")
    print(f"✅ Successful Extractions: {stats['successful_extractions']}")
    print(f"❌ Failed Extractions: {stats['failed_extractions']}")
    print(f"⚠️  Error Samples: {stats['error_samples']}")
    print(f"📁 Output File: {output_path}")
    
    # Show failed samples
    failed_items = [r for r in results if r.get('extraction_failed', False)]
    if failed_items:
        print(f"\n🔍 First 3 failed extraction samples:")
        for i, item in enumerate(failed_items[:3]):
            print(f"  Sample {i+1}:")
            if 'raw_response_preview' in item:
                print(f"    Raw Response: {item['raw_response_preview']}")
            print()
    
    return {
        'stats': stats,
        'output_file': str(output_path),
        'total_items': len(results)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract rewritten student responses from style transfer inference results"
    )
    parser.add_argument(
        "--input-file", 
        type=str, 
        required=True,
        help="Path to the input JSONL file containing style transfer inference results"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Path to the output JSONL file (default: <input_stem>_extracted_rewritten.jsonl)"
    )
    parser.add_argument(
        "--show-failed",
        type=int,
        default=3,
        help="Number of failed extraction samples to show (default: 3)"
    )
    
    args = parser.parse_args()
    
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist")
        return
    
    print(f"Extracting rewritten responses from: {input_file}")
    
    result = extract_style_transfer_responses(
        jsonl_file_path=input_file,
        output_file_path=args.output_file
    )
    
    if result:
        print(f"\n✅ Extraction completed successfully!")
        print(f"📁 Output saved to: {result['output_file']}")


if __name__ == "__main__":
    main()
