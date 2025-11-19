import subprocess
import subprocess as sp
import os
import copy
import re
import json
import sys
from openai import OpenAI
import tiktoken
import time
import multiprocessing
import shutil
import tempfile
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 加载 .env 文件
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# 在程序开始时加载环境变量
load_env_file()

init_content = """
You are an expert in Rust and I need your help on development. I will provide you the context and definition or sample 
and will ask you to help me write the code. Please pay attention to the paths and try to utilize the information I provided.
"""

counter = 0
msgs = [
    {"role": "system", "content": init_content},

]

memo = {}

# 线程安全：全局锁
log_lock = threading.Lock()
stats_lock = threading.Lock()
compile_lock = threading.Lock()
counter_lock = threading.Lock()
memo_lock = threading.Lock()
print_lock = threading.Lock()

# 详细日志采集（全局，便于在嵌套函数中记录）
detailed_log = {}
current_target_function = None
stats = None

# 简单的环境变量整型读取工具（非法值回退到默认值）
def _env_int(name: str, default: int) -> int:
    try:
        v = os.getenv(name)
        if v is None or str(v).strip() == "":
            return default
        return int(str(v).strip())
    except Exception:
        return default

# 测试生成阶段：对每个候选调用表达式（fc）的最大重试次数
# 论文设定对“单个问题”最多 3 次；这里我们仅将“候选调用表达式”的重试设为可配置（默认 1 次）。
# 如需调整，可设置环境变量 RUG_TEST_GEN_RETRY_COUNT。
TEST_GEN_RETRY_COUNT = _env_int("RUG_TEST_GEN_RETRY_COUNT", 1)

# 统一的 target flag 构造（优先显式、其次自动主机、否则不指定）
def build_target_flag():
    explicit = os.getenv('RUG_RUST_TARGET')
    if explicit and explicit.strip():
        return f" --target {explicit.strip()}"
    auto = os.getenv('RUG_AUTO_TARGET', '0').lower()
    if auto in ['1', 'true', 'yes']:
        try:
            ret = subprocess.run('rustc -Vv', shell=True, capture_output=True, text=True)
            if ret.returncode == 0:
                for line in ret.stdout.splitlines():
                    if line.startswith('host:'):
                        host = line.split(':', 1)[1].strip()
                        if host:
                            return f" --target {host}"
        except Exception:
            pass
    return ''

def _ensure_log_bucket(target: str):
    global detailed_log
    if target not in detailed_log:
        detailed_log[target] = {
            "parameter_instantiation": [],
            "test_generation": []
        }

def _log_parameter_attempt(entry: dict):
    global detailed_log, current_target_function
    target = current_target_function or "GLOBAL"
    with log_lock:
        _ensure_log_bucket(target)
        # 自动赋予 attempt 序号（按追加顺序）
        entry = dict(entry)
        entry.setdefault("attempt", len(detailed_log[target]["parameter_instantiation"]) + 1)
        detailed_log[target]["parameter_instantiation"].append(entry)

def _log_test_attempt(entry: dict):
    global detailed_log, current_target_function
    target = current_target_function or "GLOBAL"
    with log_lock:
        _ensure_log_bucket(target)
        # 自动赋予 attempt 序号（按追加顺序）
        entry = dict(entry)
        entry.setdefault("attempt", len(detailed_log[target]["test_generation"]) + 1)
        detailed_log[target]["test_generation"].append(entry)

def _inc_stat(key: str, delta: int = 1):
    global stats
    if stats is None:
        return
    with stats_lock:
        stats[key] = stats.get(key, 0) + delta

def _memo_get(k):
    with memo_lock:
        return memo.get(k)

def _memo_set(k, v):
    with memo_lock:
        memo[k] = v

def _sanitize_table_cell(s: str, limit: int = 160) -> str:
    if s is None:
        return ''
    s = s.replace('\n', ' ').replace('\r', ' ')
    s = s.replace('|', '¦')  # avoid breaking markdown table
    if len(s) > limit:
        s = s[:limit] + '…'
    return s

def generate_markdown_report(stats: dict, detailed_log: dict) -> str:
    # Overall summary header
    lines = [
        '# RUG Run Summary',
        '',
        '| Metric                      | Count |',
        '| --------------------------- | ----- |',
        f"| Total Functions Targeted    | {stats['total_targets']} |",
        f"| Functions with Tests Generated | {stats['targets_succeeded']} |",
        f"| Functions Failed            | {stats['targets_failed']} |",
        f"| **Parameter Instantiation** |       |",
        f"| Total Attempts              | {stats['param_attempts']} |",
        f"| Successful Instantiations   | {stats['param_success']} |",
        f"| Failed Instantiations       | {stats['param_failures']} |",
        f"| **Test Code Generation**    |       |",
        f"| Total Attempts              | {stats['test_gen_attempts']} |",
        f"| Successful Compilations     | {stats['test_gen_success']} |",
        f"| Failed Compilations         | {stats['test_gen_failures']} |",
        '',
        '---',
        ''
    ]
    # Per-function detail sections
    for func, buckets in detailed_log.items():
        param_attempts = buckets.get('parameter_instantiation', [])
        test_attempts = buckets.get('test_generation', [])
        lines.append(f"## Function `{func}`")
        # Parameter attempts table
        if param_attempts:
            lines.append('### Parameter Instantiation Attempts')
            lines.append('| Attempt | Phase | Type | Compile Success | Verify Success | Compiler Output |')
            lines.append('| ------- | ----- | ---- | --------------- | -------------- | --------------- |')
            for entry in param_attempts:
                attempt = entry.get('attempt', '')
                phase = entry.get('phase', '')
                ty = entry.get('target_type', '')
                success = entry.get('success', False)
                # For now compile_success == verify_success == success (compile_verify encapsulates both)
                compile_success = '✅' if success else '❌'
                verify_success = '✅' if success else '❌'
                compiler_out = _sanitize_table_cell(entry.get('compiler_output', ''))
                lines.append(f"| {attempt} | {phase} | {ty} | {compile_success} | {verify_success} | {compiler_out} |")
            lines.append('')
        else:
            lines.append('### Parameter Instantiation Attempts')
            lines.append('*(none)*')
            lines.append('')
        # Test generation attempts table
        if test_attempts:
            lines.append('### Test Generation Attempts')
            lines.append('| Attempt | Compile Success | Compiler Output |')
            lines.append('| ------- | --------------- | --------------- |')
            for entry in test_attempts:
                attempt = entry.get('attempt', '')
                success = entry.get('success', False)
                compile_success = '✅' if success else '❌'
                compiler_out = _sanitize_table_cell(entry.get('compiler_output', ''))
                lines.append(f"| {attempt} | {compile_success} | {compiler_out} |")
            lines.append('')
        else:
            lines.append('### Test Generation Attempts')
            lines.append('*(none)*')
            lines.append('')
        # Divider
        lines.append('---')
        lines.append('')
    return '\n'.join(lines)

