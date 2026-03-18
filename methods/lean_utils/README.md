 # Lean Utils 📝

一个用于处理Lean4代码的Python工具包，提供代码提取、格式化、验证等功能。

## 功能特性 🚀

### 1. **Lean代码验证** (`lean_compiler.py`)
- 使用LeanDojo或Lean CLI验证Lean4代码
- 自动降级策略：LeanDojo → Lean CLI → 语法检查
- 批量验证支持

### 2. **代码处理工具** (`lean_utils.py`)
- 从文本中提取Lean代码块
- 代码格式化和清理
- 生成Lean上下文环境
- 代码结构分析

## 安装和设置 ⚙️

### 依赖要求
```bash
# 基础Python依赖
pip install typing re

# 可选：LeanDojo (推荐)
pip install lean-dojo

# 可选：Lean4 CLI
# 从 https://github.com/leanprover/lean4 安装
```

### 快速测试
```bash
cd methods/lean_utils
python test_lean_utils.py          # 运行完整测试
python test_lean_utils.py --test   # 只运行测试
python test_lean_utils.py --demo   # 只运行演示
```

## 使用方法 📚

### 基础代码验证
```python
from methods.lean_utils import verify_lean_code

# 验证简单的Lean代码
code = "theorem simple : 2 + 2 = 4 := by simp"
result = verify_lean_code(code)

print(f"Valid: {result.is_valid}")
print(f"Errors: {result.errors}")
print(f"Method: {result.method}")
```

### 从文本提取Lean代码
```python
from methods.lean_utils import extract_lean_code_blocks

text = """
Here's a proof:
```lean
theorem test : 1 + 1 = 2 := by simp
```
"""

codes = extract_lean_code_blocks(text)
print(f"Found {len(codes)} code blocks")
```

### 批量验证
```python
from methods.lean_utils import batch_verify_lean_codes

codes = [
    "theorem test1 : 1 + 1 = 2 := by simp",
    "def double (x : ℕ) : ℕ := x + x"
]

results = batch_verify_lean_codes(codes)
for i, result in enumerate(results):
    print(f"Code {i+1}: {result}")
```

### 代码格式化
```python
from methods.lean_utils import format_lean_code

messy_code = """
    theorem test : 2 + 2 = 4 := by simp   
    
"""

clean_code = format_lean_code(messy_code, add_imports=True)
print(clean_code)
```

### 创建上下文环境
```python
from methods.lean_utils import create_lean_context

context = create_lean_context(
    problem_description="Prove x^2 ≥ 0",
    additional_definitions="def square (x : ℝ) : ℝ := x * x"
)
print(context)
```

### 分析代码结构
```python
from methods.lean_utils import analyze_lean_code_structure

code = """
theorem test (x : ℝ) : x^2 ≥ 0 := by
  exact sq_nonneg x
"""

analysis = analyze_lean_code_structure(code)
print(f"Theorems: {analysis['has_theorems']}")
print(f"Complexity: {analysis['complexity']}")
```

## API 参考 📖

### `verify_lean_code(lean_code, context="", timeout=30)`
验证Lean4代码并返回详细结果。

**参数:**
- `lean_code` (str): 要验证的Lean代码
- `context` (str): 额外上下文代码
- `timeout` (int): 验证超时时间（秒）

**返回:** `LeanCompilerResult` 对象

### `extract_lean_code_blocks(text)`
从文本中提取所有Lean代码块。

**参数:**
- `text` (str): 包含Lean代码的文本

**返回:** `List[str]` - 提取的代码块列表

### `format_lean_code(lean_code, add_imports=True)`
格式化Lean代码。

**参数:**
- `lean_code` (str): 原始Lean代码
- `add_imports` (bool): 是否添加常用导入

**返回:** `str` - 格式化后的代码

### `create_lean_context(problem_description="", additional_definitions="")`
创建Lean代码的上下文环境。

**参数:**
- `problem_description` (str): 问题描述
- `additional_definitions` (str): 额外定义

**返回:** `str` - Lean上下文代码

### `analyze_lean_code_structure(lean_code)`
分析Lean代码的结构。

**参数:**
- `lean_code` (str): 要分析的Lean代码

**返回:** `Dict[str, Any]` - 结构分析结果

## 验证方法 🔧

lean_utils支持多种验证方法，按优先级自动选择：

1. **LeanDojo** (最佳)
   - 专为ML/AI设计
   - Python原生API
   - 最佳性能和错误处理

2. **Lean CLI** (备选)
   - 直接调用Lean4编译器
   - 准确的编译结果
   - 需要系统安装Lean4

3. **语法检查** (兜底)
   - 基础语法验证
   - 不需要外部依赖
   - 有限的验证能力

## 集成示例 🔗

### 在LeanJudge中使用
```python
from methods.lean_utils import verify_lean_code, extract_lean_code_blocks

class EnhancedLeanJudge:
    def analyze_with_compiler(self, query):
        # 提取Lean代码
        codes = extract_lean_code_blocks(query)
        
        # 验证每个代码块
        verification_results = []
        for code in codes:
            result = verify_lean_code(code)
            verification_results.append(result.to_dict())
        
        return verification_results
```

## 故障排除 🔧

### 常见问题

1. **LeanDojo导入失败**
   ```
   解决: pip install lean-dojo
   自动降级到Lean CLI或语法检查
   ```

2. **Lean CLI不可用**
   ```
   解决: 安装Lean4编译器
   或使用LeanDojo作为替代
   ```

3. **编译超时**
   ```
   解决: 增加timeout参数
   或简化Lean代码复杂度
   ```

## 测试覆盖 ✅

测试文件 `test_lean_utils.py` 包含：
- ✅ 代码提取功能测试
- ✅ 格式化功能测试  
- ✅ 上下文创建测试
- ✅ 结构分析测试
- ✅ 环境设置测试
- ✅ 代码验证测试
- ✅ 批量验证测试
- ✅ 使用演示

## 贡献指南 🤝

1. 运行测试确保现有功能正常
2. 添加新功能时包含相应测试
3. 保持向后兼容性
4. 更新文档说明

## License 📄

[你的许可证信息]