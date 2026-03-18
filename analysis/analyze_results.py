import json
from collections import defaultdict, Counter

# Load evaluation report
with open('outputs/realmath_eval_llm_answer/cot/deepseek-v3.2/20260305_210854/results_realmath_evaluation_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract valid samples (exclude errors and extraction failures)
valid_samples = []
for result in data['detailed_results']:
    if (not result.get('has_error', False) and 
        not result.get('extraction_failed', False)):
        valid_samples.append({
            'predicted': result.get('predicted_score'),
            'gt': result.get('gt'),
            'max_score': result.get('max_score', 0)
        })

print(f"Valid samples: {len(valid_samples)}")
print(f"Total samples: {data['summary']['total_samples']}")
print(f"MSE Loss: {data['summary']['mse_loss']}")
print(f"Performance Score: {data['summary']['performance_score']}%")
print()

# Compute differences and statistics
differences = []
for sample in valid_samples:
    if sample['predicted'] is not None and sample['gt'] is not None:
        diff = abs(sample['predicted'] - sample['gt'])
        differences.append({
            'diff': diff,
            'predicted': sample['predicted'],
            'gt': sample['gt'],
            'max_score': sample['max_score']
        })

# Sort by difference
differences.sort(key=lambda x: x['diff'])

print("Top 20 samples (smallest diff):")
print("No. | Diff | Pred | GT | Max")
print("-" * 40)
for i, item in enumerate(differences[:20]):
    print(f"{i+1:2d}   | {item['diff']:2.0f}   | {item['predicted']:2.0f}   | {item['gt']:2.0f} | {item['max_score']:2.0f}")

print()
print("Bottom 20 samples (largest diff):")
print("No. | Diff | Pred | GT | Max")
print("-" * 40)
for i, item in enumerate(differences[-20:], len(differences)-19):
    print(f"{i:2d}   | {item['diff']:2.0f}   | {item['predicted']:2.0f}   | {item['gt']:2.0f} | {item['max_score']:2.0f}")

# Distribution of differences
diff_counter = Counter()
for item in differences:
    diff_counter[int(item['diff'])] += 1

print()
print("Difference distribution:")
print("Diff | Count | Pct")
print("-" * 25)
total_valid = len(differences)
for diff in sorted(diff_counter.keys()):
    count = diff_counter[diff]
    percentage = (count / total_valid) * 100
    print(f"{diff:2d}   | {count:3d}   | {percentage:5.1f}%")

# Summary statistics
diff_values = [item['diff'] for item in differences]
print()
print("Summary:")
print(f"Mean absolute error: {sum(diff_values) / len(diff_values):.2f}")
print(f"Max diff: {max(diff_values)}")
print(f"Min diff: {min(diff_values)}")
print(f"Median diff: {sorted(diff_values)[len(diff_values)//2]}")

# Accuracy distribution (using >=)
perfect_matches = sum(1 for d in diff_values if d == 0)
diff_1_plus = sum(1 for d in diff_values if d >= 1)
diff_2_plus = sum(1 for d in diff_values if d >= 2)
diff_3_plus = sum(1 for d in diff_values if d >= 3)
diff_4_plus = sum(1 for d in diff_values if d >= 4)
diff_5_plus = sum(1 for d in diff_values if d >= 5)
diff_10_plus = sum(1 for d in diff_values if d >= 10)

print()
print("Accuracy distribution (>=):")
print(f"Perfect match (diff=0): {perfect_matches} ({perfect_matches/total_valid*100:.1f}%)")
print(f"Diff>=1: {diff_1_plus} ({diff_1_plus/total_valid*100:.1f}%)")
print(f"Diff>=2: {diff_2_plus} ({diff_2_plus/total_valid*100:.1f}%)")
print(f"Diff>=3: {diff_3_plus} ({diff_3_plus/total_valid*100:.1f}%)")
print(f"Diff>=4: {diff_4_plus} ({diff_4_plus/total_valid*100:.1f}%)")
print(f"Diff>=5: {diff_5_plus} ({diff_5_plus/total_valid*100:.1f}%)")
print(f"Diff>=10: {diff_10_plus} ({diff_10_plus/total_valid*100:.1f}%)")