# 设定相关的全局变量，发送请求
def gpt_request(messages: list):
    """发送聊天补全请求，增加：
    - 每次请求前的详细日志（attempt、tokens估计、消息长度）
    - 可配置最大尝试次数 (RUG_API_MAX_ATTEMPTS, 默认 5)
    - 可配置调用超时 (RUG_API_CALL_TIMEOUT, 默认 60 秒)
    - 指数退避等待 (基础 2 秒，上限 20 秒)，避免一直 15 秒固定睡眠
    - RUG_DEBUG=1 时打印更多内部状态与异常堆栈
    返回 (finished, msg)
    """
    global client
    finished = False
    msg = ''
    max_attempts = _env_int('RUG_API_MAX_ATTEMPTS', 5)
    timeout_seconds = _env_int('RUG_API_CALL_TIMEOUT', 60)
    debug_flag = os.getenv('RUG_DEBUG', '0').lower() in ['1', 'true', 'yes']
    attempt = 0
    model_name = os.getenv('RUG_MODEL_NAME', 'gpt-4o-mini')
    max_resp_tokens = _env_int('RUG_API_MAX_RESPONSE_TOKENS', 2048)
    # 估算 tokens（粗略：字符/4）避免阻塞时毫无信息
    def _approx_tokens(txt: str) -> int:
        return max(1, len(txt) // 4)
    while attempt < max_attempts and not finished:
        attempt += 1
        prompt_preview = messages[-1]['content'][:240].replace('\n', ' ')
        approx_input_tokens = sum(_approx_tokens(m.get('content', '')) for m in messages)
        start_ts = time.time()
        with print_lock:
            print(f"[gpt_request] attempt={attempt}/{max_attempts} model={model_name} msgs={len(messages)} approx_tokens={approx_input_tokens} timeout={timeout_seconds}s")
            print(f"[gpt_request] last_msg_preview: {prompt_preview}")
        try:
            # 使用线程池包装，提供超时控制
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
            def _do_call():
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_resp_tokens,
                )
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_do_call)
                try:
                    response = fut.result(timeout=timeout_seconds)
                except FutTimeout:
                    fut.cancel()
                    raise TimeoutError(f"OpenAI call timed out after {timeout_seconds}s (attempt {attempt})")
            elapsed = time.time() - start_ts
            msg = response.choices[0].message.content if response and response.choices else ''
            with print_lock:
                print("=" * 40)
                print(f"[gpt_request] attempt {attempt} elapsed={elapsed:.2f}s finished response_preview={(msg[:200]+'…') if len(msg)>200 else msg}")
                if debug_flag:
                    print(messages[-1]['content'])
                    print('-' * 20)
                    print(msg)
            finished = True
        except Exception as e:
            elapsed = time.time() - start_ts
            with print_lock:
                print(f"[gpt_request] attempt {attempt} error after {elapsed:.2f}s: {e}")
                if debug_flag:
                    import traceback; traceback.print_exc()
            # 退出条件：上下文长度限制
            if "maximum context length" in str(e):
                break
            # 连接相关错误 => 重建 client
            if any(k in str(e).lower() for k in ['connection err', 'timeout', 'read timed out', 'remote disconnected']):
                api_key = os.getenv('OPENAI_API_KEY', '')
                base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    with print_lock:
                        print('[gpt_request] client reinitialized')
                except Exception as ie:
                    with print_lock:
                        print('[gpt_request] client reinit failed', ie)
            # 指数退避：2,4,8,16(封顶20)
            backoff = min(2 ** (attempt - 1), 20)
            with print_lock:
                print(f"[gpt_request] sleeping {backoff}s before retry")
            time.sleep(backoff)
    return (finished, msg)

# 初始化全局变量
def init_global(data):
    global single_path_import, glob_path_import, client
    # 从环境变量获取API密钥和基础URL
    api_key = os.getenv('OPENAI_API_KEY', '')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    client = OpenAI(api_key=api_key, base_url=base_url)
    glob = data['glob_path_import']
    glob_path_import = []
    glob_path_import = [(x, glob[x]) for x in glob]
    glob_path_import.sort(key=lambda x: len(x[0]), reverse=True)
    single_path_import = data['single_path_import']

# 解析日志文件，提取关键信息例如文件路径、函数名、生命周期、依赖关系等
def parse_log(file: str):
    ans = {}

    if not os.path.exists(file):
        print(file)
        raise Exception()
    with open(file, 'r') as fp:
        ls = fp.readlines()
        i = 0
        while i < len(ls):
            if ls[i].startswith("----"):
                lifetimes = ''
                idx = ls[i + 1].find(' ')
                target_file = ls[i + 1][:idx]
                target_func = ls[i + 1][idx + 1:-1]
                i += 1
                if ls[i + 1].startswith('\''):
                    lifetimes = ls[i + 1][:-1]
                    i += 1
                if not ls[i + 1].startswith("deps:"):
                    print(ls[i])
                    print(ls[i+1])
                assert ls[i + 1].startswith("deps:")
                deps = json.loads(ls[i + 1][5:])
                assert ls[i + 2].startswith("candidates:")
                candidates = json.loads(ls[i + 2][11:])
                i += 2
                stmts = []
                j = i + 1
                tys = []
                func_call = set()
                func_calls = []
                while j < len(ls) and not ls[j].startswith("-----"):
                    if ls[j].startswith('+'):
                        fc = ls[j][1:]
                        if fc not in func_call:
                            func_calls.append(fc)
                            func_call.add(fc)
                    else:
                        if '//' not in ls[j]:
                            pass
                        else:
                            stmts.append(ls[j])
                            if 'None+' in ls[j]:
                                tys.append((None, ls[j].split('+')[1].strip()))
                            else:
                                tys.append((ls[j].split('//')[1].strip(), None))
                    j += 1
                i = j
                if target_file not in ans:
                    ans[target_file] = []
                ans[target_file].append((target_file, stmts, func_calls, lifetimes, deps, candidates, target_func, tys))
            else:
                i += 1
    return ans

