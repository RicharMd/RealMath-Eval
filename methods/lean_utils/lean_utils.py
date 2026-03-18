"""
Lean代码处理的辅助函数
包含代码提取、格式化、上下文创建等功能

主要功能：
1. extract_lean_code_blocks - 从文本中提取Lean代码块
2. format_lean_code - 格式化Lean代码
3. create_lean_context - 创建Lean上下文环境
4. analyze_lean_code_structure - 分析代码结构
5. verify_lean_code_with_cli - 使用Lean CLI验证代码 (核心功能)
6. batch_verify_lean_codes - 批量验证代码
"""

import re
from typing import List, Dict, Any, Optional


def extract_lean_code_blocks(text: str) -> List[str]:
    """
    从文本中提取Lean代码块
    
    Args:
        text: 包含Lean代码的文本
        
    Returns:
        List[str]: 提取的Lean代码块列表
    """
    
    lean_codes = []
    
    # 只匹配明确标记为lean的代码块
    lean_pattern = r'```(?:lean|Lean)\n(.*?)\n```'
    matches = re.findall(lean_pattern, text, re.DOTALL | re.IGNORECASE)
    lean_codes.extend(matches)
    
    # 去重并清理
    cleaned_codes = []
    for code in lean_codes:
        cleaned = code.strip()
        if cleaned and cleaned not in cleaned_codes:
            cleaned_codes.append(cleaned)
    
    return cleaned_codes





def format_lean_code(lean_code: str, add_imports: bool = True) -> str:
    """
    格式化Lean代码
    
    Args:
        lean_code: 原始Lean代码
        add_imports: 是否添加常用导入
        
    Returns:
        str: 格式化后的Lean代码
    """
    
    lines = lean_code.strip().split('\n')
    formatted_lines = []
    
    # 清理每一行
    for line in lines:
        # 移除行尾空格
        cleaned_line = line.rstrip()
        formatted_lines.append(cleaned_line)
    
    # 移除空的开头和结尾行
    while formatted_lines and not formatted_lines[0].strip():
        formatted_lines.pop(0)
    while formatted_lines and not formatted_lines[-1].strip():
        formatted_lines.pop()
    
    formatted_code = '\n'.join(formatted_lines)
    
    # 添加导入（如果需要且不存在）
    if add_imports and not formatted_code.startswith('import'):
        imports = [
            "import Mathlib.Data.Real.Basic",
            "import Mathlib.Data.Nat.Basic",
            "import Mathlib.Tactic"
        ]
        formatted_code = '\n'.join(imports) + '\n\n' + formatted_code
    
    return formatted_code


def create_lean_context(problem_description: str = "", 
                       additional_definitions: str = "") -> str:
    """
    创建Lean代码的上下文环境
    
    Args:
        problem_description: 问题描述
        additional_definitions: 额外的定义
        
    Returns:
        str: Lean上下文代码
    """
    
    context_parts = []
    
    # 基础导入
    basic_imports = [
        "import Mathlib.Data.Real.Basic",
        "import Mathlib.Data.Nat.Basic",
        "import Mathlib.Data.Int.Basic",
        "import Mathlib.Algebra.BigOperators.Basic",
        "import Mathlib.Tactic"
    ]
    
    context_parts.extend(basic_imports)
    context_parts.append("")
    
    # 问题描述（作为注释）
    if problem_description.strip():
        context_parts.append("/-")
        context_parts.append(f"Problem: {problem_description}")
        context_parts.append("-/")
        context_parts.append("")
    
    # 额外定义
    if additional_definitions.strip():
        context_parts.append("-- Additional definitions")
        context_parts.append(additional_definitions.strip())
        context_parts.append("")
    
    # 常用简写和定义
    common_definitions = [
        "-- Common mathematical definitions",
        "open Real",
        "open Nat",
        ""
    ]
    
    context_parts.extend(common_definitions)
    
    return '\n'.join(context_parts)


