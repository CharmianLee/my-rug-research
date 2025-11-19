# 修改设计
好的，这是一个非常棒的改进思路！将 RUG 从一个“黑盒”工具转变为一个可供分析和迭代的“白盒”研究框架。

下面，我将深入分析 `main.py` 的结构，并为您详细列出实现这三个目标需要修改的关键位置和具体逻辑，而不直接编写代码。

---

### 需求 1：建立非破坏性的、隔离的工作流

**目标**：不修改原始项目，所有操作（代码注入、编译）都在一个临时的副本中进行。

**核心思路**：在处理每个 crate 的主函数 `run_single_fd` 的最开始，就创建一个工作副本。后续所有路径相关的操作都指向这个副本。

**需要修改的地方**:

1.  **函数: `run_single_fd(fd: str)`**
    *   **位置**: 函数的入口处，在执行任何 `subprocess.run` 之前。
    *   **修改逻辑**:
        1.  引入 `shutil` 和 `tempfile` 库。
        2.  创建一个唯一的临时目录作为工作区，例如 `work_dir = tempfile.mkdtemp(prefix=f"rug_work_{os.path.basename(fd)}_")`。
        3.  使用 `shutil.copytree(fd, work_dir, dirs_exist_ok=True)` 将原始项目 `fd` 的所有内容完整地复制到 `work_dir` 中。
        4.  **关键**: 将函数内所有对原始路径 `fd` 的使用，全部替换为新的工作路径 `work_dir`。这尤其重要，因为它会影响：
            *   所有 `subprocess.run(..., cwd=fd, ...)` 的 `cwd` 参数。
            *   所有 `open(fd + '/' + file, ...)` 的文件路径拼接。
            *   `load_analysis(fd+'/'+crate+'.json')` 和 `parse_log(fd + "/{}.out.txt".format(crate))` 的路径。
        5.  在函数的末尾，或者使用 `try...finally` 结构，添加 `shutil.rmtree(work_dir)` 来确保在运行结束后（无论成功与否）都清理掉这个临时副本。

**示例（伪代码）**:
```python
def run_single_fd(fd: str):
    work_dir = None
    try:
        # 1. 创建副本
        work_dir = f"/tmp/rug_work_{os.path.basename(fd)}"
        shutil.copytree(fd, work_dir)

        # 2. 所有后续操作都使用 work_dir
        fin = subprocess.run('cargo ws list -l', shell=True, cwd=work_dir, ...)
        # ...
        data = load_analysis(work_dir + '/' + crate + '.json')
        # ...
        # 在 compile_verify 和 compile_only 中
        with open(work_dir + '/' + file, 'r+') as fp:
            # ...
            subprocess.run(..., cwd=work_dir, ...)

    finally:
        # 3. 清理副本
        if work_dir and os.path.exists(work_dir):
            shutil.rmtree(work_dir)
```

---

### 需求 2：捕获并保存详细信息

**目标**：为每一次测试生成尝试（无论成败），都记录下 Prompt、LLM 回复、编译器错误等信息。

**核心思路**：修改负责编译验证的函数，使其不仅返回布尔值，还返回详细的错误输出。然后在调用这些函数的地方捕获并结构化地存储这些信息。

**需要修改的地方**:

1.  **函数: `compile_verify(...)` 和 `compile_only(...)`**
    *   **位置**: 函数的返回值部分。
    *   **修改逻辑**:
        *   当前函数返回 `True` 或 `False`。
        *   修改其返回值为一个元组 `(bool, str)`，例如 `(is_success, output_log)`。
        *   如果编译成功 (`ret.returncode == 0`)，返回 `(True, ret.stdout.decode('utf-8'))`。
        *   如果编译失败，返回 `(False, ret.stderr.decode('utf-8'))`。**这是捕获编译器错误的关键**。

2.  **函数: `prompt_built_in`, `prompt_with_context`, `prompt_with_src_only` (参数实例化阶段)**
    *   **位置**: `while` 循环内部，调用 `compile_verify` 的地方。
    *   **修改逻辑**:
        1.  在发起 `gpt_request` 之前，将 `messages` (即 Prompt) 保存到一个日志变量中。
        2.  保存 `gpt_request` 返回的 `code` (即 LLM 的原始回复)。
        3.  接收 `compile_verify` 返回的元组 `(finished, log_output) = compile_verify(...)`。
        4.  将 Prompt、回复、成功状态 (`finished`) 和 `log_output` (无论是 stdout 还是 stderr) 一起记录到一个结构化的日志对象中（例如一个字典）。

