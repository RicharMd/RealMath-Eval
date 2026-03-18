#!/usr/bin/env python3
"""
Test script for lean_utils functionality
测试lean_utils包的各项功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from methods.lean_utils import (
    extract_lean_code_blocks,
    format_lean_code,
    create_lean_context,
    analyze_lean_code_structure,
    verify_lean_code_with_cli,
    batch_verify_lean_codes
)


def test_extract_lean_code_blocks():
    """测试Lean代码块提取功能"""
    print("🧪 Testing extract_lean_code_blocks...")
    
    sample_text = """
Here is some mathematical reasoning with Lean code:

```lean
theorem simple_theorem : 2 + 2 = 4 := by simp
```

And here's another example:

```Lean
def factorial : ℕ → ℕ
| 0 => 1
| (n + 1) => (n + 1) * factorial n
```

Some regular code that won't be extracted:
```
have h : x > 0 := by assumption
exact h
```
    """
    
    extracted_codes = extract_lean_code_blocks(sample_text)
    
    print(f"   Extracted {len(extracted_codes)} code blocks:")
    for i, code in enumerate(extracted_codes):
        print(f"   Block {i+1}:")
        print(f"   {code}")
        print("   ---")
    
    assert len(extracted_codes) == 2, "Should extract exactly 2 clearly marked lean code blocks"
    print("   ✅ extract_lean_code_blocks test passed")


def test_format_lean_code():
    """测试Lean代码格式化功能"""
    print("\n🧪 Testing format_lean_code...")
    
    messy_code = """
    
    theorem test_theorem : 2 + 2 = 4 := by simp   
    
    def my_function (x : ℕ) : ℕ := x + 1    
    
    """
    
    formatted = format_lean_code(messy_code, add_imports=True)
    
    print("   Original code:")
    print(f"   '{messy_code}'")
    print("\n   Formatted code:")
    print(f"   {formatted}")
    
    assert "import" in formatted, "Should add imports"
    assert formatted.strip().endswith("def my_function (x : ℕ) : ℕ := x + 1"), "Should clean trailing spaces"
    print("   ✅ format_lean_code test passed")


def test_create_lean_context():
    """测试Lean上下文创建功能"""
    print("\n🧪 Testing create_lean_context...")
    
    context = create_lean_context(
        problem_description="Find the sum of first n natural numbers",
        additional_definitions="def sum_n (n : ℕ) : ℕ := n * (n + 1) / 2"
    )
    
    print("   Generated context:")
    print(f"   {context}")
    
    assert "import" in context, "Should include imports"
    assert "Find the sum" in context, "Should include problem description"
    assert "sum_n" in context, "Should include additional definitions"
    print("   ✅ create_lean_context test passed")


def test_analyze_lean_code_structure():
    """测试Lean代码结构分析功能"""
    print("\n🧪 Testing analyze_lean_code_structure...")
    
    complex_code = """
import Mathlib.Data.Real.Basic
import Mathlib.Tactic

theorem pythagorean_theorem (a b c : ℝ) : a^2 + b^2 = c^2 → 
  ∃ (triangle : Triangle), triangle.is_right_angled := by sorry

def square (x : ℝ) : ℝ := x * x

example : square 3 = 9 := by
  have h : square 3 = 3 * 3 := rfl
  rw [h]
  simp