def analyze_lean_code_structure(lean_code: str) -> Dict[str, Any]:
    """
    分析Lean代码的结构
    
    Args:
        lean_code: Lean代码
        
    Returns:
        Dict[str, Any]: 代码结构分析结果
    """
    
    analysis = {
        "has_imports": False,
        "has_theorems": [],
        "has_definitions": [],
        "has_examples": [],
        "has_tactics": [],
        "line_count": 0,
        "complexity": "simple"
    }
    
    lines = lean_code.split('\n')
    analysis["line_count"] = len([l for l in lines if l.strip()])
    
    # 检查导入
    if any(line.strip().startswith('import') for line in lines):
        analysis["has_imports"] = True
    
    # 查找定理、定义等
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('theorem'):
            theorem_name = _extract_name_from_declaration(line_stripped)
            if theorem_name:
                analysis["has_theorems"].append(theorem_name)
        
        elif line_stripped.startswith('def'):
            def_name = _extract_name_from_declaration(line_stripped)
            if def_name:
                analysis["has_definitions"].append(def_name)
        
        elif line_stripped.startswith('example'):
            analysis["has_examples"].append(f"line_{lines.index(line)+1}")
        
        # 检查策略使用
        tactics = ['by', 'exact', 'rw', 'simp', 'apply', 'have', 'show']
        for tactic in tactics:
            if tactic in line_stripped and tactic not in analysis["has_tactics"]:
                analysis["has_tactics"].append(tactic)
    
    # 评估复杂度
    complexity_score = 0
    complexity_score += len(analysis["has_theorems"]) * 3
    complexity_score += len(analysis["has_definitions"]) * 2
    complexity_score += len(analysis["has_examples"]) * 1
    complexity_score += len(analysis["has_tactics"]) * 1
    complexity_score += analysis["line_count"] // 10
    
    if complexity_score < 5:
        analysis["complexity"] = "simple"
    elif complexity_score < 15:
        analysis["complexity"] = "medium"
    else:
        analysis["complexity"] = "complex"
    
    return analysis


def _extract_name_from_declaration(declaration_line: str) -> Optional[str]:
    """从声明行中提取名称"""
    
    # 匹配 "theorem name" 或 "def name" 等模式
    match = re.search(r'(?:theorem|def|lemma)\s+([a-zA-Z_][a-zA-Z0-9_]*)', declaration_line)
    if match:
        return match.group(1)
    
    return None


# ========== 核心验证功能 ==========

def verify_lean_code_with_cli(lean_code: str, context: str = "", timeout: int = 30) -> Dict[str, Any]:
    """
    使用Lean CLI直接验证Lean代码
    
    Args:
        lean_code: 要验证的Lean代码
        context: 额外的上下文代码
        timeout: 超时时间（秒）
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    
    import tempfile
    import subprocess
    import os
    import time
    
    start_time = time.time()
    
    # 检查空代码
    if not lean_code.strip():
        return {
            "is_valid": False,
            "errors": ["Empty Lean code provided"],
            "warnings": [],
            "compilation_time": time.time() - start_time,
            "method": "lean_cli"
        }
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 构建完整的Lean代码（不依赖Mathlib）
            full_code_parts = [
                "-- Basic Lean 4 code",
                ""
            ]
            
            if context.strip():
                full_code_parts.extend([
                    "-- Context code",
                    context.strip(),
                    ""
                ])
            
            full_code_parts.extend([
                "-- Main code",
                lean_code.strip()
            ])
            
            full_code = "\n".join(full_code_parts)
            
            # 创建临时的Lean文件
            lean_file = os.path.join(temp_dir, "test.lean")
            with open(lean_file, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            # 创建基础的lakefile.lean
            lakefile = os.path.join(temp_dir, "lakefile.lean")
            with open(lakefile, 'w', encoding='utf-8') as f:
                f.write("""import Lake
open Lake DSL

package test

