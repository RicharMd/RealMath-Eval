#!/usr/bin/env python3
"""
Build Judge Benchmark Dataset for MASLab
Based on compare.py format and lean judge instructions
"""

import json
import os
import argparse
from pathlib import Path
import time
import random


WRITE_THROUGH_FIRST_INSTRUCTION="""
You are an expert mathematics evaluator tasked with scoring student responses to mathematical problems.

TASK:
- Evaluate a complete student answer against a reference answer with detailed scoring rubrics
- Provide an overall score for the student's response
- Give brief explanations for your scoring decisions

EVALUATION CRITERIA:
1. Mathematical Accuracy: Correctness of mathematical concepts, formulas, and calculations
2. Solution Approach: Logical reasoning and problem-solving methodology
3. Completeness: Whether the student addressed all required parts of the problem
4. Clarity: How well the solution is presented and explained

INPUT FORMAT:
- Reference Answer: Contains the correct solution with detailed step-by-step scoring rubrics using cumulative scoring (e.g., "------3 points" means all steps up to that point are correct and the student earns 3 points)
- Problem Statement: The complete mathematical problem (not broken into sub-questions)
- Student Response: The complete student's answer (not broken into sub-questions)

SCORING PROCESS:
1. If the student response is incomplete or unclear, first attempt a follow-through continuation based on the student's written logic (to understand intent and progress).
2. Compare the student's approach with the reference solution (use follow-through only as an aid for interpretation, not as a substitute for the student's work).
3. Identify which key mathematical steps were correctly executed by the student.
4. Check for major conceptual errors or missing components.
5. Award partial credit based on how far the student's own work progressed correctly (do not award full credit just because the follow-through can finish the problem).
6. Provide an overall score that reflects the student's performance (the highest cumulative score they achieved).

FOLLOW-THROUGH POLICY (IMPORTANT):
- If the student response is incomplete, unclear, or you cannot fully understand it at first glance, you must NOT stop early.
- First, attempt a "follow-through" continuation: infer the student's intended approach from what they wrote, then continue their reasoning in the same direction to reach a completed solution attempt (make the smallest reasonable assumptions, and do not introduce a totally different method unless the student's method is impossible).
- Then perform the pointing/scoring task: score based on what the student actually demonstrated (their correct steps, ideas, and progress), using the reference rubric; do not give full credit just because your follow-through can finish the problem.
- If multiple interpretations are possible, choose the most charitable interpretation consistent with the student's text, and briefly note the ambiguity in your explanation.

OUTPUT FORMAT:
- Overall Score: [X] where X is the score awarded
- Brief Explanation: 2-3 sentences explaining the main strengths and weaknesses of the student's response
- Key Observations: Highlight any significant mathematical insights or errors



Remember: Focus on mathematical understanding rather than formatting. Award credit for correct mathematical reasoning even if presentation could be improved.



Now, please evaluate the following:


Problem Statement: {problem_statement}

Student Response: {student_response}

Reference Answer: {reference_answer}


Please provide your evaluation:
"""


STYLE_TRANSFER_INSTRUCTION = """
You are a style normalizer tasked with rewriting student mathematical solutions into a standardized format.

TASK:
- Rewrite the student's solution text into a standardized, textbook-like format
- Preserve ALL mathematical and logical content exactly as written (including errors, incomplete steps, and reasoning)
- Change ONLY the surface presentation (formatting, structure labels, wording style)

CRITICAL CONSTRAINTS:
- You are given ONLY the student's solution text; no problem statement is provided
- Do NOT infer, correct, or complete the solution based on any external knowledge
- Do NOT add missing steps or remove existing steps
- Do NOT change any mathematical meaning, correctness, or logical structure
- If the student's answer is wrong or incomplete, keep it wrong or incomplete in the output

WHAT TO PRESERVE (CONTENT - DO NOT CHANGE):
- Every reasoning step exactly as written
- All mathematical expressions, formulas, and calculations (even if incorrect)
- All shortcuts, omissions, and incomplete parts
- All conclusions and final answers (right or wrong)
- The logical flow and sequence of steps

WHAT TO CHANGE (PATTERN - ONLY THESE):
1. Formatting:
   - Convert all mathematical expressions to standard LaTeX notation
   - Normalize notation (e.g., unify variable names if the same variable appears in different forms, but only if it does not change meaning)
   - Improve spacing and line breaks for readability

2. Structure:
   - Add explicit step labels ("Step 1:", "Step 2:", ...) at natural break points in the existing reasoning
   - Do NOT create new steps; only label existing logical segments
   - Preserve any existing sub-question markers (e.g., "(1)", "(2)") if present

3. Wording Style:
   - Convert informal or colloquial language to formal, textbook-like tone
   - Use standard mathematical phrasing (e.g., "We have", "Therefore", "It follows that", "Hence")
   - Replace vague expressions with precise mathematical language (without changing the propositional meaning)
   - Standardize connectors and transitions

INPUT FORMAT:
- Student Response: The complete student's answer text (no problem statement provided)

REWRITING PROCESS:
1. Read the student's solution carefully to understand their reasoning path (do not evaluate correctness).
2. Identify natural break points where step labels can be inserted without creating new steps.
3. Rewrite each segment:
   - Convert math to LaTeX
   - Adjust wording to formal style
   - Preserve all mathematical content and logical structure
4. Ensure the output maintains the same sequence, completeness, and correctness as the input.

OUTPUT FORMAT:
- Output ONLY the rewritten solution text
- Do NOT include any commentary, explanations, or meta-text
- Do NOT include phrases like "The student wrote:" or "Original solution:"
- The output should be a standalone, polished version that preserves all original content

EXAMPLE TRANSFORMATION (for reference only - style, not content):
Before: "So we calculate, since x=1, then f(1)=2+3=5"
After: "Step 2: We now compute. Since x = 1, it follows that f(1) = 2 + 3 = 5."

Note: In the example above, the mathematical content (x=1, f(1)=2+3=5) is preserved exactly; only the language style, formatting, and structure labels changed.

Now, please rewrite the following student response:

Student Response: {student_response}

Rewritten Solution:
"""