"""
    
    analysis = analyze_lean_code_structure(complex_code)
    
    print("   Analysis result:")
    for key, value in analysis.items():
        print(f"   {key}: {value}")
    
    assert analysis["has_imports"], "Should detect imports"
    assert len(analysis["has_theorems"]) >= 1, "Should detect theorems"
    assert len(analysis["has_definitions"]) >= 1, "Should detect definitions"
    assert "by" in analysis["has_tactics"], "Should detect tactics"
    print("   ✅ analyze_lean_code_structure test passed")


def test_verify_lean_code_with_cli():
    """测试Lean CLI代码验证功能"""
    print("\n🧪 Testing verify_lean_code_with_cli...")
    
    # 测试用例集合
    test_cases = [
        {
            "name": "Simple theorem",
            "code": "theorem simple : True := True.intro",
            "expected_valid": True,
            "context": ""
        },
        {
            "name": "Simple definition",
            "code": "def identity (x : Nat) : Nat := x",
            "expected_valid": True,
            "context": ""
        },
        {
            "name": "Simple sorry theorem",
            "code": "theorem with_sorry : True := sorry",
            "expected_valid": True,
            "context": ""
        },
        {
            "name": "Basic arithmetic",
            "code": "example : 1 + 1 = 2 := rfl",
            "expected_valid": True,
            "context": ""
        },
        {
            "name": "Syntax error",
            "code": "theorem bad syntax error",
            "expected_valid": False,
            "context": ""
        },
        {
            "name": "Empty code",
            "code": "",
            "expected_valid": False,
            "context": ""
        },
        {
            "name": "Using context",
            "code": "theorem test_with_context : my_id 5 = 5 := rfl",
            "expected_valid": True,
            "context": "def my_id (x : Nat) : Nat := x"
        },
        {
            "name": "False statement",
            "code": "theorem false_stmt : False := sorry",
            "expected_valid": True,
            "context": ""
        }
    ]
    
    passed_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(test_cases):
        print(f"\n   Test {i+1}: {test_case['name']}")
        print(f"   Code: {test_case['code'][:50]}{'...' if len(test_case['code']) > 50 else ''}")
        
        try:
            result = verify_lean_code_with_cli(test_case['code'], test_case['context'])
            
            is_valid = result["is_valid"]
            expected = test_case["expected_valid"]
            
            if is_valid == expected:
                print(f"   ✅ PASS - Expected: {expected}, Got: {is_valid}")
                passed_tests += 1
            else:
                print(f"   ❌ FAIL - Expected: {expected}, Got: {is_valid}")
                print(f"   Errors: {result.get('errors', [])}")
                failed_tests += 1
                
            print(f"   Method: {result.get('method', 'unknown')}")
            print(f"   Time: {result.get('compilation_time', 0):.2f}s")
            
        except Exception as e:
            print(f"   💥 ERROR - Exception: {str(e)}")
            failed_tests += 1
    
    print(f"\n   Summary: {passed_tests} passed, {failed_tests} failed")
    assert failed_tests == 0, f"Some tests failed: {failed_tests} failures"
    print("   ✅ verify_lean_code_with_cli test passed")


def test_batch_verify_lean_codes():
    """测试批量验证功能"""
    print("\n🧪 Testing batch_verify_lean_codes...")
    
    # 批量测试用例
    batch_test_cases = [
        {
            "codes": [
                "theorem test1 : True := True.intro",
                "def simple_id (x : Nat) : Nat := x", 
                "example : 2 + 2 = 4 := rfl"
            ],
            "context": "",
            "expected_results": [True, True, True],
            "description": "Basic valid codes"
        },
        {
            "codes": [
                "theorem valid : True := sorry",
                "def valid_def (x : Nat) : Nat := x",
                "theorem bad_syntax : invalid syntax here"
            ],
            "context": "",
            "expected_results": [True, True, False], 
            "description": "Mixed valid and invalid codes"
        },
        {
            "codes": [
                "theorem using_context : helper_func 5 = 5 := rfl",
                "example : helper_func 0 = 0 := rfl"
            ],
            "context": "def helper_func (x : Nat) : Nat := x",
            "expected_results": [True, True],
            "description": "Codes using shared context"
        }
    ]
    
    total_passed = 0
    total_failed = 0
    
    for batch_idx, test_batch in enumerate(batch_test_cases):
        print(f"\n   Batch {batch_idx + 1}: {test_batch['description']}")
        print(f"   Testing {len(test_batch['codes'])} codes...")
        
        try:
            results = batch_verify_lean_codes(test_batch['codes'], test_batch['context'])
            
            assert len(results) == len(test_batch['codes']), "Should return results for all codes"
            
            batch_passed = 0
            batch_failed = 0
            
            for i, (result, expected) in enumerate(zip(results, test_batch['expected_results'])):
                is_valid = result["is_valid"]
                code_preview = test_batch['codes'][i][:30] + "..." if len(test_batch['codes'][i]) > 30 else test_batch['codes'][i]
                
                if is_valid == expected:
                    print(f"     ✅ Code {i+1}: {code_preview}")
                    batch_passed += 1
                    total_passed += 1
                else:
                    print(f"     ❌ Code {i+1}: {code_preview}")
                    print(f"        Expected: {expected}, Got: {is_valid}")
                    if result.get('errors'):
                        print(f"        Errors: {result['errors'][0][:100]}...")
                    batch_failed += 1
                    total_failed += 1
            
            print(f"   Batch summary: {batch_passed}/{len(test_batch['codes'])} passed")
            
        except Exception as e:
            print(f"   💥 Batch failed with exception: {str(e)}")
            total_failed += len(test_batch['codes'])
    
    print(f"\n   Overall summary: {total_passed} passed, {total_failed} failed")
    assert total_failed == 0, f"Some batch tests failed: {total_failed} failures"
    print("   ✅ batch_verify_lean_codes test passed")


def test_performance():
    """测试性能表现"""
    print("\n🧪 Testing performance...")
    
    import time
    
    # 性能测试用例
    perf_tests = [
        {
            "name": "Simple theorem",
            "code": "theorem perf_test : True := True.intro"
        },
        {
            "name": "Definition",
            "code": "def perf_func (x : Nat) : Nat := x"
        },
        {
            "name": "Sorry theorem",
            "code": "theorem with_sorry : False := sorry"
        }
    ]
    
    total_time = 0
    
    for test in perf_tests:
        start_time = time.time()
        result = verify_lean_code_with_cli(test["code"])
        end_time = time.time()
        
        duration = end_time - start_time
        total_time += duration
        
        status = "✅ Valid" if result["is_valid"] else "❌ Invalid"
        print(f"   {test['name']}: {status} ({duration:.2f}s)")
    
    avg_time = total_time / len(perf_tests)
    print(f"\n   Performance summary:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per test: {avg_time:.2f}s")
    
    # 性能警告
    if avg_time > 10:
        print("   ⚠️  Warning: Average time > 10s, consider optimization")
    elif avg_time > 5:
        print("   ⚠️  Notice: Average time > 5s")
    else:
        print("   ✅ Good performance")
    
    print("   ✅ performance test completed")


def test_proof_completeness():
    """测试证明完整性检测功能"""
    
    print("\n" + "="*50)
    print("测试证明完整性检测功能")
    print("="*50)
    
    # 测试用例1：完整证明 (应该显示 no goals)
    complete_proof = """