# 判断类型是否为标准库类型
def is_std(s: str):
    if s.startswith("&mut") or s.startswith("& mut "):
        s = s[s.find("mut") + 4:]
    elif s.startswith("&"):
        s = s[max(s.find(" ") + 1, 1):]
    if s.startswith('std::') or s.startswith('core::') or s.startswith('alloc::'):
        return True
    else:
        return False

# 处理GPT的输出，提取代码块
def handle_gpt_output(code:str):
    ans = []
    in_it = False
    if '```' not in code:
        return code
    for l in code.splitlines():
        if not in_it:
            if '```rust' in l or '```Rust' in l or '```RUST' in l:
                in_it = True
        else:
            if '```' in l:
                in_it = False
            else:
                ans.append(l)
    return "\n".join(ans)

# 加载分析结果的JSON文件
def load_analysis(f: str):
    ans = None
    with open(f, 'r') as fp:
        ans = json.load(fp)
    return ans

# 递归地为类型参数生成提示，处理类型边界和候选类型。接收类型参数的边界和候选类型列表，并尝试为每个候选类型生成代码示例。
def prompt_with_bounds(parent_def_path, def_path, ty, bounds, cans, deps, candidates, data, crate, file, src_pq, fd,
                       recur):
    if 'RUG_ANY' in cans and len(cans) > 1:
        cans = [x for x in filter(lambda x: x != 'RUG_ANY', cans)]
    found = False
    concrete_can = {}
    std_count = 0
    has_succeed = False
    for can in filter(lambda x: not (
            (x.startswith('<') or '::<' in x) and x.endswith('>')) and x != 'std::io::Stdin' and x not in recur,
                      cans):
        found = True
        recur.add(can)
        if is_std(can):
            std_count += 1
            if std_count < 3:
                concrete_can[can] = prompt_built_in(fd, parent_def_path, can, file, crate)
        elif can == 'RUG_ANY':
            concrete_can[can] = prompt_built_any(parent_def_path, def_path, ty)
        else:
            if len(deps.get(can, [])) == 0:
                # no other depends
                # prompt directly
                concrete_can[can] = prompt_with_src_only(parent_def_path, ty, can, data, fd, src_pq, file, crate)
            else:
                pass
                # concrete_can[can] = prompt_pre_context(parent_def_path, def_path, can, data, crate, file, src_pq)
                map = {}
                for k, vs in deps[can].items():
                    map[k] = prompt_with_bounds(can, can, k, vs, candidates.get(can, {}).get(k, []), deps, candidates,
                                                data, crate, file, src_pq, fd, recur)
                concrete_can[can] = prompt_with_context(parent_def_path, def_path, can, data, fd, file, map, src_pq, crate)
        recur.remove(can)
    if found:
        prompt = "For `{}` type in `{}`, we have {} candidates: `{}`\n".format(get_full_path(ty),
                                                                               get_full_path(parent_def_path),
                                                                               len(concrete_can), "`, `".join(
                [get_full_path(x) for x in concrete_can.keys()]))
        if len(concrete_can) == 1 and 'RUG_ANY' in concrete_can:
            prompt = "For `{}` type in `{}`, we don't find explicit bounds.\n".format(get_full_path(ty),
                                                                                      get_full_path(parent_def_path))
        for can, v in concrete_can.items():
            prompt += v[2] + "\n"
            src_pq.append(can)
        for can, v in concrete_can.items():
            if v[0]:
                return v
        return (False, '', prompt, ty)
    if not found:
        for can in filter(lambda x: (x.startswith('<') or '::<' in x) and x.endswith('>') and x not in recur, cans):
            # assert len(deps.get(can, {})) == 1
            for nty, nbounds in deps.get(can, {}).items():
                recur.add(can)
                found = True
                src_pq.append(nty)
                src_pq.append(can)
                ans = prompt_with_bounds(
                    can, can, nty, nbounds, candidates.get(can, {}).get(nty, []), deps, candidates, data, crate, file,
                    src_pq, fd, recur)
                prompt = "For `{}` type in `{}`, `{}` can be used: \n".format(get_full_path(ty),
                                                                              get_full_path(parent_def_path),
                                                                              get_full_path(can)) + ans[2]
                recur.remove(can)
                return (ans[0], ans[1], prompt, ans[3])
    if not found:
        for x in bounds:
            src_pq.append(x)
        return (False, '',
                "For `{}` type in `{}`, you need to write a concrete implementation that satisfied bounds: `{}`.\n".format(
                    get_full_path(ty), get_full_path(parent_def_path), ", ".join([get_full_path(x) for x in bounds])),
                ty)
    assert False

# 处理没有显式边界的类型参数
def prompt_built_any(parent_def_path, def_path, ty):
    cached = _memo_get(ty)
    if cached is not None:
        with print_lock:
            print('cached', ty)
        return cached
    prompt = "The `{}` in `{}` doesn't have type bounds. It might have other implicit bounds".format(get_full_path(ty),
                                                                                                     get_full_path(
                                                                                                         def_path))
    _memo_set(ty, (False, '', prompt, ty))
    return (False, '', prompt, ty)