VF_POINTING_INSTRUCTION="""
You are an expert mathematics evaluator tasked with scoring student responses to mathematical problems.

TASK:
- **STEP 1: VERIFICATION (CRITICAL)**: Before scoring, you must explicitly verify the student's response step-by-step against the problem statement and reference answer. Check for calculation errors, logical gaps, and validity of alternative methods.
- **STEP 2: SCORING**: Evaluate the complete student answer against the reference answer with detailed scoring rubrics based on your verification.
- Provide an overall score for the student's response.
- Give brief explanations for your scoring decisions.

EVALUATION CRITERIA:
1. Mathematical Accuracy: Correctness of mathematical concepts, formulas, and calculations
2. Solution Approach: Logical reasoning and problem-solving methodology
3. Completeness: Whether the student addressed all required parts of the problem
4. Clarity: How well the solution is presented and explained

INPUT FORMAT:
- Reference Answer: Contains the correct solution with detailed step-by-step scoring rubrics using cumulative scoring (e.g., "------3 points" means all steps up to that point are correct and the student earns 3 points)
- Problem Statement: The complete mathematical problem (not broken into sub-questions)
- Student Response: The complete student's answer (not broken into sub-questions)

SCORING PROCESS:
1. **[Verification Phase]** meticulously check the student's derivation. Identify where the first error occurs (if any) and whether subsequent steps are logically consistent (follow-through).
2. Compare the student's approach with the reference solution.
3. Identify which key mathematical steps were correctly executed.
4. Check for major conceptual errors or missing components.
5. Award partial credit for partially correct solutions based on how far the student progressed correctly.
6. Provide an overall score that reflects the student's performance (the highest cumulative score they achieved).

OUTPUT FORMAT:
- Verification Analysis: [Your step-by-step verification of the student's work]
- Overall Score: [X] where X is the score awarded
- Brief Explanation: 2-3 sentences explaining the main strengths and weaknesses of the student's response
- Key Observations: Highlight any significant mathematical insights or errors



Remember: Focus on mathematical understanding rather than formatting. Award credit for correct mathematical reasoning even if presentation could be improved.



Now, please evaluate the following:


Problem Statement: {problem_statement}

Student Response: {student_response}

Reference Answer: {reference_answer}


Please provide your evaluation:
"""

META_EVALUATION_INSTRUCTION="""
You are an expert "Meta-Evaluator" for mathematical reasoning. Your goal is to analyze the discrepancy between a **Ground Truth Score (GT)** (assigned by a human expert based on a strict rubric) and a **Model Score** (assigned by an LLM judge).

Here is the specific case you need to analyze:

================ CASE DATA ================

[Problem Statement]:
{problem_statement}

[Rubric / Reference Answer]:
{reference_answer}

[Student Response]:
{student_response}

[Ground Truth Score (GT)]: {gt}

[Model Evaluation (including score and reasoning)]:
{response}

===========================================

### Task
Determine the **root cause** of the score difference (Model Score - GT Score) and classify it into one of the following 5 categories.

### Classification Categories

**A. Error Severity & Follow-through (Logic vs. Accuracy)**
*   **Definition:** The student made a calculation, transcription, or specific value error.
*   **The Conflict:** GT applies a strict penalty (often 0 points for the section) because the error simplified the problem or violated the rubric. The Model applies "error carried forward" (follow-through) principles, awarding points for correct logic after the error.
*   **Keywords:** Calculation error, arithmetic mistake, transcription error, partial credit.

**B. Process Norms & Completeness (Implicit vs. Explicit)**
*   **Definition:** The student found the correct answer but skipped steps, didn't define variables, or used non-standard formatting.
*   **The Conflict:** GT penalizes for missing "process steps" or lack of rigor in writing. The Model ignores these flaws because the "final answer" or "general idea" is correct.
*   **Keywords:** Skipped steps, lack of definition, formatting, presentation, missing units.

**C. Logical Rigor & Edge Cases (Strict vs. Lenient)**
*   **Definition:** The logical argument has holes, missing sufficient/necessary conditions, or missed specific cases (e.g., dividing by zero).
*   **The Conflict:** GT demands a watertight proof; any logical gap leads to heavy penalties. The Model is "convinced" by the general argument and overlooks the logical gap.
*   **Keywords:** Sufficient/necessary conditions, missing cases, classification discussion, logical gap.

**D. Insight Recognition (Rigidity vs. Flexibility)**
*   **Definition:** The student used an alternative method not in the reference answer.
*   **The Conflict:** GT (or the human grader) failed to recognize the validity of the alternative method (or the rubric didn't support it). The Model successfully identified the mathematical validity of the alternative approach and awarded points. (Or vice versa: Model failed to see the insight).
*   **Keywords:** Alternative method, creative solution, geometric interpretation.

**E. OOD / Other (Fundamental Anomaly) -- USE WITH CAUTION**
*   **Definition:** The discrepancy cannot be explained by scoring philosophy differences (A-D). This includes hallucinations, data corruption, or factual errors in the GT itself.
*   **Trigger Condition:** ONLY use this if the discrepancy is NOT about "how strict we should be" but about "objective factual reality" or "system failure".
*   **Examples:**
    *   The GT score is mathematically impossible (e.g., > full score).
    *   The Model hallucinated text that does not exist in the student response (e.g., OCR hallucination).
    *   The Model refused to answer due to safety policies.
    *   The Reference Answer itself is mathematically incorrect.

### Output Format (JSON)

Return **ONLY** a valid JSON object with no markdown formatting:

{{
    "model_score": <float>,
    "gt_score": <float>,
    "score_diff": <float>,
    "analysis": "<Concise explanation of WHY the scores differ based on the student's specific error>",
    "primary_category_code": "<A, B, C, D, or E>",
    "primary_category_name": "<Name of the category>",
    "ood_details": {{
        "is_ood": <boolean, true only if Category E>,
        "justification": "<Required if E: Why does this NOT fit A-D?>",
        "suggested_new_category": "<Required if E: What should this new failure mode be called?>"
    }}
}}
"""