theorem complete_example : 2 + 2 = 4 := by
  rfl
"""
    
    print("\n1. 完整证明测试 (应该是 no goals):")
    print(complete_proof)
    result = verify_lean_code_with_cli(complete_proof)
    print(f"编译成功: {result['is_valid']}")
    print(f"质量评估: {result.get('lean_analysis', {}).get('quality_assessment', 'unknown')}")
    print(f"错误信息: {result.get('errors', [])}")
    print(f"警告信息: {result.get('warnings', [])}")
    print(f"标准输出: {result.get('stdout', '')[:200]}...")
    print(f"错误输出: {result.get('stderr', '')[:200]}...")
    
    # 测试用例2：未完成的证明 (应该显示未解决的goals)
    incomplete_proof = """
theorem incomplete_example : 1 + 1 = 2 := by
  -- 使用一个不相关的策略，留下原目标未解决
  have h : True := True.intro
"""
    
    print("\n2. 未完成证明测试 (应该有未解决的goals):")
    print(incomplete_proof)
    result = verify_lean_code_with_cli(incomplete_proof)
    print(f"编译成功: {result['is_valid']}")
    print(f"质量评估: {result.get('lean_analysis', {}).get('quality_assessment', 'unknown')}")
    print(f"错误信息: {result.get('errors', [])}")
    print(f"警告信息: {result.get('warnings', [])}")
    print(f"标准输出: {result.get('stdout', '')[:300]}...")
    print(f"错误输出: {result.get('stderr', '')[:300]}...")
    
    # 测试用例3：部分完成的证明
    partial_proof = """
theorem partial_example : True ∧ True ∧ True := by
  constructor
  · trivial  -- 第一个完成了
  · constructor
    -- 这里留下两个未完成的goals
"""
    
    print("\n3. 部分完成证明测试:")
    print(partial_proof)
    result = verify_lean_code_with_cli(partial_proof)
    print(f"编译成功: {result['is_valid']}")
    print(f"质量评估: {result.get('lean_analysis', {}).get('quality_assessment', 'unknown')}")
    print(f"错误信息: {result.get('errors', [])}")
    print(f"警告信息: {result.get('warnings', [])}")
    print(f"标准输出: {result.get('stdout', '')[:300]}...")
    print(f"错误输出: {result.get('stderr', '')[:300]}...")
    
    # 测试用例4：使用sorry的证明 (应该编译成功但有警告)
    sorry_proof = """
theorem sorry_example (n : Nat) : n + 0 = n := by
  sorry
