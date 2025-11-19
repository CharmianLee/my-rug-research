# RUG 深度覆盖率报告: `humantime_gemini-2.5-flash-thinking_20251109_141506`

> **检测时间**: 2025年11月19日 星期三 23时13分21秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 82
- **通过**: 70
- **失败**: 12
- **忽略**: 0

### ❌ 失败测试详情

#### `date::tests_rug_15::test_parse_rfc3339_weak`
- **位置**: `src/date.rs:741:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: SystemTime { tv_sec: 1518568087, tv_nsec: 0 }
 right: SystemTime { tv_sec: 1518577687, tv_nsec: 0 }
```
#### `date::tests_rug_18::test_rug`
- **位置**: `src/date.rs:896:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: "2018-02-27T23:34:47Z"
 right: "2018-02-14T00:28:07Z"
```
#### `date::tests_rug_17::test_rug`
- **位置**: `src/date.rs:865:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: "1970-01-01T00:00:00.123000000Z"
 right: "1970-01-01T00:00:00.123Z"
```
#### `date::tests_rug_21::test_rug`
- **位置**: `src/date.rs:1002:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: "2023-03-15T13:20:00.500000000Z"
 right: "2023-03-15T00:00:00.500000000Z"
```
#### `duration::tests_rug_1::test_parse_duration`
- **位置**: `src/duration.rs:488:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: Ok(788645.006007008s)
 right: Ok(788045.006007008s)
```
#### `duration::tests_rug_3::test_item_plural_value_multiple_already_started`
- **位置**: `src/duration.rs:638:54`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed
```
#### `duration::tests_rug_3::test_item_plural_value_multiple_not_started`
- **位置**: `src/duration.rs:625:54`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed
```
#### `duration::tests_rug_3::test_item_plural_value_one_already_started`
- **位置**: `src/duration.rs:612:54`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed
```
#### `duration::tests_rug_3::test_item_plural_value_one_not_started`
- **位置**: `src/duration.rs:599:54`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed
```
#### `duration::tests_rug_3::test_item_plural_value_zero_not_started`
- **位置**: `src/duration.rs:586:54`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed
```
#### `duration::tests_rug_3::test_rug`
- **位置**: `src/duration.rs:562:54`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed
```
#### `duration::tests_rug_4::test_rug`
- **位置**: `src/duration.rs:655:42`
- **错误信息**:
```text
not implemented: std::fmt::Formatter cannot be directly constructed for testing this way without panicking.


failures:
    date::tests_rug_15::test_parse_rfc3339_weak
    date::tests_rug_17::test_rug
    date::tests_rug_18::test_rug
    date::tests_rug_21::test_rug
    duration::tests_rug_1::test_parse_duration
    duration::tests_rug_3::test_item_plural_value_multiple_already_started
```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **87.37%** | 🟡 良好 | 927/1061 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **88.18%** | 🟡 良好 | 97/110 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **97.54%** | 🟢 优秀 | 119/122 | 未被调用的函数数量 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/wrapper.rs` | 94.7% <br><sub style='color:gray'>(107/113)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 90.0% <br><sub style='color:gray'>(18/20)</sub> |
| `src/duration.rs` | 88.4% <br><sub style='color:gray'>(320/362)</sub> | 85.7% <br><sub style='color:gray'>(24/28)</sub> | 100.0% <br><sub style='color:gray'>(40/40)</sub> |
| `src/date.rs` | 85.3% <br><sub style='color:gray'>(500/586)</sub> | 89.0% <br><sub style='color:gray'>(73/82)</sub> | 98.4% <br><sub style='color:gray'>(61/62)</sub> |