# 处理标准库类型参数，直接生成代码示例
def prompt_built_in(fd, parent_def_path, ty, file, crate):
    cached = _memo_get(ty)
    if cached is not None:
        with print_lock:
            print('cached', ty)
        return cached
    prompt = "the `{}` can be used in {}. ".format(get_full_path(ty), get_full_path(parent_def_path))
    messages = copy.deepcopy(msgs)
    global counter
    with counter_lock:
        counter += 1
    var_name = 'v' + str(counter)
    content = """Please help me fill in the following code by creating an initialized local variable named `{}` with type `{}` using its constructor method or structual build in `{}` crate's {} file.
    Fill in any sample data if necessary. The code to fill is below and don't change function and mod names. Pay attention to the paths and reply the whole mod code only without other explanantions.
```rust
#[cfg(test)]
mod tests_prepare {{
    #[test]
    fn sample() {{
        let mut {} = // create the local variable {} with type {}
    }}
}}
```"""
    messages.append(
        {"role": "user", "content": content.format(var_name, get_full_path(ty), crate, file, var_name, var_name, get_full_path(ty))}
    )
    finished = False
    # 参数构造阶段仍保留最多 3 次尝试以符合论文描述；若需统一配置，可再引入环境变量。
    count = 3
    while not finished and count > 0:
        prompt_text = messages[-1]['content']
        has_ans, raw_code = gpt_request(messages)
        processed_code = handle_gpt_output(raw_code)
        success = False
        compile_log = ''
        if has_ans:
            # 参数阶段统计：尝试次数
            _inc_stat("param_attempts", 1)
            success, compile_log = compile_verify(fd, file, processed_code, 'tests_prepare', var_name, ty, crate)
            if success:
                finished = True
                _inc_stat("param_success", 1)
            else:
                _inc_stat("param_failures", 1)
        _log_parameter_attempt({
            "phase": "prompt_built_in",
            "target_type": get_full_path(ty),
            "prompt": prompt_text,
            "response_raw": raw_code,
            "response_processed": processed_code,
            "compile_success": success,
            "verify_success": success,
            "success": success,
            "compiler_output": compile_log
        })
        if not finished:
            count -= 1
    _memo_set(ty, (finished, processed_code if finished else raw_code, prompt, ty))
    return (finished, processed_code if finished else raw_code, prompt, ty)

# 仅编译代码以检查其有效性，若编译失败则还原文件
def compile_only(fd, file, code, crate):
    """仅尝试编译，返回 (是否成功, 输出日志)。始终回滚，确保重试环境干净。
    不再在成功时留下测试代码，成功由调用方之后通过 commit_test_code 持久化。
    """
    success = False
    stdout_text = ''
    stderr_text = ''
    with compile_lock:
        with open(fd + '/' + file, 'r+') as fp:
            origins = fp.readlines()
            mutate = copy.deepcopy(origins)
            code_adj = code.replace("use {}::".format(crate.replace('-', '_')), "use crate::")
            mutate.append(code_adj)
            fp.truncate(0)
            fp.seek(0)
            fp.writelines(mutate)
            fp.flush()
            os.fsync(fp.fileno())
            # 为了覆盖用户/仓库级默认配置的 cross target，这里显式追加目标（如果通过环境启用自动/显式）。
            target_flag = build_target_flag()
            debug_flag = os.getenv('RUG_DEBUG', '0').lower() in ['1', 'true', 'yes']
            cmd = f"cargo test{target_flag} -- --list"
            if debug_flag:
                print(f"[compile_only] running: {cmd} cwd={fd}")
            ret = subprocess.run(cmd, shell=True, cwd=fd, capture_output=True)
            stdout_text = ret.stdout.decode('utf-8', errors='ignore')
            stderr_text = ret.stderr.decode('utf-8', errors='ignore')
            if ret.returncode == 0:
                success = True
            # 始终回滚到 origins
            fp.truncate(0)
            fp.seek(0)
            fp.writelines(origins)
            fp.flush()
            os.fsync(fp.fileno())
    return (success, stdout_text if success else stderr_text)

def commit_test_code(fd, file, code, crate):
    """在确认测试代码通过编译后，真正写入文件。使用与尝试阶段相同的 use crate:: 路径替换。"""
    with compile_lock:
        with open(fd + '/' + file, 'r+') as fp:
            origins = fp.readlines()
            mutate = copy.deepcopy(origins)
            code_adj = code.replace("use {}::".format(crate.replace('-', '_')), "use crate::")
            mutate.append(code_adj)
            fp.truncate(0)
            fp.seek(0)
            fp.writelines(mutate)
            fp.flush()
            os.fsync(fp.fileno())

# 验证生成的代码是否能通过编译和测试
def compile_verify(fd, file, code, mod, var_name, ty, crate):
    """带验证执行，返回 (是否成功, 输出日志)。总是回滚文件。"""
    success = False
    stdout_text = ''
    stderr_text = ''
    with compile_lock:
        with open(fd + '/' + file, 'r+') as fp:
            origins = fp.readlines()
            mutate = copy.deepcopy(origins)
            code_adj = code.replace("use {}::".format(crate.replace('-', '_')), "use crate::")
            mutate.append(code_adj)
            fp.truncate(0)
            fp.seek(0)
            fp.writelines(mutate)
            fp.flush()
            os.fsync(fp.fileno())
            target_flag = build_target_flag()
            debug_flag = os.getenv('RUG_DEBUG', '0').lower() in ['1', 'true', 'yes']
            cmd = "cargo clean && RUG_VERIFY=1 MOD={} VAR={} cargorunner rudra{}".format(mod, var_name, target_flag)
            if debug_flag:
                print(f"[compile_verify] running: {cmd} cwd={fd}")
            ret = subprocess.run(cmd, shell=True, cwd=fd, capture_output=True)
            stdout_text = ret.stdout.decode('utf-8', errors='ignore')
            stderr_text = ret.stderr.decode('utf-8', errors='ignore')
            if ret.returncode == 0:
                success = True
            # 回滚
            fp.truncate(0)
            fp.seek(0)
            fp.writelines(origins)
            fp.flush()
            os.fsync(fp.fileno())
    return (success, stdout_text if success else stderr_text)

# 规范化/去重测试模块名，确保单次注入的代码块内不会产生重复的 mod 名称
def _normalize_test_modules(code: str, uid: int) -> str:
    """Rewrite any `mod tests` or existing `mod tests_rug_*` to unique names based on uid.

    - First occurrence -> tests_rug_{uid}
    - Subsequent occurrences -> tests_rug_{uid}_1, tests_rug_{uid}_2, ...

    This avoids E0428 (name defined multiple times) when the model outputs multiple
    test modules or reuses an existing tests_rug_* name.
    """
    # 匹配可选的 `pub ` 前缀，后接 `mod`，然后是 `tests` 或者已有的 `tests_rug_*` 名称
    pattern = re.compile(r"(\bpub\s+)?mod\s+(tests\b|tests_rug_[A-Za-z0-9_]+)\b")

    counter = 0

    def repl(m: re.Match) -> str:
        nonlocal counter
        vis = m.group(1) or ''  # 可能存在的 `pub `
        if counter == 0:
            new_name = f"tests_rug_{uid}"
        else:
            new_name = f"tests_rug_{uid}_{counter}"
        counter += 1
        return f"{vis or ''}mod {new_name}"

    return pattern.sub(repl, code)

