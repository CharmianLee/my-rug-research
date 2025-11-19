#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import argparse
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# ================= 配置 =================
# 指定使用 nightly 工具链运行覆盖率，以支持 Branch Coverage
TOOLCHAIN = "+nightly" 
# 忽略 RUG 可能引入的非核心文件或依赖
IGNORE_REGEX = r"build\.rs|target/|vendor/|tests/"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("RugCov")

class RugCoverageRunner:
    def __init__(self, crate_path: Path, output_root: Path):
        self.crate_path = crate_path.resolve()
        self.crate_name = self.crate_path.name
        # 报告输出目录：output_root/crate_name/
        self.report_dir = output_root.resolve() / self.crate_name
        self.json_path = self.report_dir / "coverage.json"
        self.summary_path = self.report_dir / "summary.md"
        self.test_stdout = ""
        self.test_stderr = ""

    def check_cargo_toml(self) -> bool:
        return (self.crate_path / "Cargo.toml").exists()

    def clean_previous_run(self):
        """清理旧的覆盖率数据，防止数据污染"""
        logger.info(f"[{self.crate_name}] 清理旧数据...")
        subprocess.run(
            ["cargo", "llvm-cov", "clean", "--workspace"],
            cwd=self.crate_path,
            capture_output=True,
            check=False
        )

    def run_coverage(self) -> bool:
        """执行覆盖率测试 (仅生成 Profile 和 JSON，不生成 HTML)"""
        logger.info(f"[{self.crate_name}] 开始运行覆盖率测试 (Branch Coverage Enabled)...")
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # 1. 运行测试，生成 .profraw 数据
        # 移除了 --html 和 --output-dir，仅运行测试并记录覆盖率
        cmd_test = [
            "cargo", TOOLCHAIN, "llvm-cov", "test",
            "--branch",
            "--workspace",
            "--ignore-filename-regex", IGNORE_REGEX,
            "--ignore-run-fail"
        ]

        # 2. 生成 JSON 报告 (基于上一步生成的 profile)
        cmd_report = [
            "cargo", TOOLCHAIN, "llvm-cov", "report",
            "--json",
            "--output-path", str(self.json_path),
            "--ignore-filename-regex", IGNORE_REGEX
        ]

        try:
            env = os.environ.copy()
            # 显式开启 instrument-coverage，确保 M4/Nightly 兼容性
            env["RUSTFLAGS"] = "-C instrument-coverage" 
            
            # Step 1: Run Tests
            logger.info(f"[{self.crate_name}] Running tests (collecting profiles)...")
            result_test = subprocess.run(
                cmd_test,
                cwd=self.crate_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 保存输出供后续分析
            self.test_stdout = result_test.stdout
            self.test_stderr = result_test.stderr

            if result_test.returncode != 0:
                # 即使失败，只要不是严重错误导致无法生成 profile，我们都继续
                # 但如果 stderr 包含 "compilation failed" 或者类似的严重错误，可能就没有 profile
                logger.warning(f"[{self.crate_name}] 测试运行包含失败 (Exit Code: {result_test.returncode})")
                # 仅打印最后几行供调试，详细信息会在报告中展示
                stderr_tail = '\n'.join(result_test.stderr.splitlines()[-5:])
                logger.warning(f"Stderr tail:\n{stderr_tail}")
                # return False # 不直接返回 False，尝试生成报告

            # Step 2: Generate JSON Report
            logger.info(f"[{self.crate_name}] Exporting coverage data to JSON...")
            result_report = subprocess.run(
                cmd_report,
                cwd=self.crate_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result_report.returncode != 0:
                logger.error(f"[{self.crate_name}] JSON 报告导出失败")
                stderr_tail = '\n'.join(result_report.stderr.splitlines()[-10:])
                logger.error(f"Stderr tail:\n{stderr_tail}")
                return False
            
            logger.info(f"[{self.crate_name}] JSON 数据已生成。")
            return True

        except Exception as e:
            logger.error(f"运行异常: {e}")
            return False

    def _safe_div(self, n: int, d: int) -> float:
        return (n / d * 100.0) if d > 0 else 0.0

    def parse_metrics(self) -> Dict[str, Any]:
        """解析 JSON 提取更丰富的关键指标"""
        if not self.json_path.exists():
            return {}

        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            
            if not data.get("data"):
                return {}
            
            # llvm-cov export json 通常在 data[0]
            export_data = data["data"][0]
            files_data = export_data.get("files", [])
            
            # 总体统计累加器
            totals = {
                "lines": {"total": 0, "covered": 0},
                "branches": {"total": 0, "covered": 0},
                "functions": {"total": 0, "covered": 0},
                "regions": {"total": 0, "covered": 0}
            }
            
            file_details = []

            for file_obj in files_data:
                fname = file_obj.get("filename", "unknown")
                # 过滤逻辑
                if "src/" not in fname and "lib.rs" not in fname:
                    continue

                summary = file_obj.get("summary", {})
                
                # 提取各维度数据
                l_stats = summary.get("lines", {})
                b_stats = summary.get("branches", {})
                f_stats = summary.get("functions", {})
                r_stats = summary.get("regions", {})

                # 单文件统计
                l_count, l_cov = l_stats.get("count", 0), l_stats.get("covered", 0)
                b_count, b_cov = b_stats.get("count", 0), b_stats.get("covered", 0)
                f_count, f_cov = f_stats.get("count", 0), f_stats.get("covered", 0)
                r_count, r_cov = r_stats.get("count", 0), r_stats.get("covered", 0)

                # 累加到总体
                totals["lines"]["total"] += l_count
                totals["lines"]["covered"] += l_cov
                totals["branches"]["total"] += b_count
                totals["branches"]["covered"] += b_cov
                totals["functions"]["total"] += f_count
                totals["functions"]["covered"] += f_cov
                totals["regions"]["total"] += r_count
                totals["regions"]["covered"] += r_cov

                # 计算单文件百分比
                l_pct = self._safe_div(l_cov, l_count)
                b_pct = self._safe_div(b_cov, b_count)
                f_pct = self._safe_div(f_cov, f_count)

                # 计算一个简单的“关注度分数”：分支覆盖率越低且行数越多，分数越高（越需要关注）
                # 仅当分支总数 > 0 时计算风险，防止空文件干扰
                risk_score = (100 - b_pct) * (l_count / 100.0) if b_count > 0 else 0

                file_details.append({
                    "file": fname,
                    "metrics": {
                        "line": {"pct": l_pct, "cov": l_cov, "total": l_count},
                        "branch": {"pct": b_pct, "cov": b_cov, "total": b_count},
                        "function": {"pct": f_pct, "cov": f_cov, "total": f_count}
                    },
                    "risk_score": risk_score
                })

            # 计算总体百分比
            overall = {}
            for key in totals:
                overall[key] = {
                    "pct": self._safe_div(totals[key]["covered"], totals[key]["total"]),
                    "stats": f"{totals[key]['covered']}/{totals[key]['total']}"
                }

            return {
                "overall": overall,
                "details": file_details
            }

        except Exception as e:
            logger.error(f"JSON 解析失败: {e}")
            return {}

    def _get_status_icon(self, pct: float) -> str:
        """根据覆盖率返回状态图标"""
        if pct >= 90: return "🟢 优秀"
        if pct >= 75: return "🟡 良好"
        if pct >= 50: return "🟠 警告"
        return "🔴 危险"

    def generate_markdown(self, metrics: Dict[str, Any]):
        """生成详细的 Markdown 报告"""
        if not metrics:
            return

        ov = metrics["overall"]
        details = metrics["details"]
        test_results = self.analyze_test_results()

        with open(self.summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# RUG 深度覆盖率报告: `{self.crate_name}`\n\n")
            f.write(f"> **检测时间**: {os.popen('date').read().strip()} | **架构**: Apple Silicon M4\n\n")
            
            # 0. 测试执行结果 (Test Execution)
            f.write("## 0. 测试执行结果 (Test Execution)\n\n")
            status_icon = "🟢" if test_results["failed"] == 0 and test_results["total"] > 0 else "🔴"
            if test_results["total"] == 0: status_icon = "⚪"
            
            f.write(f"**状态**: {status_icon} {test_results.get('status', 'Unknown')}\n\n")
            f.write(f"- **总测试数**: {test_results['total']}\n")
            f.write(f"- **通过**: {test_results['passed']}\n")
            f.write(f"- **失败**: {test_results['failed']}\n")
            f.write(f"- **忽略**: {test_results['ignored']}\n\n")
            
            if test_results["failures_list"]:
                f.write("### ❌ 失败测试详情\n\n")
                for fail in test_results["failures_list"]:
                    f.write(f"#### `{fail['name']}`\n")
                    f.write(f"- **位置**: `{fail['location']}`\n")
                    f.write(f"- **错误信息**:\n")
                    f.write(f"```text\n{fail['message']}\n```\n")
            
            # 1. 核心仪表盘
            f.write("## 1. 核心指标概览 (Dashboard)\n\n")
            f.write("| 维度 | 覆盖率 (%) | 状态 | 命中/总数 | 说明 |\n")
            f.write("| :--- | :---: | :---: | :---: | :--- |\n")
            
            # 行覆盖
            l_pct = ov['lines']['pct']
            f.write(f"| **Lines (行)** | **{l_pct:.2f}%** | {self._get_status_icon(l_pct)} | {ov['lines']['stats']} | 基础可执行代码覆盖情况 |\n")
            
            # 分支覆盖 (最重要)
            b_pct = ov['branches']['pct']
            f.write(f"| **Branches (分支)** | **{b_pct:.2f}%** | {self._get_status_icon(b_pct)} | {ov['branches']['stats']} | **逻辑完备性核心指标** (if/match/loop) |\n")
            
            # 函数覆盖
            f_pct = ov['functions']['pct']
            f.write(f"| **Functions (函数)** | **{f_pct:.2f}%** | {self._get_status_icon(f_pct)} | {ov['functions']['stats']} | 未被调用的函数数量 |\n\n")

            # 2. 重点关注文件 (Top 5 Risky)
            # 排序规则：风险分倒序（优先显示分支覆盖低且代码量大的）
            sorted_by_risk = sorted(details, key=lambda x: x['risk_score'], reverse=True)
            top_risky = [x for x in sorted_by_risk if x['metrics']['branch']['pct'] < 80 and x['metrics']['branch']['total'] > 0][:5]

            if top_risky:
                f.write("## 2. 🚨 重点关注文件 (Top Risky Files)\n")
                f.write("以下文件代码量较大但**分支覆盖率较低**，建议优先补充测试用例：\n\n")
                f.write("| 文件路径 | 分支覆盖率 | 缺失分支数 | 代码行数 |\n")
                f.write("| :--- | :---: | :---: | :---: |\n")
                for item in top_risky:
                    display_name = item['file'].split(self.crate_name)[-1].lstrip(os.sep)
                    b_metric = item['metrics']['branch']
                    l_metric = item['metrics']['line']
                    missed_branches = b_metric['total'] - b_metric['cov']
                    f.write(f"| `{display_name}` | **{b_metric['pct']:.2f}%** | {missed_branches} | {l_metric['total']} |\n")
                f.write("\n")
            
            # 3. 详细文件列表
            f.write("## 3. 所有文件详细数据\n\n")
            f.write("| 文件名 | 行覆盖率 (Line) | 分支覆盖率 (Branch) | 函数覆盖率 (Func) |\n")
            f.write("| :--- | :---: | :---: | :---: |\n")
            
            # 按分支覆盖率升序排序显示所有文件
            sorted_files = sorted(details, key=lambda x: x['metrics']['branch']['pct'])
            
            for item in sorted_files:
                display_name = item['file'].split(self.crate_name)[-1].lstrip(os.sep)
                
                l_m = item['metrics']['line']
                b_m = item['metrics']['branch']
                f_m = item['metrics']['function']
                
                # 使用简单的颜色标记
                b_str = f"{b_m['pct']:.1f}%"
                if b_m['pct'] < 50 and b_m['total'] > 0:
                    b_str = f"🔴 {b_str}"
                elif b_m['pct'] < 80 and b_m['total'] > 0:
                    b_str = f"🟠 {b_str}"
                
                line_info = f"{l_m['pct']:.1f}% <br><sub style='color:gray'>({l_m['cov']}/{l_m['total']})</sub>"
                branch_info = f"{b_str} <br><sub style='color:gray'>({b_m['cov']}/{b_m['total']})</sub>"
                func_info = f"{f_m['pct']:.1f}% <br><sub style='color:gray'>({f_m['cov']}/{f_m['total']})</sub>"

                f.write(f"| `{display_name}` | {line_info} | {branch_info} | {func_info} |\n")

        logger.info(f"Markdown 报告已生成: {self.summary_path}")

    def analyze_test_results(self) -> Dict[str, Any]:
        """解析测试输出，提取失败信息和统计"""
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "ignored": 0,
            "failures_list": [],
            "summary_line": "未找到测试总结行",
            "status": "Unknown"
        }
        
        # 合并 stdout 和 stderr 进行分析，因为 cargo test 的输出可能混杂
        full_log = self.test_stdout + "\n" + self.test_stderr
        
        # 1. 提取 Summary Line
        # test result: FAILED. 62 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.20s
        summary_match = re.search(r"test result: (.*?)\. (\d+) passed; (\d+) failed; (\d+) ignored;", full_log)
        if summary_match:
            results["status"] = summary_match.group(1)
            results["passed"] = int(summary_match.group(2))
            results["failed"] = int(summary_match.group(3))
            results["ignored"] = int(summary_match.group(4))
            results["total"] = results["passed"] + results["failed"] + results["ignored"]
            results["summary_line"] = summary_match.group(0)
        
        # 2. 提取详细失败信息
        # 模式：
        # ---- test_name stdout ----
        # thread 'test_name' panicked at file:line:col:
        # message
        # ...
        
        # 简单的切分方法：按 "---- " 切分
        parts = full_log.split("---- ")
        for part in parts[1:]: # 跳过第一个（通常是前面的日志）
            # part 格式类似: "duration::tests_rug_1::test_complex_combination stdout ----\n\nthread ... panicked at ..."
            lines = part.splitlines()
            if not lines: continue
            
            test_name_line = lines[0]
            if " stdout ----" not in test_name_line: continue
            
            test_name = test_name_line.replace(" stdout ----", "").strip()
            
            # 寻找 panic 信息
            panic_info = "No panic message found"
            location = "Unknown location"
            
            content = "\n".join(lines[1:])
            
            # 匹配 panic 行
            # 格式1: thread '...' panicked at src/lib.rs:10:5:
            # 格式2: thread '...' (1234) panicked at src/lib.rs:10:5:
            panic_match = re.search(r"thread '.*?'(?: \(.*?\))? panicked at (.*?:\d+:\d+):\n(.*)", content, re.DOTALL)
            if panic_match:
                location = panic_match.group(1)
                raw_msg = panic_match.group(2).strip()
                panic_info = "\n".join(raw_msg.splitlines()[:10])
            else:
                # 尝试匹配另一种格式: panicked at 'message', file:line:col
                panic_match_2 = re.search(r"thread '.*?'(?: \(.*?\))? panicked at '(.*?)', (.*?:\d+:\d+)", content)
                if panic_match_2:
                    panic_info = panic_match_2.group(1)
                    location = panic_match_2.group(2)
                else:
                    # 尝试更宽泛的匹配
                    panic_match_3 = re.search(r"panicked at (.*?:\d+:\d+):\n(.*)", content, re.DOTALL)
                    if panic_match_3:
                        location = panic_match_3.group(1)
                        raw_msg = panic_match_3.group(2).strip()
                        panic_info = "\n".join(raw_msg.splitlines()[:10])

            results["failures_list"].append({
                "name": test_name,
                "location": location,
                "message": panic_info
            })
            
        return results

def main():
    parser = argparse.ArgumentParser(description="RUG 产物覆盖率分析工具 (M4/Nightly) - Enhanced")
    parser.add_argument("input_path", type=Path, help="RUG 输出的单个 Crate 路径，或者包含多个 Crate 的父目录")
    parser.add_argument("--output", type=Path, default=Path("coverage_reports"), help="报告输出目录")
    parser.add_argument("--batch", action="store_true", help="批量模式：输入路径是包含多个 crate 的目录")

    args = parser.parse_args()

    targets = []
    if args.batch:
        if not args.input_path.exists():
            logger.error("输入路径不存在")
            sys.exit(1)
        for item in args.input_path.iterdir():
            if item.is_dir() and (item / "Cargo.toml").exists():
                targets.append(item)
    else:
        targets.append(args.input_path)

    logger.info(f"检测到 {len(targets)} 个待分析目标")

    for target in targets:
        runner = RugCoverageRunner(target, args.output)
        if not runner.check_cargo_toml():
            logger.warning(f"跳过 {target}: 未找到 Cargo.toml")
            continue
        
        runner.clean_previous_run()
        success = runner.run_coverage()
        
        if success:
            metrics = runner.parse_metrics()
            runner.generate_markdown(metrics)
        else:
            logger.error(f"{target.name} 分析失败，请检查代码是否可编译。")

if __name__ == "__main__":
    main()