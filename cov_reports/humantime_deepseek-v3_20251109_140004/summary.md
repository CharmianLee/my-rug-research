# RUG 深度覆盖率报告: `humantime_deepseek-v3_20251109_140004`

> **检测时间**: 2025年11月19日 星期三 23时13分15秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 63
- **通过**: 62
- **失败**: 1
- **忽略**: 0

### ❌ 失败测试详情

#### `duration::tests_rug_1::test_complex_combination`
- **位置**: `src/duration.rs:488:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: Ok(38995999.00800901s)
 right: Ok(39059647.00800901s)


failures:
    duration::tests_rug_1::test_complex_combination

test result: FAILED. 62 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.20s

```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **95.36%** | 🟢 优秀 | 740/776 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **87.27%** | 🟡 良好 | 96/110 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **96.12%** | 🟢 优秀 | 99/103 | 未被调用的函数数量 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/wrapper.rs` | 80.9% <br><sub style='color:gray'>(38/47)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 83.3% <br><sub style='color:gray'>(15/18)</sub> |
| `src/duration.rs` | 94.8% <br><sub style='color:gray'>(276/291)</sub> | 85.7% <br><sub style='color:gray'>(24/28)</sub> | 100.0% <br><sub style='color:gray'>(31/31)</sub> |
| `src/date.rs` | 97.3% <br><sub style='color:gray'>(426/438)</sub> | 87.8% <br><sub style='color:gray'>(72/82)</sub> | 98.1% <br><sub style='color:gray'>(53/54)</sub> |