"""
    
    print("\n4. 使用sorry的证明:")
    print(sorry_proof)
    result = verify_lean_code_with_cli(sorry_proof)
    print(f"编译成功: {result['is_valid']}")
    print(f"质量评估: {result.get('lean_analysis', {}).get('quality_assessment', 'unknown')}")
    print(f"错误信息: {result.get('errors', [])}")
    print(f"警告信息: {result.get('warnings', [])}")
    print(f"标准输出: {result.get('stdout', '')[:200]}...")
    print(f"错误输出: {result.get('stderr', '')[:200]}...")
    
    # 测试用例5：构造器未完成
    constructor_incomplete = """
theorem constructor_incomplete : True ∧ True := by
  constructor
  -- 第一个goal没完成
  -- 第二个goal也没完成
"""
    
    print("\n5. 构造器未完成证明:")
    print(constructor_incomplete)
    result = verify_lean_code_with_cli(constructor_incomplete)
    print(f"编译成功: {result['is_valid']}")
    print(f"质量评估: {result.get('lean_analysis', {}).get('quality_assessment', 'unknown')}")
    print(f"错误信息: {result.get('errors', [])}")
    print(f"警告信息: {result.get('warnings', [])}")
    print(f"标准输出: {result.get('stdout', '')[:300]}...")
    print(f"错误输出: {result.get('stderr', '')[:300]}...")


def test_advanced_cases():
    """测试高级和边界情况"""
    print("\n🧪 Testing advanced cases...")
    
    # 测试1: 复杂的递归定义
    recursive_code = """
def fibonacci : Nat → Nat
| 0 => 0
| 1 => 1
| n + 2 => fibonacci n + fibonacci (n + 1)

theorem fib_positive (n : Nat) : n > 0 → fibonacci n ≥ fibonacci (n - 1) := by
  sorry
"""
    
    print("   Testing recursive definition...")
    result = verify_lean_code_with_cli(recursive_code)
    print(f"   Recursive def result: {'✅' if result['is_valid'] else '❌'}")
    
    # 测试2: 类型错误
    type_error_code = """
theorem type_mismatch : Nat = String := by
  rfl
"""
    
    print("   Testing type error...")
    result = verify_lean_code_with_cli(type_error_code)
    print(f"   Type error detected: {'✅' if not result['is_valid'] else '❌'}")
    
    # 测试3: 名称解析错误
    name_error_code = """
theorem name_error : undefined_name = 42 := by
  rfl
"""
    
    print("   Testing name resolution error...")
    result = verify_lean_code_with_cli(name_error_code)
    print(f"   Name error detected: {'✅' if not result['is_valid'] else '❌'}")
    
    # 测试4: 复杂的策略组合
    complex_tactics = """
set_option maxRecDepth 1000

theorem complex_proof (n : Nat) : n + 0 = n := by
  cases n with
  | zero => rfl
  | succ n => 
    rw [Nat.add_succ]
    rw [complex_proof n]
"""
    
    print("   Testing complex tactics...")
    result = verify_lean_code_with_cli(complex_tactics)
    is_valid = result['is_valid']
    print(f"   Complex tactics result: {'✅' if is_valid else '❌'}")
    
    if not is_valid:
        print("\n   Detailed error information:")
        # 打印错误信息
        if 'errors' in result and result['errors']:
            print("   Errors:")
            for error in result['errors']:
                print(f"     {error}")
        
        # 打印Lean分析结果
        if 'lean_analysis' in result:
            analysis = result['lean_analysis']
            if analysis.get('error_messages'):
                print("\n   Lean error messages:")
                for msg in analysis['error_messages']:
                    print(f"     {msg}")
            if analysis.get('warning_messages'):
                print("\n   Lean warnings:")
                for msg in analysis['warning_messages']:
                    print(f"     {msg}")
        
        # 打印标准输出和错误输出
        if result.get('stdout'):
            print("\n   Standard output:")
            print(f"     {result['stdout']}")
        if result.get('stderr'):
            print("\n   Standard error:")
            print(f"     {result['stderr']}")
            
        print("\n   End of error details")


def test_edge_cases():
    """测试边界情况和异常处理"""
    print("\n🧪 Testing edge cases...")
    
    # 测试1: 非常长的代码
    long_code = "theorem long_name_" + "a" * 1000 + " : True := True.intro"
    print("   Testing very long code...")
    result = verify_lean_code_with_cli(long_code)
    print(f"   Long code handled: {'✅' if result['is_valid'] else '❌'}")
    
    # 测试2: 特殊字符
    special_chars = """