3.  **函数: `run_single_fd(...)` (最终测试生成阶段)**
    *   **位置**: `for fc in reversed(func_call):` 循环内部，调用 `compile_only` 的地方。
    *   **修改逻辑**:
        1.  在发起 `gpt_request` 之前，保存最终构建的 `output` 变量 (即最终的 Prompt)。
        2.  保存 `gpt_request` 返回的 `code`。
        3.  接收 `compile_only` 返回的元组 `(finished, log_output) = compile_only(...)`。
        4.  将 Prompt、回复、成功状态和日志输出记录到一个大的、按函数组织的日志对象中。

4.  **数据存储**:
    *   在 `run_single_fd` 的开头，初始化一个大的字典，如 `detailed_log = {}`。
    *   在每次记录时，都添加到这个字典中，结构可以设计为：
      ```json
      {
        "target_function_name": {
          "parameter_instantiation": [
            { "attempt": 1, "target_type": "...", "prompt": "...", "response": "...", "success": false, "compiler_output": "..." }
          ],
          "test_generation": [
            { "attempt": 1, "prompt": "...", "response_raw": "...", "injected_code": "...", "success": true, "compiler_output": "..." }
          ]
        }
      }
      ```
    *   在 `run_single_fd` 的 `finally` 块中，将这个 `detailed_log` 字典序列化为 JSON 文件并保存。

---

### 需求 3：增强统计逻辑并生成 Markdown 报告

**目标**：对流程中的关键步骤进行成功/失败统计，并以 Markdown 表格形式输出。

**核心思路**：在 `run_single_fd` 中维护一个统计计数的字典。在关键的逻辑判断点更新这些计数器，并在最后生成报告。

**需要修改的地方**:

1.  **函数: `run_single_fd(...)`**
    *   **位置**: 函数开头。
    *   **修改逻辑**:
        *   初始化一个统计字典 `stats = { "total_targets": 0, "targets_succeeded": 0, "targets_failed": 0, "param_attempts": 0, "param_success": 0, "param_failures": 0, "test_gen_attempts": 0, "test_gen_success": 0, "test_gen_failures": 0 }`。

2.  **修改各个关键节点以更新统计**:
    *   **总目标**: 在 `for (_, stmts, ...)` 循环开始时，`stats["total_targets"] += 1`。
    *   **参数实例化**: 在 `prompt_built_in` 等函数的 `while` 循环内，每次调用 `compile_verify` 前 `stats["param_attempts"] += 1`。根据返回结果，更新 `stats["param_success"]` 或 `stats["param_failures"]`。
    *   **测试生成**: 在 `run_single_fd` 的最终测试生成 `while` 循环内，每次调用 `compile_only` 前 `stats["test_gen_attempts"] += 1`。根据返回结果，更新 `stats["test_gen_success"]` 或 `stats["test_gen_failures"]`。
    *   **最终目标成败**: 在 `if succeed:` 判断处，更新 `stats["targets_succeeded"]` 或 `stats["targets_failed"]`。

3.  **生成 Markdown 报告**:
    *   **位置**: 在 `run_single_fd` 的末尾（`finally` 块之前）。
    *   **修改逻辑**:
        1.  创建一个新函数，例如 `generate_markdown_report(stats)`。
        2.  该函数接收 `stats` 字典，并使用 f-string 或其他模板方法将其格式化为 Markdown 表格字符串。
            ```python
            report = f"""
            # RUG Run Summary

            | Metric                      | Count |
            | --------------------------- | ----- |
            | Total Functions Targeted    | {stats['total_targets']} |
            | Functions with Tests Generated | {stats['targets_succeeded']} |
            | Functions Failed            | {stats['targets_failed']} |
            | **Parameter Instantiation** |       |
            | Total Attempts              | {stats['param_attempts']} |
            | Successful Instantiations   | {stats['param_success']} |
            | Failed Instantiations       | {stats['param_failures']} |
            | **Test Code Generation**    |       |
            | Total Attempts              | {stats['test_gen_attempts']} |
            | Successful Compilations     | {stats['test_gen_success']} |
            | Failed Compilations         | {stats['test_gen_failures']} |
            """
            ```
        3.  将这个字符串写入一个 `.md` 文件，例如 `rug_summary.md`。