# 获取字符串中的实际路径
def get_real_path(s: str):
    return s[s.find("\"") + 1:s.rfind("\"")]

# 处理有上下文信息的类型参数
def prompt_with_context(parent_def_path, def_path, ty, data, fd, file, ctxt, src_pq, crate):
    cached = _memo_get(ty)
    if cached is not None:
        with print_lock:
            print('cached', ty)
        return cached
    global counter
    with counter_lock:
        counter += 1
    var_name = 'v' + str(counter)
    targets = data['targets']
    dependencies = data['dependencies']
    srcs = data['srcs']
    struct_to_trait = data['struct_to_trait']
    trait_to_struct = data['trait_to_struct']
    self_to_fn = data['self_to_fn']
    type_to_def_path = data['type_to_def_path']
    struct_constructor = data['struct_constructor']
    prompt = "for `{}` used as `{}`, ".format(get_full_path(ty), get_full_path(def_path))
    cons = [get_full_path(x) for x in filter(lambda x: x not in ['clone'], struct_constructor.get(ty, []))]
    constructors = ''
    if len(cons) > 0:
        prompt += "try to use constructor functions like `{}` to build `{}`. ".format(", ".join(cons),
                                                                                      get_full_path(ty))
        constructors = "try to use constructor functions like `{}` to build `{}`. ".format(", ".join(cons),
                                                                                           get_full_path(ty))

    src_pq.append(ty)

    code = ''
    file_loc = ''
    if ty in srcs:
        code += srcs[ty][0]
        file_loc = " in {}".format(get_real_path(srcs[ty][1]))
    if ty in self_to_fn:
        for c in self_to_fn[ty]:
            if c not in 'CloneCopyDebug':
                code += c + '\n'
    info = prompt_struct.format(get_full_path(ty), file_loc, code)
    # context info
    for k, v in ctxt.items():
        if v[0]:
            # has concrete example
            tp = 'For the generic arg `{}`, `{}` can be used, the code to construct it as a local variable is shown below and is verified. Please reuse it without modifcations of statements.\n```rust\n{}\n```'.format(
                k, get_full_path(v[3]), v[1])
        else:
            tp = 'For the generic arg `{}`, here are the hints: {}'.format(k, v[2])
        info += tp
        prompt += tp
    messages = copy.deepcopy(msgs)
    content = """Please help me fill in the following code by creating an initialized local variable named `{}` with type `{}` using its constructor method or structual build. {}
{}  
The code to fill is below and don't change function and mod names. Fill in any sample data if necessary. Pay attention to the paths and reply with the code only without other explanantions.
```rust
#[cfg(test)]
mod tests_prepare {{
    #[test]
    fn sample() {{
        let mut {} = // create the local variable {} with type {}
    }}
}}
```"""
    messages.append(
        {"role": "user", "content": content.format(var_name, get_full_path(ty), constructors, info, var_name, var_name,
                                                   get_full_path(ty))}
    )
    finished = False
    # 参数构造阶段仍保留最多 3 次尝试；当前需求仅减少候选调用表达式的重试次数。
    count = 3
    while not finished and count > 0:
        prompt_text = messages[-1]['content']
        has_ans, raw_code = gpt_request(messages)
        processed_code = handle_gpt_output(raw_code)
        success = False
        compile_log = ''
        if has_ans:
            _inc_stat("param_attempts", 1)
            success, compile_log = compile_verify(fd, file, processed_code, 'tests_prepare', var_name, ty, crate)
            if success:
                finished = True
                _inc_stat("param_success", 1)
            else:
                _inc_stat("param_failures", 1)
        _log_parameter_attempt({
            "phase": "prompt_with_context",
            "target_type": get_full_path(ty),
            "prompt": prompt_text,
            "response_raw": raw_code,
            "response_processed": processed_code,
            "compile_success": success,
            "verify_success": success,
            "success": success,
            "compiler_output": compile_log
        })
        if not finished:
            count -= 1
    _memo_set(ty, (finished, processed_code if finished else raw_code, prompt, ty))
    return (finished, processed_code if finished else raw_code, prompt, ty)

# 处理仅有源代码信息的类型参数
def prompt_with_src_only(parent_def_path, def_path, ty, data, fd, src_pq, file, crate):
    cached = _memo_get(ty)
    if cached is not None:
        return cached
    src_pq.append(ty)
    targets = data['targets']
    dependencies = data['dependencies']
    srcs = data['srcs']
    struct_to_trait = data['struct_to_trait']
    trait_to_struct = data['trait_to_struct']
    self_to_fn = data['self_to_fn']
    type_to_def_path = data['type_to_def_path']
    struct_constructor = data['struct_constructor']
    struct_constructor = data['struct_constructor']

    prompt = "the `{}` satisfies `{}` in `{}`. ".format(get_full_path(ty), get_full_path(def_path),
                                                        get_full_path(parent_def_path))
    cons = [get_full_path(x) for x in filter(lambda x: x not in ['clone'], struct_constructor.get(ty, []))]
    constructors = ''
    if len(cons) > 0:
        prompt += "Try to use constructor functions like `{}` to build `{}`. ".format(", ".join(cons),
                                                                                      get_full_path(ty))
        constructors = "Try to use constructor functions like `{}` to build `{}`. ".format(", ".join(cons),
                                                                                           get_full_path(ty))
    code = ''
    file_loc = ''
    if ty in srcs:
        code += srcs[ty][0]
        file_loc = " in {}".format(get_real_path(srcs[ty][1]))
    if ty in self_to_fn:
        for c in self_to_fn[ty]:
            if c not in 'CloneCopyDebug':
                code += c + '\n'
    info = prompt_struct.format(get_full_path(ty), file_loc, code)
    messages = copy.deepcopy(msgs)
    global counter
    with counter_lock:
        counter += 1
    var_name = 'v' + str(counter)
    content = """Please help me fill in the following code by creating an initialized local variable named `{}` with type `{}` using its constructor method or structual build in `{}` crate {} file. {}
{}  
The code to fill is below and don't change function and mod names. Fill in any sample data if necessary. Pay attention to the paths and reply with the code only without other explanantions.
```rust
#[cfg(test)]
mod tests_prepare {{
    #[test]
    fn sample() {{
        let mut {} = // create the local variable {} with type {}
    }}
}}
```"""
    messages.append(
        {"role": "user", "content": content.format(var_name, get_full_path(ty), crate, file, constructors, info, var_name, var_name,
                                                   get_full_path(ty))}
    )
    finished = False
    # 参数构造阶段仍保留最多 3 次尝试；如需后续外部配置，可与 TEST_GEN_RETRY_COUNT 类似扩展。
    count = 3
    while not finished and count > 0:
        prompt_text = messages[-1]['content']
        has_ans, raw_code = gpt_request(messages)
        processed_code = handle_gpt_output(raw_code)
        success = False
        compile_log = ''
        if has_ans:
            _inc_stat("param_attempts", 1)
            success, compile_log = compile_verify(fd, file, processed_code, 'tests_prepare', var_name, ty, crate)
            if success:
                finished = True
                _inc_stat("param_success", 1)
            else:
                _inc_stat("param_failures", 1)
        _log_parameter_attempt({
            "phase": "prompt_with_src_only",
            "target_type": get_full_path(ty),
            "prompt": prompt_text,
            "response_raw": raw_code,
            "response_processed": processed_code,
            "compile_success": success,
            "verify_success": success,
            "success": success,
            "compiler_output": compile_log
        })
        if not finished:
            count -= 1
    _memo_set(ty, (finished, processed_code if finished else raw_code, prompt, ty))
    return (finished, processed_code if finished else raw_code, prompt, ty)