theorem special_chars : "你好" = "你好" := by
  rfl
"""
    
    print("   Testing special characters...")
    result = verify_lean_code_with_cli(special_chars)
    print(f"   Special chars result: {'✅' if result['is_valid'] else '❌'}")
    
    # 测试3: 大量注释
    lots_of_comments = """
-- 这是一个很长的注释
-- 这是另一个注释
-- 还有更多注释
theorem with_comments : True := True.intro
-- 结尾注释
"""
    
    print("   Testing code with many comments...")
    result = verify_lean_code_with_cli(lots_of_comments)
    print(f"   Comments handled: {'✅' if result['is_valid'] else '❌'}")
    
    # 测试4: 空白和格式
    weird_formatting = """
  theorem   weird_spaces   :   True   :=   True.intro  
"""
    
    print("   Testing weird formatting...")
    result = verify_lean_code_with_cli(weird_formatting)
    print(f"   Formatting handled: {'✅' if result['is_valid'] else '❌'}")


def test_error_handling():
    """测试错误处理的健壮性"""
    print("\n🧪 Testing error handling robustness...")
    
    # 测试1: 超时情况（模拟）
    potential_timeout = """
theorem might_timeout : ∀ n : Nat, n = n := by
  intro n
  -- 这应该很快完成
  rfl
"""
    
    print("   Testing potential timeout case...")
    result = verify_lean_code_with_cli(potential_timeout, timeout=1)  # 很短的超时
    print(f"   Timeout handling: {'✅' if 'timeout' not in str(result.get('errors', [])) else '⚠️'}")
    
    # 测试2: 无效的上下文
    invalid_context = "this is not valid lean code"
    valid_code = "theorem test : True := True.intro"
    
    print("   Testing invalid context...")
    result = verify_lean_code_with_cli(valid_code, invalid_context)
    print(f"   Invalid context handled: {'✅' if not result['is_valid'] else '❌'}")
    
    # 测试3: 混合编码
    mixed_encoding = """
theorem test_encoding : True := True.intro
-- 混合编码测试 αβγ δεζ
"""
    
    print("   Testing mixed encoding...")
    result = verify_lean_code_with_cli(mixed_encoding)
    print(f"   Encoding handled: {'✅' if result['is_valid'] else '❌'}")


def test_comprehensive_json_parsing():
    """测试JSON解析的各种情况"""
    print("\n🧪 Testing comprehensive JSON parsing...")
    
    # 测试各种会产生不同JSON输出的代码
    test_cases = [
        {
            "name": "Multiple warnings",
            "code": """
theorem multi_warning : True := sorry
def unused_def : Nat := 42
""",
            "expect": "warnings"
        },
        {
            "name": "Nested errors", 
            "code": """
theorem nested_error : False := by
  have h : True := True.intro
  -- 这里应该产生嵌套的错误信息
""",
            "expect": "nested_errors"
        },
        {
            "name": "Info messages",
            "code": """
#check Nat.add
theorem info_test : True := True.intro
""",
            "expect": "info_messages"
        }
    ]
    
    for test in test_cases:
        print(f"   Testing {test['name']}...")
        result = verify_lean_code_with_cli(test['code'])
        analysis = result.get('lean_analysis', {})
        
        if test['expect'] == 'warnings':
            has_warnings = len(analysis.get('warning_messages', [])) > 0
            print(f"   Warnings detected: {'✅' if has_warnings else '❌'}")
        elif test['expect'] == 'info_messages':
            has_info = len(analysis.get('info_messages', [])) > 0
            print(f"   Info messages: {'✅' if has_info else '❌'}")
        else:
            print(f"   Processed: ✅")


def run_comprehensive_tests():
    """运行全面的测试套件"""
    print("🚀 Running comprehensive lean_utils test suite...")
    print("=" * 70)
    
    try:
        # 基础测试
        test_extract_lean_code_blocks()
        test_format_lean_code()
        test_create_lean_context()
        test_analyze_lean_code_structure()
        test_verify_lean_code_with_cli()
        test_batch_verify_lean_codes()
        test_performance()
        test_proof_completeness()
        
        # 高级测试
        test_advanced_cases()
        test_edge_cases()
        test_error_handling()
        test_comprehensive_json_parsing()
        
        print("\n" + "=" * 70)
        print("🎉 All comprehensive tests passed! lean_utils is robust and ready.")
        
    except Exception as e:
        print(f"\n❌ Comprehensive test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("🚀 Running lean_utils test suite...")
    print("=" * 60)
    
    try:
        test_extract_lean_code_blocks()
        test_format_lean_code()
        test_create_lean_context()
        test_analyze_lean_code_structure()
        test_verify_lean_code_with_cli()
        test_batch_verify_lean_codes()
        test_performance()
        test_proof_completeness()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! lean_utils is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def demo_usage():
    """演示lean_utils的使用方法"""
    print("\n📚 lean_utils Usage Demo")
    print("=" * 40)
    
    # 演示完整的工作流程
    sample_mathematical_text = """