通过以上修改，您将把 `main.py` 从一个执行工具，转变为一个强大的、可追溯、可量化的测试生成研究框架，极大地便利了后续的分析与改进工作。


# 隔离工作流修改总结

## 修改目标
建立非破坏性的、隔离的工作流，确保所有操作（代码注入、编译）都在临时副本中进行，不修改原始项目。

## 主要修改

“持久化的、隔离的输出副本”，每次运行都会在项目根目录 rug_runs 下生成唯一副本，所有代码注入与编译都在该副本中执行，并在结束后保留下来。

关键改动
新建持久化运行目录

在项目根目录创建 rug_runs
运行目录命名：{crate}{model_name}{timestamp}
model_name 来自环境变量 RUG_MODEL_NAME（默认 gpt-3.5-turbo）
timestamp 形如 YYYYMMDD_HHMMSS
将源项目完整复制到该目录后作为工作区
入口逻辑调整

当无参时：遍历当前目录的子目录（原有逻辑），为每个 crate 调用 run_single(fd)，run_single 会创建副本并直接调用 run_single_fd(output_dir)
当有参时：将该参数视为源目录，run_single 会创建副本并调用 run_single_fd(output_dir)
不再通过 shell 重启 main.py，也不再把日志重定向到源目录；所有产出（MD、JSON）在当前工作目录下生成，代码变更发生在副本内
run_single_fd 接口变更

签名由 run_single_fd(fd: str) 改为 run_single_fd(work_dir: str)
内部所有路径处理均基于 work_dir
移除了临时目录创建和清理逻辑，不再删除工作副本
crate 名使用 os.path.basename(work_dir)（即副本目录名）
工件生成

统计 Markdown 报告：rug_summary_{basename(work_dir)}.md（示例：rug_summary_humantime_gpt-3.5-turbo_20251108_153012.md）
详细日志 JSON：detailed_log_{basename(work_dir)}.json
compile_only 成功时不回滚，保留注入到副本中的代码；compile_verify 始终回滚（用于参数实例化校验）
使用方法
单 crate 运行（例如在 example 目录）：

这会在项目根目录 rug_runs 下创建：
rug_runs/humantime_gpt-3.5-turbo_YYYYMMDD_HHMMSS/
并在该副本内执行所有注入与编译流程。
在当前目录生成：

rug_summary_humantime_gpt-3.5-turbo_YYYYMMDD_HHMMSS.md
detailed_log_humantime_gpt-3.5-turbo_YYYYMMDD_HHMMSS.json
多 crate（无参数）：

仍按原有逻辑遍历 example 下的子目录，但每个 crate 将创建独立的 rug_runs 下副本，并在该副本内运行。
已满足的点
不再修改原项目目录；所有更改都发生在 rug_runs 下的副本
不再使用临时目录，也不进行删除；副本作为一次运行的“产物”保留
之前实现的详细日志与统计汇总保持兼容，且按副本名落盘，便于对齐一次运行的产物




# 记录输出修改总结
把“每次尝试的 Prompt、LLM 回复、编译输出”全链路记录下来，并在 finally 中落盘为 JSON。

## 做了什么

- 改造编译函数，返回详细日志
  - compile_only(fd, file, code, crate) 现返回 (success: bool, log: str)
  - compile_verify(fd, file, code, mod, var_name, ty, crate) 现返回 (success: bool, log: str)
  - 捕获 stdout/stderr；compile_verify 始终回滚文件；compile_only 保持原有成功时不回滚的行为（避免引入潜在副作用变更）

- 在参数实例化阶段记录详细信息
  - 在 prompt_built_in / prompt_with_context / prompt_with_src_only 的每次 while 尝试中，记录：
    - prompt（这次请求发给 LLM 的完整用户消息）
    - response_raw（LLM 原始回复）
    - response_processed（去掉围栏后的代码）
    - success（是否通过 compile_verify）
    - compiler_output（stdout 或 stderr）
  - 这些记录被归入 detailed_log[当前目标函数].parameter_instantiation