@[default_target]
lean_lib Test
""")
            
            # 第一步：基础编译检查 (使用JSON输出获取结构化信息)
            json_cmd = ["lean", lean_file, "--json"]
            json_process = subprocess.run(
                json_cmd,
                text=True,
                capture_output=True,
                timeout=timeout // 2,
                cwd=temp_dir
            )
            
            # 第二步：带统计信息的编译 (获取更详细的诊断)
            stats_cmd = ["lean", lean_file, "--stats", "--profile"]
            stats_process = subprocess.run(
                stats_cmd,
                text=True,
                capture_output=True,
                timeout=timeout // 2,
                cwd=temp_dir
            )
            
            compilation_time = time.time() - start_time
            
            # 解析Lean的输出 (使用实际存在的功能)
            lean_analysis = parse_lean_output_realistic(
                json_process.stdout, 
                json_process.stderr,
                stats_process.stdout,
                stats_process.stderr,
                lean_code
            )
            
            # 解析结果
            if json_process.returncode == 0:
                # 成功编译
                warnings = []
                if json_process.stderr:
                    warnings.append(f"Lean output: {json_process.stderr.strip()}")
                
                # 基于Lean输出的分析
                if lean_analysis["has_issues"]:
                    warnings.extend(lean_analysis["issue_warnings"])
                
                return {
                    "is_valid": True,
                    "lean_analysis": lean_analysis,
                    "errors": [],
                    "warnings": warnings,
                    "compilation_time": compilation_time,
                    "method": "lean_cli_enhanced",
                    "stdout": json_process.stdout.strip() if json_process.stdout else "",
                    "stderr": json_process.stderr.strip() if json_process.stderr else ""
                }
            else:
                # 编译失败
                errors = []
                if json_process.stderr:
                    errors.append(json_process.stderr.strip())
                if json_process.stdout:
                    errors.append(json_process.stdout.strip())
                if not errors:
                    errors.append(f"Lean compilation failed with exit code {json_process.returncode}")
                
                return {
                    "is_valid": False,
                    "lean_analysis": lean_analysis,
                    "errors": errors,
                    "warnings": [],
                    "compilation_time": compilation_time,
                    "method": "lean_cli_enhanced",
                    "exit_code": json_process.returncode
                }
    
    except subprocess.TimeoutExpired:
        return {
            "is_valid": False,
            "errors": [f"Lean compilation timeout after {timeout} seconds"],
            "warnings": [],
            "compilation_time": timeout,
            "method": "lean_cli_enhanced",
            "error_type": "timeout"
        }
    
    except FileNotFoundError:
        return {
            "is_valid": False,
            "errors": ["Lean CLI not found. Please install Lean 4."],
            "warnings": [],
            "compilation_time": time.time() - start_time,
            "method": "lean_cli_enhanced",
            "error_type": "environment"
        }
    
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Unexpected error: {str(e)}"],
            "warnings": [],
            "compilation_time": time.time() - start_time,
            "method": "lean_cli_enhanced",
            "error_type": "environment"
        }


def parse_lean_output_realistic(json_stdout: str, json_stderr: str, 
                               stats_stdout: str, stats_stderr: str, 
                               original_code: str) -> Dict[str, Any]:
    """
    解析Lean编译器的实际输出，使用Lean 4真实支持的功能
    
    Args:
        json_stdout: JSON格式输出的标准输出
        json_stderr: JSON格式输出的错误输出  
        stats_stdout: 统计信息输出
        stats_stderr: 统计信息错误输出
        original_code: 原始代码
        
    Returns:
        Dict[str, Any]: 基于实际Lean输出的分析结果
    """
    
    import json as json_lib
    
    analysis = {
        "has_issues": False,
        "issue_warnings": [],
        "json_messages": [],
        "error_messages": [],
        "warning_messages": [],
        "info_messages": [],
        "stats_info": {},
        "lean_diagnostics": {},
        "quality_assessment": "unknown",
        "analysis_method": "lean_realistic_output"
    }
    
    # 解析JSON输出 (如果有的话)
    if json_stdout:
        try:
            for line in json_stdout.split('\n'):
                if line.strip():
                    try:
                        json_msg = json_lib.loads(line)
                        analysis["json_messages"].append(json_msg)
                        
                        # 分析消息类型
                        if 'severity' in json_msg:
                            severity = json_msg['severity']
                            message_text = json_msg.get('message', '')
                            
                            if severity == 'error':
                                analysis["error_messages"].append(message_text)
                                analysis["has_issues"] = True
                            elif severity == 'warning':
                                analysis["warning_messages"].append(message_text)
                                # 某些警告也表示问题
                                if any(keyword in message_text.lower() for keyword in ['sorry', 'admit', 'incomplete']):
                                    analysis["has_issues"] = True
                                    analysis["issue_warnings"].append(f"Potential incomplete proof: {message_text}")
                            elif severity == 'info':
                                analysis["info_messages"].append(message_text)
                                
                    except json_lib.JSONDecodeError:
                        continue
                        
        except Exception as e:
            analysis["issue_warnings"].append(f"Error parsing JSON output: {str(e)}")
    
    # 解析stderr中的普通诊断信息
    if json_stderr:
        stderr_lines = json_stderr.split('\n')
        for line in stderr_lines:
            line = line.strip()
            if line:
                # Lean 4的标准错误信息格式
                if any(marker in line.lower() for marker in ['error:', 'warning:', 'info:']):
                    if 'error:' in line.lower():
                        analysis["error_messages"].append(line)
                        analysis["has_issues"] = True
                    elif 'warning:' in line.lower():
                        analysis["warning_messages"].append(line)
                        # 检查是否是证明相关的警告
                        if any(keyword in line.lower() for keyword in ['sorry', 'admit', 'goal', 'proof']):
                            analysis["has_issues"] = True
                            analysis["issue_warnings"].append(line)
    
    # 解析统计信息
    if stats_stdout:
        # 提取有用的统计信息
        stats_lines = stats_stdout.split('\n')
        for line in stats_lines:
            if 'elaboration time' in line.lower() or 'checking time' in line.lower():
                analysis["stats_info"]["timing"] = line.strip()
            elif 'memory' in line.lower():
                analysis["stats_info"]["memory"] = line.strip()
    
    # 基于实际分析评估质量
    if len(analysis["error_messages"]) > 0:
        analysis["quality_assessment"] = "invalid"
    elif analysis["has_issues"]:
        analysis["quality_assessment"] = "incomplete_or_problematic"  
    elif len(analysis["warning_messages"]) > 0:
        analysis["quality_assessment"] = "valid_with_warnings"
    else:
        analysis["quality_assessment"] = "valid"
    
    # 诊断统计
    analysis["lean_diagnostics"] = {
        "error_count": len(analysis["error_messages"]),
        "warning_count": len(analysis["warning_messages"]),
        "info_count": len(analysis["info_messages"]),
        "json_message_count": len(analysis["json_messages"]),
        "has_stats": bool(analysis["stats_info"])
    }
    
    return analysis


def batch_verify_lean_codes(lean_codes: List[str], context: str = "", 
                           timeout_per_code: int = 30) -> List[Dict[str, Any]]:
    """
    批量验证多个Lean代码块
    
    Args:
        lean_codes: Lean代码列表
        context: 共同的上下文
        timeout_per_code: 每个代码的超时时间
        
    Returns:
        List[Dict[str, Any]]: 验证结果列表
    """
    
    results = []
    
    for i, lean_code in enumerate(lean_codes):
        print(f"Verifying code block {i+1}/{len(lean_codes)}...")
        result = verify_lean_code_with_cli(lean_code, context, timeout_per_code)
        results.append(result)
    
    return results


# ========== 向后兼容性和已废弃功能 ==========

# 保持向后兼容性的别名
verify_lean_code_with_dojo = verify_lean_code_with_cli

# # ========== LeanDojo 相关代码 (已废弃) ==========
# # 
# # 以下代码是之前使用LeanDojo的实现，现在已经被更简单的CLI方案替代
# # 保留在这里仅供参考，实际使用请使用 verify_lean_code_with_cli
# #
# # def verify_lean_code_with_dojo_original(lean_code: str, context: str = "", timeout: int = 30) -> Dict[str, Any]:
# #     """
# #     使用LeanDojo验证Lean代码 (已废弃)
# #     
# #     此函数已被 verify_lean_code_with_cli 替代，原因：
# #     1. LeanDojo依赖复杂，配置困难
# #     2. 需要下载traced repositories
# #     3. 直接CLI调用更简单可靠
# #     """
# #     
# #     try:
# #         from lean_dojo import LeanGitRepo, Dojo, LeanError
# #         import time
# #         
# #         start_time = time.time()
# #         
# #         # 使用LeanDojo的示例仓库
# #         repo = LeanGitRepo("https://github.com/yangky11/lean4-example", "...")
# #         entry = (repo, "Lean4Example.lean", 1)
# #         
# #         with Dojo(entry, timeout=timeout) as (dojo, init_state):
# #             # ... LeanDojo相关实现
# #             pass
# #             
# #     except Exception as e:
# #         return {
# #             "is_valid": False,
# #             "errors": [f"LeanDojo error: {str(e)}"],
# #             "method": "leandojo_deprecated"
# #         }

# 保留简化版本的analyze_proof_completeness作为备用
def analyze_proof_completeness_simple(lean_code: str) -> Dict[str, Any]:
    """
    简单的证明完整性分析（备用方法）
    
    注意：这个方法只做基础的字符串匹配，不如基于Lean输出的分析科学
    仅在无法获取Lean详细输出时使用
    """
    
    analysis = {
        "has_sorry": False,
        "sorry_count": 0,
        "has_admit": False, 
        "admit_count": 0,
        "method": "simple_string_matching",
        "warning": "This is a simplified analysis based on string matching, not scientific proof verification"
    }
    
    lines = lean_code.split('\n')
    
    for line in lines:
        line_stripped = line.strip().lower()
        
        # 检查 sorry
        if 'sorry' in line_stripped:
            analysis["has_sorry"] = True
            analysis["sorry_count"] += line_stripped.count('sorry')
        
        # 检查 admit  
        if 'admit' in line_stripped:
            analysis["has_admit"] = True 
            analysis["admit_count"] += line_stripped.count('admit')
    
    return analysis