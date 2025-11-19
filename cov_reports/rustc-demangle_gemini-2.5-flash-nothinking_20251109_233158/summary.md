# RUG 深度覆盖率报告: `rustc-demangle_gemini-2.5-flash-nothinking_20251109_233158`

> **检测时间**: 2025年11月19日 星期三 23时13分26秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 91
- **通过**: 90
- **失败**: 1
- **忽略**: 0

### ❌ 失败测试详情

#### `tests_rug_44::test_rug`
- **位置**: `src/lib.rs:611:9`
- **错误信息**:
```text
assertion failed: demangled_result.is_ok()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    tests_rug_44::test_rug

test result: FAILED. 90 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.03s

error: test failed, to rerun pass `-p rustc-demangle --lib`
```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **92.26%** | 🟢 优秀 | 1620/1756 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **78.85%** | 🟡 良好 | 205/260 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **97.51%** | 🟢 优秀 | 196/201 | 未被调用的函数数量 |

## 2. 🚨 重点关注文件 (Top Risky Files)
以下文件代码量较大但**分支覆盖率较低**，建议优先补充测试用例：

| 文件路径 | 分支覆盖率 | 缺失分支数 | 代码行数 |
| :--- | :---: | :---: | :---: |
| `src/v0.rs` | **76.11%** | 43 | 1043 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `crates/capi/src/lib.rs` | 99.0% <br><sub style='color:gray'>(97/98)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(9/9)</sub> |
| `src/v0.rs` | 91.6% <br><sub style='color:gray'>(955/1043)</sub> | 🟠 76.1% <br><sub style='color:gray'>(137/180)</sub> | 98.3% <br><sub style='color:gray'>(113/115)</sub> |
| `src/lib.rs` | 90.1% <br><sub style='color:gray'>(290/322)</sub> | 80.0% <br><sub style='color:gray'>(24/30)</sub> | 93.3% <br><sub style='color:gray'>(42/45)</sub> |
| `src/legacy.rs` | 93.7% <br><sub style='color:gray'>(207/221)</sub> | 87.5% <br><sub style='color:gray'>(42/48)</sub> | 100.0% <br><sub style='color:gray'>(29/29)</sub> |
| `crates/native-c/src/lib.rs` | 98.6% <br><sub style='color:gray'>(71/72)</sub> | 100.0% <br><sub style='color:gray'>(2/2)</sub> | 100.0% <br><sub style='color:gray'>(3/3)</sub> |