QUESTION_INSTRUCTION="""
    You are a high school student in a mathematics class. You are given a mathematical problem and you are asked to solve it.
    Please solve the problem and provide your solution.
    The problem is:
    {problem_statement}


    Please first think and then solve the problem step by step.

    IMPORTANT: Answer each sub-question in order, following the format of an answer sheet.
    
    Answer Format Requirements:
    1. Identify all sub-questions in the problem (e.g., (1), (2), (3), or (Ⅰ), (Ⅱ), (Ⅲ), etc.)
    2. Answer each sub-question sequentially using the exact same numbering format as in the problem
    3. For each sub-question, write your answer in the following format:
    
    (1) [Your solution for sub-question (1) here]
    
    (2) [Your solution for sub-question (2) here]
    
    (3) [Your solution for sub-question (3) here]
    
    And so on...
    
    If the problem uses Roman numerals like (Ⅰ), (Ⅱ), (Ⅲ), use the same format:
    
    (Ⅰ) [Your solution here]
    
    (Ⅱ) [Your solution here]
    
    For each sub-question, provide:
    - Clear step-by-step reasoning
    - All necessary calculations
    - Final answer clearly marked
    
    Example format:
    (1) First, I need to...
    [Show your work]
    Therefore, the answer is...
    
    (2) For this part, I will...
    [Show your work]
    So the result is...

"""

POINTING_BENCHMARK_INSTRUCTION="""
You are an expert mathematics evaluator tasked with scoring student responses to mathematical problems.

TASK:
- Evaluate a complete student answer against a reference answer with detailed scoring rubrics
- Provide an overall score for the student's response
- Give brief explanations for your scoring decisions

EVALUATION CRITERIA:
1. Mathematical Accuracy: Correctness of mathematical concepts, formulas, and calculations
2. Solution Approach: Logical reasoning and problem-solving methodology
3. Completeness: Whether the student addressed all required parts of the problem
4. Clarity: How well the solution is presented and explained

INPUT FORMAT:
- Reference Answer: Contains the correct solution with detailed step-by-step scoring rubrics using cumulative scoring (e.g., "------3 points" means all steps up to that point are correct and the student earns 3 points)
- Problem Statement: The complete mathematical problem (not broken into sub-questions)
- Student Response: The complete student's answer (not broken into sub-questions)

SCORING PROCESS:
1. Compare the student's approach with the reference solution
2. Identify which key mathematical steps were correctly executed 
3. Check for major conceptual errors or missing components
4. Award partial credit for partially correct solutions based on how far the student progressed correctly
5. Provide an overall score that reflects the student's performance (the highest cumulative score they achieved)

OUTPUT FORMAT:
- Overall Score: [X] where X is the score awarded
- Brief Explanation: 2-3 sentences explaining the main strengths and weaknesses of the student's response
- Key Observations: Highlight any significant mathematical insights or errors



Remember: Focus on mathematical understanding rather than formatting. Award credit for correct mathematical reasoning even if presentation could be improved.



Now, please evaluate the following:


Problem Statement: {problem_statement}

Student Response: {student_response}

Reference Answer: {reference_answer}


Please provide your evaluation:
"""


def get_instruction_template(source, dataset_name):
    """Return instruction template for the given dataset."""
    if dataset_name == "realmath_eval":
        return POINTING_BENCHMARK_INSTRUCTION
    elif dataset_name == "VF_pointing":
        return VF_POINTING_INSTRUCTION
    elif dataset_name == "VF_realmath_eval":
        return VF_POINTING_INSTRUCTION
    elif dataset_name == "write_through_first":
        return WRITE_THROUGH_FIRST_INSTRUCTION
    elif dataset_name == "style_transfer":
        return STYLE_TRANSFER_INSTRUCTION
    elif dataset_name == "meta_eval":
        return META_EVALUATION_INSTRUCTION
    elif dataset_name == "question":
        return QUESTION_INSTRUCTION
    else:
        raise ValueError(f"Unknown dataset_name: {dataset_name}")


