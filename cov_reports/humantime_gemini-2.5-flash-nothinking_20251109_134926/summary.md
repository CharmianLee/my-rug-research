# RUG 深度覆盖率报告: `humantime_gemini-2.5-flash-nothinking_20251109_134926`

> **检测时间**: 2025年11月19日 星期三 23时13分14秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 87
- **通过**: 81
- **失败**: 6
- **忽略**: 0

### ❌ 失败测试详情

#### `duration::tests_rug_1::test_parse_duration_combined`
- **位置**: `src/duration.rs:551:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: Ok(38995999.00800901s)
 right: Ok(38995423.00800901s)
```
#### `duration::tests_rug_1::test_parse_duration_different_cases`
- **位置**: `src/duration.rs:599:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: Err(UnknownUnit { start: 1, end: 5, unit: "Hour", value: 1 })
 right: Ok(3723s)
```
#### `duration::tests_rug_1::test_parse_duration_months`
- **位置**: `src/duration.rs:517:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: Ok(2630016s)
 right: Ok(2629728s)
```
#### `wrapper::tests_rug_29::test_rug`
- **位置**: `src/wrapper.rs:228:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: SystemTime { tv_sec: 1698400800, tv_nsec: 0 }
 right: SystemTime { tv_sec: 1698391200, tv_nsec: 0 }
```
#### `wrapper::tests_rug_30::test_rug`
- **位置**: `src/wrapper.rs:244:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: SystemTime { tv_sec: 1698400800, tv_nsec: 0 }
 right: SystemTime { tv_sec: 1698391200, tv_nsec: 0 }
```
#### `wrapper::tests_rug_32::test_rug`
- **位置**: `src/wrapper.rs:268:76`
- **错误信息**:
```text
called `Result::unwrap()` on an `Err` value: InvalidFormat


failures:
    duration::tests_rug_1::test_parse_duration_combined
    duration::tests_rug_1::test_parse_duration_different_cases
    duration::tests_rug_1::test_parse_duration_months
    wrapper::tests_rug_29::test_rug
    wrapper::tests_rug_30::test_rug
    wrapper::tests_rug_32::test_rug
```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **96.79%** | 🟢 优秀 | 935/966 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **93.64%** | 🟢 优秀 | 103/110 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **97.64%** | 🟢 优秀 | 124/127 | 未被调用的函数数量 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/wrapper.rs` | 89.3% <br><sub style='color:gray'>(75/84)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 90.9% <br><sub style='color:gray'>(20/22)</sub> |
| `src/duration.rs` | 96.3% <br><sub style='color:gray'>(363/377)</sub> | 92.9% <br><sub style='color:gray'>(26/28)</sub> | 100.0% <br><sub style='color:gray'>(49/49)</sub> |
| `src/date.rs` | 98.4% <br><sub style='color:gray'>(497/505)</sub> | 93.9% <br><sub style='color:gray'>(77/82)</sub> | 98.2% <br><sub style='color:gray'>(55/56)</sub> |
