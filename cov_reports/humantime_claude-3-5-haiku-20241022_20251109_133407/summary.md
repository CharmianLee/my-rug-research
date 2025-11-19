# RUG 深度覆盖率报告: `humantime_claude-3-5-haiku-20241022_20251109_133407`

> **检测时间**: 2025年11月19日 星期三 23时13分20秒 CST | **架构**: Apple Silicon M4

## 0. 测试执行结果 (Test Execution)

**状态**: 🟢 ok

- **总测试数**: 50
- **通过**: 50
- **失败**: 0
- **忽略**: 0

## 1. 核心指标概览 (Dashboard)

| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **Lines (行)** | **94.18%** | 🟢 优秀 | 663/704 | 基础可执行代码覆盖情况 |
| **Branches (分支)** | **86.36%** | 🟡 良好 | 95/110 | **逻辑完备性核心指标** (if/match/loop) |
| **Functions (函数)** | **88.89%** | 🟡 良好 | 80/90 | 未被调用的函数数量 |

## 3. 所有文件详细数据

| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |
| :--- | :---: | :---: | :---: |
| `src/wrapper.rs` | 57.1% <br><sub style='color:gray'>(16/28)</sub> | 0.0% <br><sub style='color:gray'>(0/0)</sub> | 42.9% <br><sub style='color:gray'>(6/14)</sub> |
| `src/duration.rs` | 94.8% <br><sub style='color:gray'>(253/267)</sub> | 85.7% <br><sub style='color:gray'>(24/28)</sub> | 100.0% <br><sub style='color:gray'>(27/27)</sub> |
| `src/date.rs` | 96.3% <br><sub style='color:gray'>(394/409)</sub> | 86.6% <br><sub style='color:gray'>(71/82)</sub> | 95.9% <br><sub style='color:gray'>(47/49)</sub> |