def convert_realmath_eval_to_maslab_format(input_file, output_file, task_type="pointwise", sample_size=None, dataset_name="realmath_eval"):
    """
    Convert realmath_eval format data to MASLab format.
    """
    print(f"Converting {input_file} to MASLab format...")
    print(f"Task type: {task_type}")
    
    data_list = []
    
    if os.path.isdir(input_file):
        json_files = [f for f in os.listdir(input_file) if f.endswith('.json')]
        json_files.sort()  
        print(f"Found {len(json_files)} JSON files in directory")
        
        for json_file in json_files:
            file_path = os.path.join(input_file, json_file)
            print(f"Processing {json_file}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                question = data.get("question", "")
                question_location = data.get("question_location", "")
                question_type = data.get("question_type", "")
                question_level = data.get("question_level", "")
                full_score = data.get("full_score", 0)
                
                reference_answer_data = data.get("reference_answer", {})
                reference_answer = reference_answer_data.get("translated_text", "")
                
                answers = data.get("answers", [])
                
                if not question or not reference_answer or not answers:
                    print(f"Warning: Skipping {json_file} - missing required fields")
                    continue
                
                for answer_data in answers:
                    student_id = answer_data.get("student_id", "")
                    student_answer = answer_data.get("answer", "")
                    student_score = answer_data.get("score", 0)
                    sub_question_scores = answer_data.get("sub_question_scores", {})
                    
                    if not student_answer:
                        print(f"Warning: Skipping student {student_id} in {json_file} - no answer")
                        continue
                    
                    instruction_template = get_instruction_template("realmath_eval", dataset_name)
                    
                    full_query = instruction_template.format(
                        reference_answer=reference_answer,
                        problem_statement=question,
                        student_response=student_answer
                    )
                    
                    converted_item = {
                        "query": full_query,
                        "student_response": student_answer,
                        "sub_question_scores": sub_question_scores,
                        "gt": student_score,  # Use student's actual score as ground truth
                        "reference_answer": reference_answer,
                        "problem_statement": question,
                        "student_id": student_id,
                        "question_location": question_location,
                        "question_type": question_type,
                        "question_level": question_level,
                        "full_score": full_score,
                        "task_description": f"Score the student response for mathematical problem {question_location}",
                        "source": dataset_name,
                        "tag": ["llm_judge", "pointwise", "math_scoring", dataset_name, f"level_{question_level}"]
                    }
                    
                    if converted_item["query"] and converted_item["student_response"] and converted_item["gt"] is not None:
                        data_list.append(converted_item)
                    else:
                        print(f"Warning: Skipping incomplete item for student {student_id} in {json_file}")
                        
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error in {json_file}: {e}")
            except Exception as e:
                print(f"Warning: Error processing {json_file}: {e}")
    
    else:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            question = data.get("question", "")
            question_location = data.get("question_location", "")
            question_type = data.get("question_type", "")
            question_level = data.get("question_level", "")
            full_score = data.get("full_score", 0)
            
            reference_answer_data = data.get("reference_answer", {})
            reference_answer = reference_answer_data.get("translated_text", "")
            
            answers = data.get("answers", [])
            
            if not question or not reference_answer or not answers:
                print(f"Warning: Missing required fields in {input_file}")
                return 0
            
            for answer_data in answers:
                student_id = answer_data.get("student_id", "")
                student_answer = answer_data.get("answer", "")
                student_score = answer_data.get("score", 0)
                sub_question_scores = answer_data.get("sub_question_scores", {})
                if not student_answer:
                    print(f"Warning: Skipping student {student_id} - no answer")
                    continue
                
                instruction_template = get_instruction_template("realmath_eval", dataset_name)
                
                full_query = instruction_template.format(
                    reference_answer=reference_answer,
                    problem_statement=question,
                    student_response=student_answer
                )
                
                converted_item = {
                    "query": full_query,
                    "student_response": student_answer,
                    "sub_question_scores": sub_question_scores,
                    "gt": student_score,  
                    "reference_answer": reference_answer,
                    "problem_statement": question,
                    "student_id": student_id,
                    "question_location": question_location,
                    "question_type": question_type,
                    "question_level": question_level,
                    "full_score": full_score,
                    "task_description": f"Score the student response for mathematical problem {question_location}",
                    "source": dataset_name,
                    "tag": ["llm_judge", "pointwise", "math_scoring", dataset_name, f"level_{question_level}"]
                }
                
                if converted_item["query"] and converted_item["student_response"] and converted_item["gt"] is not None:
                    data_list.append(converted_item)
                else:
                    print(f"Warning: Skipping incomplete item for student {student_id}")
                    
        except json.JSONDecodeError as e:
            print(f"Warning: JSON decode error in {input_file}: {e}")
            return 0
        except Exception as e:
            print(f"Warning: Error processing {input_file}: {e}")
            return 0
    
    question_groups = {}
    for item in data_list:
        question_loc = item.get("question_location", "unknown")
        if question_loc not in question_groups:
            question_groups[question_loc] = []
        question_groups[question_loc].append(item)
    
    print(f"\nQuestions processed:")
    for question_loc, items in question_groups.items():
        print(f"  - {question_loc}: {len(items)} student responses")
    
    # Two-level sampling: first by question, then by score distribution
    if sample_size and sample_size < len(data_list):
        random.seed(42)
        
        num_questions = len(question_groups)
        samples_per_question = sample_size // num_questions
        remaining_samples = sample_size % num_questions
        
        print(f"\nSampling strategy:")
        print(f"  Total sample size: {sample_size}")
        print(f"  Number of questions: {num_questions}")
        print(f"  Samples per question: {samples_per_question}")
        print(f"  Remaining samples to distribute: {remaining_samples}")
        
        sampled_data = []
        
        for i, (question_loc, question_items) in enumerate(sorted(question_groups.items())):
            # Same sample count per question, remainder to earlier questions
            question_sample_size = samples_per_question + (1 if i < remaining_samples else 0)
            
            print(f"\n  Question {question_loc}: target {question_sample_size} samples")
            
            # Group by score within this question
            score_groups = {}
            for item in question_items:
                score = item.get("gt", 0)
                if score not in score_groups:
                    score_groups[score] = []
                score_groups[score].append(item)
            
            # Sample uniformly by score within this question
            if question_sample_size >= len(question_items):
                # Take all if target >= total samples for this question
                sampled_data.extend(question_items)
                print(f"    Sampled all {len(question_items)} samples")
            else:
                num_score_groups = len(score_groups)
                samples_per_score = question_sample_size // num_score_groups
                remaining_in_question = question_sample_size % num_score_groups
                
                question_sampled = []
                sampled_count = 0
                
                for j, (score, items) in enumerate(sorted(score_groups.items())):
                    # Same count per score bin
                    target_count = samples_per_score + (1 if j < remaining_in_question else 0)
                    
                    if len(items) <= target_count:
                        question_sampled.extend(items)
                        sampled_count += len(items)
                        print(f"      Score {score}: sampled all {len(items)} samples (target {target_count})")
                    else:
                        question_sampled.extend(random.sample(items, target_count))
                        sampled_count += target_count
                        print(f"      Score {score}: sampled {target_count} out of {len(items)} samples")
                
                # If short, supplement from score bins with more samples
                if sampled_count < question_sample_size:
                    shortage = question_sample_size - sampled_count
                    print(f"    Need {shortage} more samples to reach target {question_sample_size}")
                    
                    # Find score bins with remaining samples (sorted by count desc)
                    available_scores = []
                    for score, items in sorted(score_groups.items(), key=lambda x: len(x[1]), reverse=True):
                        available = [item for item in items if item not in question_sampled]
                        if available:
                            available_scores.append((score, available))
                    
                    # Supplement from these bins
                    supplement_count = 0
                    for score, available in available_scores:
                        if supplement_count >= shortage:
                            break
                        need = min(len(available), shortage - supplement_count)
                        question_sampled.extend(random.sample(available, need))
                        supplement_count += need
                        print(f"      Score {score}: supplemented {need} samples")
                
                sampled_data.extend(question_sampled)
        
        data_list = sampled_data
        
        # Global supplement if still short
        if len(data_list) < sample_size:
            global_shortage = sample_size - len(data_list)
            print(f"\nGlobal supplement: Need {global_shortage} more samples to reach target {sample_size}")
            
            # Find all unsampled items (sorted by question and score)
            all_available = []
            for question_loc, question_items in sorted(question_groups.items()):
                for item in question_items:
                    if item not in data_list:
                        all_available.append(item)
            
            if all_available:
                # Supplement needed count
                supplement_needed = min(global_shortage, len(all_available))
                supplement_samples = random.sample(all_available, supplement_needed)
                data_list.extend(supplement_samples)
                print(f"Supplemented {supplement_needed} samples from remaining pool")
            else:
                print(f"Warning: No more samples available for supplement")
        
        print(f"\nTotal sampled: {len(data_list)} items")
        
        # Show question and score distribution after sampling
        question_dist = {}
        score_dist = {}
        for item in data_list:
            q_loc = item.get("question_location", "unknown")
            score = item.get("gt", 0)
            question_dist[q_loc] = question_dist.get(q_loc, 0) + 1
            score_dist[score] = score_dist.get(score, 0) + 1
        
        print(f"\nQuestion distribution after sampling:")
        for q_loc in sorted(question_dist.keys()):
            print(f"  {q_loc}: {question_dist[q_loc]} samples")
        
        print(f"\nOverall score distribution after sampling:")
        for score in sorted(score_dist.keys()):
            print(f"  Score {score}: {score_dist[score]} samples")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data_list)} items to {output_file}")
    return len(data_list)