# 根据类型获取完整路径
def get_full_path(ty: str):
    if ty in single_path_import:
        return single_path_import[ty]
    for k, v in glob_path_import:
        if ty.startswith(k):
            t = ''
            if len(v) > 1:
                t = v
            assert not (t + ty[len(k) + 2:]).startswith("::")
            return t + ty[len(k) + 2:]
    return ty


# 定义各种提示模板
prompt_target = """The target function is `{}` in `{}` crate's {} file, its definition path is `{}`{} and source code is like below:
```rust
{}
```

"""

prompt_dep = """The bounds and generic parameter info is shown below:
```
{}
```

"""

prompt_struct = """ The relevant definition, and method of `{}`{} are shown below:
```rust
{}
```
"""

prompt_impls = """The `{}` impls `{}` traits.
"""

prompt_rimpls = """The `{}` trait has `{}` that implements it.
"""

uid = 0

def _scan_existing_test_module_ids(src_root: str) -> int:
    """扫描 src 目录下已有的 `mod tests_rug_<n>` 模块，返回最大 n。
    若不存在返回 -1。
    只匹配顶层/任意位置的 `mod tests_rug_数字`，不区分前置可见性。
    """
    max_id = -1
    pattern = re.compile(r"\bmod\s+tests_rug_(\d+)\b")
    for root, _, files in os.walk(os.path.join(src_root, 'src')):
        for fn in files:
            if not fn.endswith('.rs'):
                continue
            fp = os.path.join(root, fn)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                for m in pattern.finditer(text):
                    try:
                        val = int(m.group(1))
                        if val > max_id:
                            max_id = val
                    except ValueError:
                        pass
            except Exception:
                pass
    return max_id

