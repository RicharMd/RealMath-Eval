# lean_utils 🧮

**一个轻量级的Lean4代码处理工具包，基于LeanDojo集成**

## ✨ 特性

- 🔍 **代码提取**: 从文本中提取Lean代码块
- 🎨 **代码格式化**: 清理和标准化Lean代码
- ⚡ **真实验证**: 使用LeanDojo调用真正的Lean编译器
- 📊 **批量处理**: 同时验证多个代码块
- 🔧 **代码分析**: 分析Lean代码结构和复杂度

## 🚀 快速开始

### 基本使用

```python
from methods.lean_utils import verify_lean_code_with_dojo

# 验证Lean代码
result = verify_lean_code_with_dojo("theorem test : 2 + 2 = 4 := by simp")
print(f"Valid: {result['is_valid']}")
print(f"Errors: {result['errors']}")
print(f"Time: {result['compilation_time']:.2f}s")
```

### 批量验证

```python
from methods.lean_utils import batch_verify_lean_codes

codes = [
    "theorem test1 : 1 + 1 = 2 := by simp",
    "def double (x : ℕ) : ℕ := x + x",
    "theorem broken : 1 = 2 := by simp"  # Will fail
]

results = batch_verify_lean_codes(codes)
for i, result in enumerate(results):
    status = "✅" if result["is_valid"] else "❌"
    print(f"Code {i+1}: {status}")
```

### 代码提取

```python
from methods.lean_utils import extract_lean_code_blocks

text = """
Here's a theorem:
```lean
theorem example : 1 + 1 = 2 := by simp
```
"""

codes = extract_lean_code_blocks(text)
print(f"Found {len(codes)} Lean code blocks")
```

## 🧪 测试

运行完整测试套件：
```bash
cd methods/lean_utils
python test_lean_utils.py --test
```

运行快速验证测试：
```bash
python test_lean_utils.py --quick
```

查看演示：
```bash
python test_lean_utils.py --demo
```

测试选项：
- `--test`: 完整测试套件
- `--quick`: 快速验证测试
- `--perf`: 性能测试
- `--batch`: 批量测试
- `--demo`: 使用演示
- `--all`: 所有测试+演示

## 📋 API 参考

### `verify_lean_code_with_dojo(lean_code, context="", timeout=30)`
使用LeanDojo验证Lean代码

**参数:**
- `lean_code` (str): 要验证的Lean代码
- `context` (str): 可选上下文代码
- `timeout` (int): 超时时间（秒）

**返回:** dict 包含验证结果

### `batch_verify_lean_codes(lean_codes, context="", timeout_per_code=30)`
批量验证多个Lean代码块

**参数:**
- `lean_codes` (List[str]): Lean代码列表
- `context` (str): 共享上下文
- `timeout_per_code` (int): 每个代码的超时时间

**返回:** List[dict] 验证结果列表

### `extract_lean_code_blocks(text)`
从文本中提取标记为lean的代码块

**参数:**
- `text` (str): 包含代码的文本

**返回:** List[str] 提取的代码块

### `analyze_lean_code_structure(lean_code)`
分析Lean代码结构

**参数:**
- `lean_code` (str): 要分析的代码

**返回:** dict 包含结构信息

### `format_lean_code(lean_code, add_imports=True)`
格式化Lean代码

**参数:**
- `lean_code` (str): 原始代码
- `add_imports` (bool): 是否添加常用导入

**返回:** str 格式化后的代码

## 🔧 技术细节

### 验证方法
- **LeanDojo**: 使用真正的Lean编译器进行验证
- **Command模式**: 通过LeanDojo的command接口执行代码
- **错误检测**: 捕获编译错误和语法错误

### 性能
- 平均验证时间：2-5秒
- 支持超时控制
- 自动错误分类

### 错误处理
- 编译错误 vs 环境错误分类
- 详细错误信息
- 优雅降级

## 🏗️ 架构

```
lean_utils/
├── __init__.py          # 包入口
├── lean_utils.py        # 主要功能实现
├── test_lean_utils.py   # 测试套件
└── README_UPDATED.md    # 本文档
```

## 🤝 与LeanDojo集成

本包基于[LeanDojo](https://github.com/lean-dojo/LeanDojo)构建，提供：
- 真正的Lean编译器调用
- 高质量的验证结果
- 完整的错误报告

## 📝 示例输出

```python
{
    "is_valid": True,
    "errors": [],
    "warnings": ["Successfully executed in LeanDojo"],
    "compilation_time": 2.45,
    "method": "leandojo_command",
    "state_id": 1
}
```

---

**简单、可靠、高效** - lean_utils让Lean代码验证变得简单！ 