def convert_style_transfer_to_maslab_format(input_file, output_file, task_type="pointwise", dataset_name="style_transfer"):
    """
    Convert realmath_eval_diff_ge2.json to MASLab format for style transfer experiment.
    For each item, use STYLE_TRANSFER_INSTRUCTION template with only student_response filled in.
    """
    print(f"Converting {input_file} to MASLab format for style transfer...")
    print(f"Task type: {task_type}")
    
    data_list = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        if not isinstance(items, list):
            print(f"Error: Expected JSON array, got {type(items)}")
            return 0
        
        print(f"Found {len(items)} items in {input_file}")
        
        instruction_template = get_instruction_template("style_transfer", dataset_name)
        
        for item in items:
            student_response = item.get("student_response", "")
            if not student_response:
                print(f"Warning: Skipping item with missing student_response")
                continue
            
            # Build query using style transfer template (only student_response)
            full_query = instruction_template.format(
                student_response=student_response
            )
            
            # Preserve all original fields, but update query
            converted_item = {
                "query": full_query,
                "student_response": student_response,  # Original student response (will be replaced by LLM output)
                "sub_question_scores": item.get("sub_question_scores", {}),
                "gt": item.get("gt"),
                "reference_answer": item.get("reference_answer", ""),
                "problem_statement": item.get("problem_statement", ""),
                "student_id": item.get("student_id", ""),
                "question_location": item.get("question_location", ""),
                "question_type": item.get("question_type", ""),
                "question_level": item.get("question_level", ""),
                "full_score": item.get("full_score", 0),
                "task_description": f"Rewrite student response in standardized style for problem {item.get('question_location', 'unknown')}",
                "source": "style_transfer",
                "tag": ["style_transfer", "pointwise", "math_scoring", "realmath_eval", f"level_{item.get('question_level', 'unknown')}"]
            }
            
            if converted_item["query"] and converted_item["student_response"]:
                data_list.append(converted_item)
            else:
                print(f"Warning: Skipping incomplete item")
        
        print(f"Processed {len(data_list)} items")
        
    except json.JSONDecodeError as e:
        print(f"Error: JSON decode error in {input_file}: {e}")
        return 0
    except Exception as e:
        print(f"Error: Error processing {input_file}: {e}")
        return 0
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data_list)} items to {output_file}")
    return len(data_list)


