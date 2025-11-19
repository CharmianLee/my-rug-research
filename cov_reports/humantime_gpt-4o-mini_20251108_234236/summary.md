# RUG 深度覆盖率报告: `humantime_gpt-4o-mini_20251108_234236`

> **检测时间**: 2025年11月19日 星期三 23时13分16秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🔴 FAILED

- **总测试数**: 47
- **通过**: 45
- **失败**: 2
- **忽略**: 0

### ❌ 失败测试详情

#### `date::tests_rug_12::test_two_digits`
- **位置**: `src/date.rs:636:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: Err(InvalidDigit)
 right: Ok(37)
```
#### `date::tests_rug_15::test_rug`
- **位置**: `src/date.rs:673:9`
- **错误信息**:
```text
assertion `left == right` failed
  left: SystemTime { tv_sec: 1518568087, tv_nsec: 0 }
 right: SystemTime { tv_sec: 1518564487, tv_nsec: 0 }


failures:
    date::tests_rug_12::test_two_digits
    date::tests_rug_15::test_rug

test result: FAILED. 45 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.19s
```
## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **94.21%** | 🟢 优秀 | 667/708 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **88.18%** | 🟡 良好 | 97/110 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **88.51%** | 🟡 良好 | 77/87 | 未被调用的函数数量 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/wrapper.rs` | 55.2% <br><sub style='color:gray'>(16/29)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 35.7% <br><sub style='color:gray'>(5/14)</sub> |
| `src/date.rs` | 96.6% <br><sub style='color:gray'>(400/414)</sub> | 87.8% <br><sub style='color:gray'>(72/82)</sub> | 97.9% <br><sub style='color:gray'>(47/48)</sub> |
| `src/duration.rs` | 94.7% <br><sub style='color:gray'>(251/265)</sub> | 89.3% <br><sub style='color:gray'>(25/28)</sub> | 100.0% <br><sub style='color:gray'>(25/25)</sub> |
