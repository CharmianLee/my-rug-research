# RUG 深度覆盖率报告: `humantime_gpt-4.1-mini_20251109_001052`

> **检测时间**: 2025年11月19日 星期三 23时13分13秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 55
- **通过**: 54
- **失败**: 1
- **忽略**: 0

### ❌ 失败测试详情

#### `date::tests_rug_15::test_rug`
- **位置**: `src/date.rs:703:13`
- **错误信息**:
```text
assertion `left == right` failed
  left: SystemTime { tv_sec: 1518568087, tv_nsec: 0 }
 right: SystemTime { tv_sec: 1517881687, tv_nsec: 0 }


failures:
    date::tests_rug_15::test_rug

test result: FAILED. 54 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.19s

```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **95.22%** | 🟢 优秀 | 737/774 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **86.84%** | 🟡 良好 | 99/114 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **93.81%** | 🟢 优秀 | 91/97 | 未被调用的函数数量 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/wrapper.rs` | 79.1% <br><sub style='color:gray'>(34/43)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 70.6% <br><sub style='color:gray'>(12/17)</sub> |
| `src/duration.rs` | 95.3% <br><sub style='color:gray'>(284/298)</sub> | 86.7% <br><sub style='color:gray'>(26/30)</sub> | 100.0% <br><sub style='color:gray'>(29/29)</sub> |
| `src/date.rs` | 96.8% <br><sub style='color:gray'>(419/433)</sub> | 86.9% <br><sub style='color:gray'>(73/84)</sub> | 98.0% <br><sub style='color:gray'>(50/51)</sub> |