def convert_question_to_maslab_format(input_file, output_file, task_type="choice", sample_size=None):
    """
    Convert question format data to MASLab format.
    """
    print(f"Converting {input_file} to MASLab format...")
    print(f"Task type: {task_type}")
    
    data_list = []
    
    if os.path.isdir(input_file):
        json_files = [f for f in os.listdir(input_file) if f.endswith('.json')]
        json_files.sort()  
        print(f"Found {len(json_files)} JSON files in directory")
        
        for json_file in json_files:
            file_path = os.path.join(input_file, json_file)
            print(f"Processing {json_file}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                question = data.get("question", "")
                question_location = data.get("question_location", "")
                question_type = data.get("question_type", "")
                question_level = data.get("question_level", "")
                full_score = data.get("full_score", 0)
                reference_answer_data = data.get("reference_answer", {})
                reference_answer = reference_answer_data.get("translated_text", "")
                
                
                
                instruction_template = get_instruction_template("question", "question")
                full_query = instruction_template.format(
                    problem_statement=question,
                )
                

                converted_item = {
                    "query": full_query,
                    "problem_statement": question,
                    "question_location": question_location,
                    "question_type": question_type,
                    "question_level": question_level,
                    "full_score": full_score,
                    "reference_answer": reference_answer,
                    "task_description": f"Score the student response for mathematical problem {question_location}",
                    "source": "question",
                    "tag": ["llm_judge", "pointwise", "math_scoring", "realmath_eval", f"level_{question_level}"]
                }

                if converted_item["query"]  and converted_item["problem_statement"] is not None:
                    data_list.append(converted_item)
                else:
                    print(f"Warning: Skipping incomplete item for question {question_location}")

            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error in {json_file}: {e}")
            except Exception as e:
                print(f"Warning: Error processing {json_file}: {e}")
    
    else:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            question = data.get("question", "")
            question_location = data.get("question_location", "")
            question_type = data.get("question_type", "")
            question_level = data.get("question_level", "")
            full_score = data.get("full_score", 0)
            reference_answer_data = data.get("reference_answer", {})
            reference_answer = reference_answer_data.get("translated_text", "")
            
            instruction_template = get_instruction_template("question", "question")
            full_query = instruction_template.format(
                    problem_statement=question,
                )
                
            converted_item = {
                    "query": full_query,
                    "problem_statement": question,
                    "question_location": question_location,
                    "question_type": question_type,
                    "question_level": question_level,
                    "full_score": full_score,
                    "reference_answer": reference_answer,
                    "task_description": f"Score the student response for mathematical problem {question_location}",
                    "source": "question",
                    "tag": ["llm_judge", "pointwise", "math_scoring", "realmath_eval", f"level_{question_level}"]
                }
                
            if converted_item["query"]  and converted_item["problem_statement"] is not None:
                data_list.append(converted_item)
            else:
                print(f"Warning: Skipping incomplete item for question {question_location}")
                    
        except json.JSONDecodeError as e:
            print(f"Warning: JSON decode error in {input_file}: {e}")
            return 0
        except Exception as e:
            print(f"Warning: Error processing {input_file}: {e}")
            return 0
    
    question_groups = {}
    for item in data_list:
        question_loc = item.get("question_location", "unknown")
        if question_loc not in question_groups:
            question_groups[question_loc] = []
        question_groups[question_loc].append(item)
    
    print(f"\nQuestions processed:")
    for question_loc, items in question_groups.items():
        print(f"  - {question_loc}: {len(items)} student responses")
    
    # Sampling
    if sample_size and sample_size < len(data_list):
        random.seed(42)
        # Random sample from original data
        original_length = len(data_list)
        indices = random.sample(range(len(data_list)), sample_size)
        data_list = [data_list[i] for i in indices]
        print(f"Sampled {sample_size} items from {original_length} total items")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data_list)} items to {output_file}")
    return len(data_list)