# 处理单个文件夹，生成单元测试
def run_single_fd(work_dir:str):
    global uid
    global detailed_log, current_target_function
    global stats
    enc = tiktoken.encoding_for_model("gpt-4")
    import copy
    init = """You are an expert in Rust. I need your help to develop unit tests for the given function in the crate.I will give you the information about the target function and relevant definitions. I may give you the sample code to build the parameters, please strictly follow the sample code to construct the variable (you can change the variable names) and its use statements since these code are verified. Please only output the unit test(Rust code) for the targetfunction without any explainations and be strict about compiler checks and import paths. Please prepare the inital test data if necessary."""
    msgs = [
        {"role": "system", "content": init},

    ]
    ok = 0
    exceed_16 = 0
    exceed_128 = 0
    total = 0
    # 初始化详细日志容器
    detailed_log = {}
    current_target_function = None
    stats = {
        "total_targets": 0,
        "targets_succeeded": 0,
        "targets_failed": 0,
        "param_attempts": 0,
        "param_success": 0,
        "param_failures": 0,
        "test_gen_attempts": 0,
        "test_gen_success": 0,
        "test_gen_failures": 0
    }
    
    try:
        # 确认工作目录存在（应为已复制的副本）
        if not os.path.isdir(work_dir):
            print(f"!!! Error: Work directory '{work_dir}' not found.")
            return
        # 获取工作区中的crate名称（副本目录名即 crate 名）
        crate = os.path.basename(work_dir)
        # 工作路径（副本根）
        path = os.path.abspath(work_dir)  # 使用工作目录的绝对路径
        # 基于已存在的 tests_rug_* 模块设定 uid 起点，避免重名
        try:
            existing_max = _scan_existing_test_module_ids(path)
            if existing_max >= 0:
                # 加 1 作为起始，避免与现有重复
                global uid
                uid = existing_max + 1
                print(f"--- Detected existing tests_rug_* max id = {existing_max}, starting uid from {uid} ---")
        except Exception as e:
            print(f"--- Warning: scanning existing test modules failed: {e} ---")
        # 获取工作区中的crate列表（若将来支持 workspace，可在此扩展）
        # fin = subprocess.run('cargo ws list -l', shell=True, cwd=work_dir, capture_output=True)
        # 逐个处理工作区中的crate
        # for l in fin.stdout.decode('utf-8').splitlines():
        #     ls = l.split(' ')
        #     crate = ls[0].strip()
        #     path = ls[-1]
        # Helper: build optional --target flag (removed previous hardcoded target).
        # Priority:
        # 1. RUG_RUST_TARGET explicit value
        # 2. RUG_AUTO_TARGET=1 => detect host via `rustc -Vv` (best-effort)
        # 3. default => no --target (use rustup default for host)
        # 复用全局 build_target_flag() 保证所有阶段一致
        target_flag = build_target_flag()

        for _ in ["once"]:  # single crate flow retained
            # 生成分析JSON文件和日志文件
            # 如果分析文件不存在，则运行分析命令生成
            if not os.path.exists(work_dir+'/'+crate+'.json'):
                print(f"--- Running analysis for {crate} (generating .json) ---")
                # 使用可配置 target_flag (可能为空)。不再硬编码平台三元组。
                analysis_cmd = f'cargo clean && CHAT_UNIT=1 cargorunner rudra{target_flag}'
                result = subprocess.run(analysis_cmd, shell=True, capture_output=True, text=True, cwd=path) # 使用 path 作为 cwd
                if result.returncode != 0:
                    print(f"!!! Analysis command failed for {crate} !!!")
                    print(f"CWD: {path}")
                    print(f"Return Code: {result.returncode}")
                    print("--- STDERR ---")
                    print(result.stderr)
                    # 失败后直接退出，不再继续
                    continue 
                subprocess.run('mv preprocess.json {}.json'.format(crate), shell=True, capture_output=True, cwd=work_dir)
            # 如果日志文件不存在，则运行测试命令生成
            if not os.path.exists(work_dir+"/"+crate+".out.txt"):
                print(f"--- Running analysis for {crate} (generating .out.txt) ---")
                # 使用同样的 target_flag
                log_gen_cmd = f'cargo clean && UNIT_GEN=s1 cargorunner rudra{target_flag}'
                fin = subprocess.run(log_gen_cmd, shell=True, capture_output=True, text=True, cwd=path) # 使用 path 作为 cwd
                if fin.returncode != 0:
                    print(f"!!! Log generation command failed for {crate} !!!")
                    print(f"CWD: {path}")
                    print(f"Return Code: {fin.returncode}")
                    print("--- STDERR ---")
                    print(fin.stderr)
                    # 失败后直接退出，不再继续
                    continue
                with open(work_dir+"/"+crate+".out.txt", 'w') as fp:
                    fp.writelines("\n".join(fin.stdout.splitlines()))
            # 加载分析结果的JSON文件
            if os.path.exists(work_dir+'/'+crate+'.json'):
                data = load_analysis(work_dir+'/'+crate+'.json')
                targets = data['targets']
                dependencies = data['dependencies']
                srcs = data['srcs']
                struct_to_trait = data['struct_to_trait']
                trait_to_struct = data['trait_to_struct']
                self_to_fn = data['self_to_fn']
                type_to_def_path = data['type_to_def_path']
                init_global(data)
                # 解析日志文件，提取关键信息
                ans = parse_log(work_dir + "/{}.out.txt".format(crate))
            for f, vv in ans.items():
                # 对于每个文件，处理其中的函数调用信息
                file = f
                for (_, stmts, func_call, lifetimes, deps, candidates, target_func, tys) in vv:
                    _inc_stat("total_targets", 1)
                    # 过滤掉以/home开头的文件和特定函数
                    if file.startswith("/home") or target_func.endswith(">::fmt"):
                        continue
                    if target_func not in targets:
                        print('missing', target_func)
                        continue
                    uid += 1    # uid用于唯一标识每个生成的单元测试
                    total += 1  # total用于统计生成的单元测试数量
                    meta = targets[target_func] # meta包含函数的名称和可选的trait信息
                    func_name = meta[0]
                    optional_trait = meta[2]
                    final_prompt = ''
                    parent_def_path = target_func   # parent_def_path表示函数的定义路径
                    # 为当前目标函数准备日志桶
                    current_target_function = target_func
                    _ensure_log_bucket(current_target_function)
                    src_pq = [] # src_pq用于存储需要包含在单元测试中的源代码路径
                    has_sample = set()  # has_sample用于记录已经有样例代码的参数索引

                    # 并行生成每个参数的提示（仅 GPT 交互并发，编译阶段被锁串行）
                    def _param_job(idx, ty, primitive):
                        local_src = []
                        if ty is not None:
                            def_path = ty
                            if ty in type_to_def_path:
                                def_path = type_to_def_path[ty]
                            prmpt = ''
                            if target_func in deps and ty in deps[target_func]:
                                bounds = deps[target_func][ty]
                                cans = []
                                if ty in candidates[target_func]:
                                    cans = candidates[target_func][ty]
                                prmpt = prompt_with_bounds(parent_def_path, def_path, ty, bounds, cans, deps, candidates,
                                                           data, crate, f, local_src, work_dir, set())
                            if len(prmpt) == 0:
                                if is_std(ty):
                                    prmpt = prompt_built_in(work_dir, parent_def_path, ty, file, crate)
                                else:
                                    prmpt = prompt_with_src_only(parent_def_path, def_path, ty, data, work_dir, local_src, f, crate)
                            return (idx, True, prmpt, local_src, ty, primitive)
                        else:
                            # primitive 类型：不需要 GPT
                            return (idx, False, None, [], ty, primitive)

                    thread_count = int(os.getenv("RUG_GPT_THREADS", "4"))
                    jobs = []
                    with ThreadPoolExecutor(max_workers=max(1, thread_count)) as executor:
                        futures = []
                        for idx, (ty, primitive) in enumerate(tys):
                            futures.append(executor.submit(_param_job, idx, ty, primitive))
                        for fut in as_completed(futures):
                            idx, has_ty, prmpt, local_src, ty_v, primitive_v = fut.result()
                            if not has_ty:
                                final_prompt += "For {}th argument, its type is `{}`, please use some sample data to initialize it.\n".format(idx + 1, primitive_v)
                                continue
                            # 聚合结果
                            if prmpt and prmpt[0]:
                                has_sample.add(idx)
                                final_prompt += "For {}th argument, `{}` can be used, please use following sample code to construct it:\n```rust\n{}\n```\n".format(
                                    idx + 1, prmpt[3], prmpt[1])
                            else:
                                src_pq.extend(local_src)
                                final_prompt += "For {}th argument, `{}` can be used, please use following description to construct it:\n```\n{}\n```\n".format(
                                    idx + 1, prmpt[3] if prmpt else ty_v, prmpt[2] if prmpt else "")
                    # request for unit test
                    target = target_func
                    deps = dependencies[target]
                    func_src = srcs[target][0]
                    trait_stmt = ''
                    if len(optional_trait) > 0:
                        trait_stmt = ", as an implmeent of `{}` trait".format(optional_trait)
                    pr_target = prompt_target.format(func_name, crate, file, target, trait_stmt, func_src)
                    src_pq = set(src_pq)
                    single_test_template = """ 
        #[cfg(test)]
        mod tests {{
            use super::*;
            {}
            #[test]
            fn test_rug() {{
                {}
                
                {}
            }}
        }}
                            """
                    succeed = False
                    for fc in reversed(func_call):
                        if '<' in fc and (' for ' in fc or ' as ' in fc):
                            continue
                        params = ''
                        param_template = "let mut p{} = ... ;\n"
                        no_sample = set()
                        for idx, (ty, primitive) in enumerate(tys):
                            params += param_template.format(idx)
                            if idx not in has_sample:
                                no_sample.add(idx)
                        option_t = ""
                        if len(optional_trait) > 0:
                            option_t = "use crate::{};".format(get_full_path(optional_trait))
                        tests = single_test_template.format(option_t, params, fc)
                        output = pr_target
                        test_template = """
        Please help me following steps on the code below to build the unit test:
        
        1. fill in the {} variables in the following code using the samples without modifications and keep the type declarations
        2. construct the variables {} based on hints if there isn't a sample and fill in the generic args if I didn't give you the generic args
        3. combine all the use statements and place them inside the `tests` mod, remove the duplicated use, but don't add new ones
        
        ```rust
        {}
        ```
                                """
                        output += test_template.format(", ".join(["p" + str(x) for x in has_sample]),
                                                       ", ".join(["p" + str(x) for x in no_sample]), tests)
                        output += final_prompt
                        for dep in src_pq:
                            code = ''
                            file_loc = ''
                            if dep in srcs:
                                code += srcs[dep][0]
                                file_loc = " in {}".format(get_real_path(srcs[dep][1]))
                            if dep in self_to_fn:
                                for c in self_to_fn[dep]:
                                    if c not in 'CloneCopyDebug':
                                        code += c + '\n'
                            if len(code) > 0:
                                output += prompt_struct.format(get_full_path(dep), file_loc, code)

                        print('=' * 40)
                        messages = copy.deepcopy(msgs)
                        messages.append({"role": "user", "content": output})
                        finished = False
                        # 针对单个候选调用表达式（fc）的重试次数，默认 1 次，可通过 RUG_TEST_GEN_RETRY_COUNT 配置
                        count = TEST_GEN_RETRY_COUNT
                        while not finished and count > 0:
                            prompt_text = output
                            has_ans, raw_code = gpt_request(messages)
                            processed = handle_gpt_output(raw_code)
                            processed_code = _normalize_test_modules(processed, uid)
                            success = False
                            compile_log = ''
                            if has_ans:
                                try:
                                    if stats is not None:
                                        stats["test_gen_attempts"] += 1
                                except Exception:
                                    pass
                                success, compile_log = compile_only(work_dir, file, processed_code, crate)
                                if success:
                                    finished = True
                                    succeed = True
                                    # 成功后再持久化写入，避免失败残留导致重复模块
                                    commit_test_code(work_dir, file, processed_code, crate)
                                    try:
                                        if stats is not None:
                                            stats["test_gen_success"] += 1
                                    except Exception:
                                        pass
                                else:
                                    try:
                                        if stats is not None:
                                            stats["test_gen_failures"] += 1
                                    except Exception:
                                        pass
                            _log_test_attempt({
                                "prompt": prompt_text,
                                "response_raw": raw_code,
                                "injected_code": processed_code,
                                "compile_success": success,
                                "success": success,
                                "compiler_output": compile_log
                            })
                            if not finished:
                                count -= 1
                        if finished:
                            print('unit gen succeed', target_func)
                            ok += 1
                            break
                    if not succeed:
                        print('unit gen err', target_func)
                        _inc_stat("targets_failed", 1)
                    else:
                        _inc_stat("targets_succeeded", 1)
        print(ok, exceed_16, total)
        # 生成 Markdown 统计报告（写入运行副本目录）
        try:
            report_md = generate_markdown_report(stats, detailed_log)
            summary_name = f"{work_dir}/rug_summary.md"
            with open(summary_name, 'w') as fp_md:
                fp_md.write(report_md)
            print(f"--- Saved markdown summary to {summary_name} ---")
        except Exception as e:
            print(f"--- Warning: failed to write markdown summary: {e} ---")
    
    finally:
        # 保存运行产物（不再删除工作副本）到副本目录
        try:
            # 保存详细日志到工作副本目录
            import json as _json_local
            out_name = f"{work_dir}/detailed_log.json"
            with open(out_name, 'w') as _fp_log:
                _json_local.dump(detailed_log, _fp_log, indent=2, ensure_ascii=False)
            print(f"--- Saved detailed log to {out_name} ---")
        except Exception as e:
            print(f"--- Warning: Failed to save artifacts: {e} ---")

