# RUG 深度覆盖率报告: `rust-crc32fast_gemini-2.5-flash-nothinking_20251109_235808`

> **检测时间**: 2025年11月19日 星期三 23时13分28秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 41
- **通过**: 35
- **失败**: 6
- **忽略**: 0

### ❌ 失败测试详情

#### `combine::tests_rug_8::test_multiply_specific_values`
- **位置**: `src/combine.rs:103:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: 3590622373
 right: 4085188353
```
#### `combine::tests_rug_8::test_multiply_with_poly`
- **位置**: `src/combine.rs:96:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: 2852767883
 right: 1992562952
```
#### `combine::tests_rug_8::test_multiply_identity`
- **位置**: `src/combine.rs:79:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: 2852767883
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```
#### `combine::tests_rug_8::test_multiply_powers_of_x`
- **位置**: `src/combine.rs:85:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: 2405603159
 right: 2
```
#### `combine::tests_rug_9::test_combine_medium_len2`
- **位置**: `src/combine.rs:151:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: 1736612752
 right: 99463401
```
#### `combine::tests_rug_9::test_combine_small_len2`
- **位置**: `src/combine.rs:141:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: 1033773249
 right: 977292288


failures:
    combine::tests_rug_8::test_multiply_identity
    combine::tests_rug_8::test_multiply_powers_of_x
    combine::tests_rug_8::test_multiply_specific_values
    combine::tests_rug_8::test_multiply_with_poly
```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **93.93%** | 🟢 优秀 | 356/379 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **87.50%** | 🟡 良好 | 7/8 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **97.14%** | 🟢 优秀 | 68/70 | 未被调用的函数数量 |

## 2. 🚨 重点关注文件 (Top Risky Files)
以下文件代码量较大但**分支覆盖率较低**，建议优先补充测试用例：

| 文件路径 | 分支覆盖率 | 缺失分支数 | 代码行数 |
| :--- | :---: | :---: | :---: |
| `src/lib.rs` | **50.00%** | 1 | 123 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/specialized/aarch64.rs` | 97.6% <br><sub style='color:gray'>(41/42)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(9/9)</sub> |
| `src/specialized/mod.rs` | 100.0% <br><sub style='color:gray'>(18/18)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(4/4)</sub> |
| `src/lib.rs` | 91.9% <br><sub style='color:gray'>(113/123)</sub> | 🟠 50.0% <br><sub style='color:gray'>(1/2)</sub> | 92.9% <br><sub style='color:gray'>(26/28)</sub> |
| `src/baseline.rs` | 100.0% <br><sub style='color:gray'>(109/109)</sub> | 100.0% <br><sub style='color:gray'>(2/2)</sub> | 100.0% <br><sub style='color:gray'>(15/15)</sub> |
| `src/combine.rs` | 86.2% <br><sub style='color:gray'>(75/87)</sub> | 100.0% <br><sub style='color:gray'>(4/4)</sub> | 100.0% <br><sub style='color:gray'>(14/14)</sub> |