def convert_VF_pointing_to_maslab_format(input_file, output_file, task_type="pointwise", sample_size=None, dataset_name="VF_pointing"):
    """
    Convert realmath_eval format to Verify-First MASLab format.
    Uses VF_POINTING_INSTRUCTION.
    """
    print(f"Converting {input_file} to MASLab VF_pointing format...")
    print(f"Task type: {task_type}")
    
    data_list = []
    
    if os.path.isdir(input_file):
        # Only single JSON file supported for now; see realmath_eval for dir support
        print("Error: input_file must be a json file for VF_pointing conversion (directory support not implemented yet)")
        return 0
    else:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # realmath_eval.json is a list
            if not isinstance(data, list):
                print(f"Error: expected list in {input_file}")
                return 0
                
            for item in data:
                # Extract original fields
                question = item.get("problem_statement", "")
                # Some versions use "question"
                if not question: 
                    question = item.get("question", "")
                    
                reference_answer = item.get("reference_answer", "")
                # If reference_answer is dict (contains translated_text)
                if isinstance(reference_answer, dict):
                    reference_answer = reference_answer.get("translated_text", "")
                
                student_answer = item.get("student_response", "")
                # Fallback to answer if no student_response
                if not student_answer:
                    student_answer = item.get("answer", "")
                
                student_score = item.get("gt", 0)
                # Fallback to score if gt missing
                if student_score is None:
                    student_score = item.get("score", 0)
                
                student_id = item.get("student_id", "")
                question_location = item.get("question_location", "")
                question_type = item.get("question_type", "")
                question_level = item.get("question_level", "")
                full_score = item.get("full_score", 0)
                sub_question_scores = item.get("sub_question_scores", {})

                if not student_answer or not question or not reference_answer:
                    # Assume input is build_judge_dataset output (realmath_eval.json format)
                    if "query" in item:
                        # Already converted item
                        pass
                    else:
                        print(f"Warning: Skipping item {student_id} - missing fields")
                        continue
                
                instruction_template = get_instruction_template("VF_pointing", dataset_name)
                
                full_query = instruction_template.format(
                    reference_answer=reference_answer,
                    problem_statement=question,
                    student_response=student_answer
                )
                
                converted_item = {
                    "query": full_query,
                    "student_response": student_answer,
                    "sub_question_scores": sub_question_scores,
                    "gt": student_score,  
                    "reference_answer": reference_answer,
                    "problem_statement": question,
                    "student_id": student_id,
                    "question_location": question_location,
                    "question_type": question_type,
                    "question_level": question_level,
                    "full_score": full_score,
                    "task_description": f"Verify and score student response for {question_location}",
                    "source": dataset_name,
                    "tag": ["llm_judge", "pointwise", "math_scoring", dataset_name, f"level_{question_level}"]
                }
                
                if converted_item["query"] and converted_item["student_response"] and converted_item["gt"] is not None:
                    data_list.append(converted_item)
                else:
                    print(f"Warning: Skipping incomplete item for student {student_id}")
                    
        except json.JSONDecodeError as e:
            print(f"Warning: JSON decode error in {input_file}: {e}")
            return 0
        except Exception as e:
            print(f"Warning: Error processing {input_file}: {e}")
            return 0
    
    # Sampling
    if sample_size and sample_size < len(data_list):
        random.seed(42)
        print(f"Sampling {sample_size} items from {len(data_list)}...")
        data_list = random.sample(data_list, sample_size)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data_list)} items to {output_file}")
    return len(data_list)