- 在最终测试生成阶段记录详细信息
  - 在 run_single_fd 的 for fc in reversed(func_call) → while 尝试中，记录：
    - prompt（最终合成的 output）
    - response_raw（LLM 原始回复）
    - injected_code（处理后注入到文件中的代码）
    - success（是否通过 compile_only）
    - compiler_output（stdout 或 stderr）
  - 这些记录被归入 detailed_log[当前目标函数].test_generation

- 结构化日志与写盘
  - 在 run_single_fd 开头初始化 detailed_log，全程按“目标函数名”分桶
  - finally 中将 detailed_log 序列化到当前工作目录下的文件：detailed_log_{crate}.json
  - 仍保持临时工作副本的隔离与清理逻辑不变

## 关键实现点

- 新增全局日志工具
  - 全局结构与工具函数：
    - detailed_log: dict
    - current_target_function: str
    - _ensure_log_bucket, _log_parameter_attempt, _log_test_attempt
  - 在处理每个目标函数前设置 current_target_function，并确保对应桶存在

- 修改点总览（都在 main.py）
  - 新增全局日志与工具函数（memo 下方）
  - compile_only/compile_verify 返回 (bool, str) 并捕获输出
  - prompt_built_in/prompt_with_context/prompt_with_src_only：
    - 提前取 prompt_text = messages[-1]['content']
    - 记录 response_raw 与 processed_code
    - 使用返回的新元组来判断 success 并写入日志
  - run_single_fd：
    - 初始化 detailed_log、current_target_function
    - 为每个 target_func 设置日志 bucket
    - 记录测试生成阶段的 prompt/response_raw/injected_code/success/compiler_output
    - finally 中写出 detailed_log_{crate}.json 并清理临时工作目录

## 输出文件

- 运行完成后会在当前目录生成：
  - detailed_log_{crate}.json
  - 示例：运行 humantime 时输出 `detailed_log_humantime.json`

JSON 结构示例（按目标函数名分组）：
{
  "crate::module::func": {
    "parameter_instantiation": [
      {
        "attempt": 1,
        "phase": "prompt_with_context",
        "target_type": "std::time::Duration",
        "prompt": "...",
        "response_raw": "...",
        "response_processed": "...",
        "success": false,
        "compiler_output": "..."
      }
    ],
    "test_generation": [
      {
        "attempt": 1,
        "prompt": "...",
        "response_raw": "...",
        "injected_code": "...",
        "success": true,
        "compiler_output": "..."
      }
    ]
  }
}

## 如何运行

- 单个 crate（例如 humantime）
  ```bash
  python3 main.py humantime
  ```
- 成功后在 example 目录看到 `detailed_log_humantime.json`。

注意：如果本地环境没有安装 openai 依赖，脚本会在导入处失败，无法触发 LLM 及编译阶段；请先安装 `openai` 并配置相关环境变量，或者在本地跳过 LLM 流程改为桩实现再验证编译环节。

## 质量门禁

- 语法检查（Python）：PASS
- 构建/运行：未执行完整运行（你的环境上一次运行因缺少 openai 失败）；日志逻辑与返回值修改不影响现有控制流
- 测试：无项目内自动化测试可运行；变更点已自洽、类型/调用方已全部适配

## 后续可选优化

- 将 compile_only 成功时也回滚文件，避免在隔离目录内多次注入叠加（当前保持原行为以降低风险）。
- 将 prompt 文本精简（例如仅保存最后一次 user 消息）以减少日志体积。
- 支持按目标函数或时间戳拆分多个日志文件，便于并行与历史留存。

已进行更改。


# markdown 报告修改总结
产物路径

Markdown 报告写入副本根目录：{work_dir}/rug_summary.md
详细日志 JSON 写入副本根目录：{work_dir}/detailed_log.json
保留运行副本目录，不清理
报告细化

增强 generate_markdown_report，包含：
顶部总览统计表（总目标数、成功/失败、参数阶段尝试/成功/失败、测试生成尝试/成功/失败）
每个 Function 的分节：
参数实例化尝试表：Attempt | Phase | Type | Compile Success | Verify Success | Compiler Output
测试生成尝试表：Attempt | Compile Success | Compiler Output
Compiler Output 会做简单清洗：换行转空格、管道符转 ¦、截断到 160 字符，避免破坏 Markdown 表格
日志字段更完备