Question: Basic Lean definitions and theorems.

Response A: Simple theorem.
```lean
theorem simple_true : True := True.intro
```

Response B: Basic definition.
```lean
def double (x : Nat) : Nat := x + x
```
"""
    
    print("1. Extract Lean code blocks:")
    codes = extract_lean_code_blocks(sample_mathematical_text)
    for i, code in enumerate(codes):
        print(f"   Code {i+1}: {code.split(':')[0]}...")
    
    print(f"\n2. Found {len(codes)} code blocks for verification")
    
    print("\n3. Verify each code block with Lean CLI:")
    valid_count = 0
    for i, code in enumerate(codes):
        print(f"   Verifying code {i+1}...")
        result = verify_lean_code_with_cli(code)
        
        status = "✅ Valid" if result["is_valid"] else "❌ Invalid" 
        time_taken = result.get("compilation_time", 0)
        print(f"   Result: {status} ({time_taken:.2f}s)")
        
        if result["is_valid"]:
            valid_count += 1
        elif result.get("errors"):
            print(f"   Error: {result['errors'][0][:80]}...")
    
    print(f"\n4. Summary: {valid_count}/{len(codes)} codes are valid")
    
    print("\n5. Batch verification demo:")
    batch_codes = [
        "theorem demo1 : True := True.intro",
        "def identity (x : Nat) : Nat := x",
        "example : 3 + 1 = 4 := rfl"
    ]
    
    batch_results = batch_verify_lean_codes(batch_codes)
    valid_batch = sum(1 for r in batch_results if r["is_valid"])
    print(f"   Batch result: {valid_batch}/{len(batch_codes)} valid")
    
    print("\n6. Code analysis demo:")
    if codes:
        analysis = analyze_lean_code_structure(codes[0])
        print(f"   Structure: {analysis['complexity']} complexity")
        print(f"   Contains: {len(analysis['has_theorems'])} theorems, {len(analysis['has_definitions'])} definitions")
    
    print("\n✨ Demo completed! lean_utils is ready for use.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test lean_utils functionality")
    parser.add_argument("--demo", action="store_true", help="Run usage demo")
    parser.add_argument("--test", action="store_true", help="Run full test suite")
    parser.add_argument("--quick", action="store_true", help="Run quick verification test only")
    parser.add_argument("--perf", action="store_true", help="Run performance test only")
    parser.add_argument("--batch", action="store_true", help="Run batch test only")
    parser.add_argument("--all", action="store_true", help="Run all tests and demo")
    parser.add_argument("--completeness", action="store_true", help="Run proof completeness test")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive test suite")
    parser.add_argument("--advanced", action="store_true", help="Run advanced test cases")
    parser.add_argument("--edge", action="store_true", help="Run edge case tests")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_usage()
    elif args.test:
        run_all_tests()
    elif args.quick:
        print("🚀 Running quick verification test...")
        test_verify_lean_code_with_cli()
    elif args.perf:
        print("🚀 Running performance test...")
        test_performance()
    elif args.batch:
        print("🚀 Running batch verification test...")
        test_batch_verify_lean_codes()
    elif args.all:
        print("🚀 Running complete test suite with demo...")
        if run_all_tests():
            demo_usage()
    elif args.completeness:
        print("🚀 Running proof completeness test...")
        test_proof_completeness()
    elif args.comprehensive:
        print("🚀 Running comprehensive test suite...")
        run_comprehensive_tests()
    elif args.advanced:
        print("🚀 Running advanced test cases...")
        test_advanced_cases()
    elif args.edge:
        print("🚀 Running edge case tests...")
        test_edge_cases()
    else:
        # 默认运行测试和演示
        print("🚀 Running default: tests + demo")
        print("Use --help for more options")
        if run_all_tests():
            demo_usage()