def convert_meta_eval_to_maslab_format(input_file, output_file, task_type="choice", sample_size=None, diff_threshold=2):
    """
    Convert realmath_eval results (results.jsonl) to meta_eval task:
    - Use META_EVALUATION_INSTRUCTION for query
    - Use results_realmath_evaluation_report.json to compute |predicted_score - gt|
    - Keep only samples with diff >= diff_threshold (default 2)
    """
    print(f"Converting {input_file} to MASLab meta-eval format...")
    print(f"Task type: {task_type}")
    print(f"Score diff threshold: {diff_threshold}")

    if os.path.isdir(input_file):
        print("Error: input_file should be a JSONL result file, not a directory.")
        return 0

    # Read report, build sample_id -> detailed record mapping
    base_dir = os.path.dirname(input_file)
    report_path = os.path.join(base_dir, "results_realmath_evaluation_report.json")
    if not os.path.exists(report_path):
        print(f"Error: report file not found: {report_path}")
        return 0

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        detailed_results = report_data.get("detailed_results", [])
        report_map = {item.get("sample_id"): item for item in detailed_results}
    except Exception as e:
        print(f"Error: failed to load report file: {e}")
        return 0

    data_list = []
    total_lines = 0
    kept_lines = 0

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                try:
                    sample = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error at line {idx}: {e}")
                    continue

                sample_id = idx  # results.jsonl 1:1 with report sample_id (line number from 1)
                report_item = report_map.get(sample_id)
                if not report_item:
                    print(f"Warning: sample_id {sample_id} missing in report; skipped.")
                    continue

                if report_item.get("extraction_failed") or report_item.get("has_error"):
                    continue

                gt_score = report_item.get("gt")
                model_score = report_item.get("predicted_score")
                if model_score is None:
                    model_score = report_item.get("original_predicted_score")
                try:
                    gt_score = float(gt_score)
                    model_score = float(model_score)
                except (TypeError, ValueError):
                    continue

                score_diff = abs(model_score - gt_score)
                if score_diff < diff_threshold:
                    continue

                # Fill meta-eval prompt
                instruction_template = get_instruction_template("meta_eval", "meta_eval")
                full_query = instruction_template.format(
                    problem_statement=sample.get("problem_statement", ""),
                    reference_answer=sample.get("reference_answer", ""),
                    student_response=sample.get("student_response", ""),
                    gt=gt_score,
                    response=sample.get("response", "")
                )

                converted_item = {
                    "query": full_query,
                    "gt": gt_score,
                    "model_score": model_score,
                    "score_diff": score_diff,
                    "reference_answer": sample.get("reference_answer", ""),
                    "problem_statement": sample.get("problem_statement", ""),
                    "student_response": sample.get("student_response", ""),
                    "response": sample.get("response", ""),
                    "sub_question_scores": sample.get("sub_question_scores", {}),
                    "sample_id": sample_id,
                    "question_location": sample.get("question_location", ""),
                    "question_type": sample.get("question_type", ""),
                    "question_level": sample.get("question_level", ""),
                    "full_score": sample.get("full_score", None),
                    "task_description": f"Meta-evaluate score gap for math problem {sample.get('question_location', '')}",
                    "source": "meta_eval",
                    "tag": ["llm_judge", "meta_eval", "math_scoring", "realmath_eval"]
                }

                data_list.append(converted_item)
                kept_lines += 1
    except Exception as e:
        print(f"Error: failed to read {input_file}: {e}")
        return 0

    print(f"Total samples read: {total_lines}, kept (diff >= {diff_threshold}): {kept_lines}")

    # Sampling
    if sample_size and sample_size < len(data_list):
        random.seed(42)
        original_length = len(data_list)
        data_list = random.sample(data_list, sample_size)
        print(f"Sampled {sample_size} items from {original_length} total items")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data_list)} items to {output_file}")
    return len(data_list)



        
def main():
    parser = argparse.ArgumentParser(description="Build Judge Benchmark dataset for MASLab")
    parser.add_argument("--input-file", type=str, required=True, help="Input JSONL file path")
    parser.add_argument("--output-name", type=str, required=True, help="Output dataset name (without extension)")
    parser.add_argument("--sample-size", type=int, default=None, help="Sample size (default: use all data)")
    parser.add_argument("--dataset_name", type=str, default="realmath_eval", help="""dataset name:
                        - realmath_eval
                        - VF_pointing
                        - VF_realmath_eval
                        - write_through_first
                        - question
                        - meta_eval
                        - style_transfer
                        """)
    args = parser.parse_args()

    input_file = args.input_file
    output_file = f"./data/{args.output_name}.json"

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        return

    if args.dataset_name == "realmath_eval":
        num_items = convert_realmath_eval_to_maslab_format(
            input_file=input_file,
            output_file=output_file,
            task_type="pointwise",
            sample_size=args.sample_size,
            dataset_name=args.dataset_name
        )
    elif args.dataset_name == "VF_realmath_eval":
        num_items = convert_realmath_eval_to_maslab_format(
            input_file=input_file,
            output_file=output_file,
            task_type="pointwise",
            sample_size=args.sample_size,
            dataset_name="VF_realmath_eval"
        )
    elif args.dataset_name == "VF_pointing" or args.dataset_name == "write_through_first":
        num_items = convert_VF_pointing_to_maslab_format(
            input_file=input_file,
            output_file=output_file,
            task_type="pointwise",
            sample_size=args.sample_size,
            dataset_name=args.dataset_name
        )
    elif args.dataset_name == "question":
        num_items = convert_question_to_maslab_format(
            input_file=input_file,
            output_file=output_file,
            task_type="choice",
            sample_size=args.sample_size
        )
    elif args.dataset_name == "meta_eval":
        num_items = convert_meta_eval_to_maslab_format(
            input_file=input_file,
            output_file=output_file,
            task_type="choice",
            sample_size=args.sample_size
        )
    elif args.dataset_name == "style_transfer":
        num_items = convert_style_transfer_to_maslab_format(
            input_file=input_file,
            output_file=output_file,
            task_type="pointwise",
            dataset_name=args.dataset_name
        )
    else:
        raise ValueError(f"Invalid dataset name: {args.dataset_name}")
    
    print(f"\n✅ Dataset creation completed!")
    print(f"📁 Output file: {output_file}")
    print(f"📊 Total items: {num_items}")
    print(f"🎯 Task type: Choice ")
    
    # Show sample data
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if data:
            print(f"\n📋 Sample data:")
            sample = data[0]
            print(f"Source: {sample['source']}")
            if 'gt' in sample:
                print(f"GT: {sample['gt']}")
            print(f"Query preview: {sample['query'][:200]}...")

if __name__ == "__main__":
    main() 