参数阶段每次尝试记录：
phase（prompt_built_in/prompt_with_context/prompt_with_src_only）
target_type、prompt、response_raw、response_processed
compile_success、verify_success、success（当前 compile_verify 统一为 success）
compiler_output（stdout 或 stderr）
测试生成阶段每次尝试记录：
prompt、response_raw、injected_code
compile_success、success、compiler_output
统计计数与落盘

stats 仍按之前规则更新，并用于 Markdown 顶部总览
报告生成时调用 generate_markdown_report(stats, detailed_log)
统计和详细日志都落在运行副本目录中



# 多线程并行交互修改总结
我已将 GPT 交互并行化，并对日志与统计做了线程安全改造，同时序列化了文件写入/编译步骤以避免竞态；接下来给你变更摘要与使用方式。

## 本次改动要点

- 新增并行：参数构造阶段的所有 GPT 请求并行执行，加速“类型参数样例生成”的关键路径。
  - 使用线程池，线程数可通过环境变量 RUG_GPT_THREADS 配置（默认 4）。
- 线程安全保障：
  - 日志与统计：所有尝试记录（_log_parameter_attempt/_log_test_attempt）加锁，统计项增量通过 _inc_stat() 加锁处理。
  - 全局计数与缓存：生成变量名用的 counter、memo 缓存的读写加锁，避免并发条件下重复、错乱。
  - 编译安全：compile_only / compile_verify 包裹互斥锁，确保文件追加/回滚与 cargo 调用不会并发写同一文件。
  - 打印输出：并发打印用锁避免日志交错。
- 设计兼容：Markdown 报告与详细日志 schema 不变；新增的尝试记录顺序由日志锁控制（按写入时序），依旧稳定。
- 使用体验：无需更改调用方式；可通过 RUG_GPT_THREADS 控制并发度。

## 关键实现

- 新增锁
  - log_lock, stats_lock, compile_lock, counter_lock, memo_lock, print_lock
- 统计改造
  - 提供 _inc_stat(key, delta=1) 统一加锁更新；参数阶段计数改用该方法。
- GPT 并发（参数阶段）
  - 在 `run_single_fd` 中对每个参数位提交任务到 `ThreadPoolExecutor`。
  - 每个任务内部调用现有的 `prompt_with_bounds` / `prompt_built_in` / `prompt_with_src_only`（内部编译验证仍会顺序通过 compile_lock）。
  - 收集结果后拼接 final_prompt、src_pq、has_sample。
- 文件安全
  - `compile_only` 与 `compile_verify` 代码-写入-编译-回滚全过程套 `compile_lock`，保证串行执行。

## 如何使用

- 可按原方式运行。例如：
  - 已看到你在 example 下运行单 crate：`python3 main.py humantime` 成功
- 想加速 GPT 并发请求，可设定线程数：
  ```zsh
  export RUG_GPT_THREADS=6
  python3 main.py humantime
  ```
- 说明：
  - GPT 请求会并行，编译步骤会串行（保证安全）；总体能显著缩短等待时间。
  - 仍在 `rug_runs/<crate>_<model>_<timestamp>/` 保存 `rug_summary.md` 与 `detailed_log.json`。

## 边界与后续可选优化

- 当前只并行了“参数构造”阶段的 GPT 交互；“单元测试生成”阶段仍保持顺序（减少复杂度与风险）。如果你希望进一步并行化测试生成阶段，也可以类似处理，但要注意：
  - 编译依旧需要串行或使用更细粒度的文件隔离策略（如为每次编译写入临时文件再合并）。
  - 日志与统计已经是线程安全的，可以复用。

## 质量门禁

- 语法检查：PASS（修复了一个缩进问题）
- Lint/Typecheck：未检测到新的问题（本项目为脚本为主）
- 测试：未修改业务逻辑路径及输出格式；并发仅作用于 GPT 阶段，编译依旧串行确保稳定

## 结论

- 已按你的要求添加“GPT 交互的多线程请求功能”，并做好了线程安全的日志与统计设计，以及编译阶段的安全防护。
- 你可以通过 RUG_GPT_THREADS 调节并发度，在 macOS 上 zsh 环境直接运行即可。若需要，我们可以继续并行化测试生成阶段，或引入更细粒度的编译隔离来提升吞吐。

已进行更改。