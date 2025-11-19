# RUG 深度覆盖率报告: `uuid_gemini-2.5-flash-nothinking_20251110_000940`

> **检测时间**: 2025年11月19日 星期三 23时13分23秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🟢 ok

- **总测试数**: 98
- **通过**: 98
- **失败**: 0
- **忽略**: 0

## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **81.12%** | 🟡 良好 | 1891/2331 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **91.41%** | 🟢 优秀 | 117/128 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **76.19%** | 🟡 良好 | 288/378 | 未被调用的函数数量 |

## 2. 🚨 重点关注文件 (Top Risky Files)
以下文件代码量较大但**分支覆盖率较低**，建议优先补充测试用例：

| 文件路径 | 分支覆盖率 | 缺失分支数 | 代码行数 |
| :--- | :---: | :---: | :---: |
| `src/builder.rs` | **25.00%** | 3 | 187 |
| `src/parser.rs` | **75.00%** | 4 | 200 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `macros/src/error.rs` | 0.0% <br><sub style='color:gray'>(0/61)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 0.0% <br><sub style='color:gray'>(0/2)</sub> |
| `macros/src/lib.rs` | 0.0% <br><sub style='color:gray'>(0/45)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 0.0% <br><sub style='color:gray'>(0/7)</sub> |
| `macros/src/parser.rs` | 0.0% <br><sub style='color:gray'>(0/52)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 0.0% <br><sub style='color:gray'>(0/3)</sub> |
| `src/md5.rs` | 100.0% <br><sub style='color:gray'>(8/8)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(1/1)</sub> |
| `src/non_nil.rs` | 93.8% <br><sub style='color:gray'>(45/48)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 91.7% <br><sub style='color:gray'>(11/12)</sub> |
| `src/rng.rs` | 80.0% <br><sub style='color:gray'>(24/30)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 66.7% <br><sub style='color:gray'>(6/9)</sub> |
| `src/sha1.rs` | 100.0% <br><sub style='color:gray'>(8/8)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(1/1)</sub> |
| `src/v1.rs` | 100.0% <br><sub style='color:gray'>(33/33)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(4/4)</sub> |
| `src/v3.rs` | 100.0% <br><sub style='color:gray'>(14/14)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(3/3)</sub> |
| `src/v4.rs` | 100.0% <br><sub style='color:gray'>(14/14)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(3/3)</sub> |
| `src/v5.rs` | 100.0% <br><sub style='color:gray'>(20/20)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(4/4)</sub> |
| `src/v6.rs` | 100.0% <br><sub style='color:gray'>(33/33)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(4/4)</sub> |
| `src/v8.rs` | 100.0% <br><sub style='color:gray'>(14/14)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 100.0% <br><sub style='color:gray'>(2/2)</sub> |
| `src/builder.rs` | 65.2% <br><sub style='color:gray'>(122/187)</sub> | 🔴 25.0% <br><sub style='color:gray'>(1/4)</sub> | 55.6% <br><sub style='color:gray'>(20/36)</sub> |
| `src/parser.rs` | 93.0% <br><sub style='color:gray'>(186/200)</sub> | 🟠 75.0% <br><sub style='color:gray'>(12/16)</sub> | 85.7% <br><sub style='color:gray'>(18/21)</sub> |
| `src/error.rs` | 68.1% <br><sub style='color:gray'>(49/72)</sub> | 93.8% <br><sub style='color:gray'>(15/16)</sub> | 50.0% <br><sub style='color:gray'>(1/2)</sub> |
| `src/lib.rs` | 97.7% <br><sub style='color:gray'>(510/522)</sub> | 95.5% <br><sub style='color:gray'>(63/66)</sub> | 96.5% <br><sub style='color:gray'>(83/86)</sub> |
| `src/fmt.rs` | 74.8% <br><sub style='color:gray'>(228/305)</sub> | 100.0% <br><sub style='color:gray'>(12/12)</sub> | 67.5% <br><sub style='color:gray'>(56/83)</sub> |
| `src/timestamp.rs` | 86.0% <br><sub style='color:gray'>(505/587)</sub> | 100.0% <br><sub style='color:gray'>(12/12)</sub> | 72.1% <br><sub style='color:gray'>(62/86)</sub> |
| `src/v7.rs` | 100.0% <br><sub style='color:gray'>(78/78)</sub> | 100.0% <br><sub style='color:gray'>(2/2)</sub> | 100.0% <br><sub style='color:gray'>(9/9)</sub> |