# 多进程运行单个文件夹的处理函数
def run_single(fd):
    """为给定源目录 fd 创建一个持久化的副本，并在该副本中运行。"""
    try:
        src_path = os.path.abspath(fd)
        if not os.path.isdir(src_path):
            print(f"!!! Error: Source directory '{src_path}' not found.")
            return
        # 输出根目录位于项目根目录（example 的上级目录）
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        runs_root = os.path.join(project_root, "rug_runs")
        os.makedirs(runs_root, exist_ok=True)
        run_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = os.getenv("RUG_MODEL_NAME", "gpt-3.5-turbo")
        crate_name = os.path.basename(src_path)
        output_dir = os.path.join(runs_root, f"{crate_name}_{model_name}_{run_timestamp}")
        print(f"--- Creating run copy: {output_dir} ---")
        shutil.copytree(src_path, output_dir)
        # 直接在当前进程内运行
        run_single_fd(output_dir)
    except Exception as e:
        print(f"run_single error: {e}")


if __name__ == '__main__':
    args = []
    if len(sys.argv) < 2:
        # os.chdir(sys.argv[1])
        for fd in os.listdir('.'):
            if not os.path.isdir(fd):
                continue
            # fd = sys.argv[1]
            fin = subprocess.run('cargo ws list -l', shell=True, cwd=fd, capture_output=True)
            if fin.returncode == 0:
                args.append(fd)
        # print(args)
        with multiprocessing.Pool(8) as p:
            p.map(run_single, args)
    else:
        # 单 crate 运行：参数为源目录，创建持久化副本后在副本内运行
        fd = sys.argv[1]
        run_single(fd)
