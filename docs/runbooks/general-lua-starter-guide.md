# 通用 Lua 反编译 Starter Guide

本指南面向与原游戏、本地化工程无关的新任务。你只需本仓库和待处理的 Lua 5.1 字节码，不需要前作反编译器、游戏文件或翻译资产。以下命令均从仓库根目录执行；API 以本次指南提交时的实现为准。

## 1. 先确认输入与验收目标

本项目读取的是 **bytecode chunk**，不是普通 `.lua` 源码；扩展名不能区分两者。支持范围由 `src/pyluadec/ingest/header.py` 定义：

| 字段 | 支持值 |
| --- | --- |
| 签名 / 版本 / 格式 | `1b 4c 75 61` / `0x51` / `0` |
| 字节序 | little-endian |
| `int` / Instruction | 4 / 4 字节 |
| 序列化 `size_t` | 4 或 8 字节，与宿主指针宽度无关 |
| `lua_Number` | 8 字节、非 integral（double） |

Lua 5.2–5.4、LuaJIT、加密封装、自定义 opcode 或改造 VM 不在现有支持范围。仅修改头部版本不能转换字节码。头部匹配也不能证明定制 VM 的执行语义匹配，需确认目标运行时。

先约定交付物：可读源码、原始输入哈希、认证报告、运行环境、残留问题。把“行为正确”和“可读性”分别验收；原变量名、注释和原始排版通常无法从 stripped 字节码恢复。

## 2. 构建与基础检查

准备 Git、Python ≥ 3.12、uv、CMake ≥ 3.24、C/C++17 工具链和 `patch`。具体平台准备见 [64 位构建指南](64bit-migration.md)。

```bash
uv sync --locked
./scripts/build_native.sh
uv run pytest -q
```

构建生成 `build/lua_sz4`、`build/luac_sz4`、sz8 变体，以及 `src/pyluadec/_native/` 的 Python 扩展。Python ABI 或机器改变后需要重建；`uv sync` 本身不构建这些扩展。不要用系统里的其他版本 `luac` 替代仓库 oracle。

无历史语料时部分测试会 skip，这是基础自检，不代表历史语料全量验收。`PYLUADEC_CORPUS_DIR` / `PYLUADEC_PRED_CORPUS_DIR` 是旧语料测试入口；**不要为消除 skip 把它们指向新任务数据**，部分测试校验固定的文件集与台账。新任务的验收应独立保存。

## 3. 跑通一个与游戏无关的任务

下面创建一个数值求和例子，编译、反编译，并保存精确的输出字节及报告。`build/` 被 Git 忽略，正式任务应把需要留档的结果复制到独立交付目录或任务仓库。

```bash
mkdir -p build/starter-demo
cat > build/starter-demo/input.lua <<'LUA'
local total = 0
for i = 1, 5 do
    total = total + i
end
print(total)
LUA
build/luac_sz4 -s -o build/starter-demo/input.luac build/starter-demo/input.lua
```

接下来这个 Python 片段也是处理实际文件的最小模板：更换 `input_path` 和 `output_dir` 即可。保留输入原件，不要覆盖。

```bash
uv run python - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path
from pyluadec import oracle
from pyluadec.ingest import load_file
from pyluadec.pipeline import decompile_chunk
from pyluadec.verify.certify import carries_debug, certify_l3
from pyluadec.verify.normalize import LADDER_VERSION

input_path = Path("build/starter-demo/input.luac")
output_dir = Path("build/starter-demo/result")
output_dir.mkdir(parents=True, exist_ok=True)
original = load_file(input_path)
result = decompile_chunk(original, proposals={}, naming={})
source_path = output_dir / "decompiled.lua"
source_path.write_bytes(result.source)
# 显式检查编译成功。certify_l3 的 L1 本身不能区分编译失败和比较失败。
compiled = oracle.compile_source(result.source, strip=not carries_debug(original))
(output_dir / "recompiled.luac").write_bytes(compiled)
# 验证实际写盘的整个 chunk，不能只凭逐 proto 等级判断交付物。
cert = certify_l3(original, source_path.read_bytes())
sha256 = lambda data: hashlib.sha256(data).hexdigest()
report = {
    "input": str(input_path),
    "input_sha256": sha256(input_path.read_bytes()),
    "source_sha256": sha256(source_path.read_bytes()),
    "recompiled_sha256": sha256(compiled),
    "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"])),
    "oracle_sha256": sha256(oracle.luac_sz4().read_bytes()),
    "ladder": LADDER_VERSION,
    "compile_ok": True,
    "whole_chunk": {"level": cert.level, "rung": cert.rung,
                    "mismatches": [{"path": m.path, "field": m.field}
                                   for m in cert.mismatches]},
    "levels": result.levels,
    "rungs": result.rungs,
    "reasons": result.reasons,
    "shipped_fallback": result.shipped_fallback,
    "shipped_proposal": result.shipped_proposal,
    "proposal_rung": result.proposal_rung,
    "hybrid": result.hybrid,
    "confessions": result.confessions_by_proto,
}
(output_dir / "report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print(json.dumps(report["whole_chunk"]))
PY
```

此例应得到整文件 `L3`、rung `0` 或 `1`；输出等级取决于真实比较，不硬编码成功。可以再执行这个已知安全的例子：

```bash
build/lua_sz4 build/starter-demo/input.luac > build/starter-demo/original.stdout
build/lua_sz4 build/starter-demo/result/decompiled.lua > build/starter-demo/candidate.stdout
diff -u build/starter-demo/original.stdout build/starter-demo/candidate.stdout
```

两边应均输出 `15`。这一次 stdout 一致只是此输入的动态证据。实际任务需按业务准备环境和测试，而不能照搬这个断言。对不可信字节码，原生解析及动态执行都应放进有资源限制的隔离环境；本项目不是安全沙箱。

### 为何不直接调用 `decompile_file()`？

目前 `decompile_file(path)` 会按 `path.name` 加载 `corpus/proposals` 与 `corpus/naming` 的历史清单。同名的新文件也会进入这个流程。通用入口用 `load_file` + `decompile_chunk(..., proposals={}, naming={})`，避免原项目资产参与。

同理，`scripts/run_corpus.py`、warranty、naming 和若干 probe/ratchet 脚本属于历史语料工作流，不能直接当成通用批处理 CLI；尤其不要让新任务重写 `corpus/ledger.jsonl`、golden、pins 或 `corpus/final/`。

批量处理时，在上述模板外加文件遍历，按输入相对路径保存每份源码和报告，避免不同子目录同名文件互相覆盖。每个文件独立捕获解析/编译异常，写入失败清单；任何失败必须反映到批处理退出码，不能只统计已成功的文件。4/8 字节输入由 ingest 自动分派，oracle 产出的 sz4 字节码不保证可直接部署到使用另一 ABI 的目标运行时。

## 4. 正确解释认证结果

| 证据 | 能说明什么 | 不能说明什么 |
| --- | --- | --- |
| 编译成功（最低层证据） | 产物是该 Lua 编译器接受的源码 | 与输入等价 |
| 差分执行 / L1.5、L1.75、L2 类探针 | 指定环境、输入、观测范围内一致 | 未运行路径或所有上下文等价 |
| L3.0（rung 0） | 重编译后的整棵 proto 按比较器逐字段相同 | 逐字节相同的文件、证明过的编译器/VM |
| L3.1（rung 1） | 仅归一化指定 debug 信息后，整棵 proto 相同 | debug API、错误文本、行号等观察相同 |

现有阶梯只有 `L3.0` 与 `L3.1`，版本是 `l3-ladder-v1`。rung 1 清除 source、行信息、局部变量名和 upvalue 名，但保留局部作用域范围、数量、指令字、常量原始数值位模式、栈帧参数及所有子 proto。细节和健全性论证见 `verify/normalize.py`。不要把历史设计里讨论的更高 rung 当成已经实现的能力。

`DecompileResult.levels` 是自动重建的逐 proto 认证记录，**不是最终产物的完整认证摘要**：

- `shipped_fallback[path]` 表示实际输出该部分是否用了状态机；不能由 `levels[path]` 推导。
- hybrid 可能保留 fallback 子树；不能把混合认证说成全树 L3。
- proposal 整树认证成功后，自动重建的原 `levels` 仍可能是 L1；同时检查 `proposal_rung`、`shipped_proposal`，并对最终文件再跑 `certify_l3`。
- `certify_l3` 返回 L1 也可能是编译失败，且这时 `mismatches` 为空。所以模板显式先编译，再做认证。
- `main_0_1` 是管线 proto 路径；比较器的 `root/0/1` 指向同一位置。

这里的 L3 是实用的 **translation validation（针对产物的重编译比对）**。可信基础包含 Lua 编译器、VM、原生读取桥、比较器和归一化规则；仓库没有用 Lean/Coq 等证明助手验证整个链路。即使 L3.1 通过，也须明确排除 debug 观察差异，以及目标运行时与 oracle 不一致的情形。源文件哈希、认证结果与实际交付文件必须绑定；后续手工润色会使旧报告失效。

## 5. 质量不足时如何修复

先定位质量问题，再选工作路线：

1. **解析拒绝或未知 VM**：先查头部、封装和 VM 指令语义，解决兼容性；不要跳过读取校验。
2. **正确但难读**：若已整树 L3，先保留已认证版本；重命名、整理排版后再认证。stripped 输入允许较多命名调整，但不保证 debug 行为一致。
3. **fallback / hybrid / L1**：按 `reasons` 和失配 `field` 定位。将最小相关函数、指令列表、上值绑定和实际输入交给修复 agent；不要只给整个巨大状态机要求“美化”。
4. **动态差异**：保存首个不同事件和最小输入序列，检查求值顺序、短路条件、表/元方法、闭包捕获、vararg、多返回值、nil 空洞、tailcall 和循环边界。不要排序事件来隐藏副作用顺序差异。

查看字节码可用匹配输入宽度的工具，例如 sz4：

```bash
build/luac_sz4 -p -l -l build/starter-demo/input.luac > build/starter-demo/input.listing.txt
```

`-p` 防止 listing 命令在当前目录生成 `luac.out`；sz8 输入改用 `luac_sz8`。失配常见原因：`code` 是指令或寄存器分配/求值顺序差异；`const[...]` 是常量或顺序差异；`nups` 是闭包绑定差异；`locvars` 是 debug 局部作用域差异。不要为了让未剥离输入通过，私自 strip 原件、删除作用域字段或放宽比较器。

两条修复路线可以并用：

- **修项目**：为可泛化的模式修复 `express/`、`sir/`、`emit/`，加入能在修复前失败的最小语义回归。维持默认严格 effect 模型；通过相关测试，再运行整套测试。有原语料时另跑旧台账回归。
- **修这份产物**：直接编辑候选源码，并用原始 root 对整个候选调用 `certify_l3`。这条路无需扩展反编译器，也能取得整树 L3，适合一次性任务。

还可使用已有 propose-and-certify 通道，为自动重建拒绝的 **非根函数** 提交 wrapper 源码（参数个数、vararg 标志和上值顺序必须来自原 proto）：

```lua
local u0 -- 无 upvalue 时省略；多个时按原始索引声明 u0, u1, ...
return function(arg0)
    return u0(arg0)
end
```

以下是接入形状，路径与函数仅为占位示意：

```python
proposals = {"main_0": Path("task/proposals/main_0.lua").read_bytes()}
result = decompile_chunk(original, proposals=proposals, naming={})
cert = certify_l3(original, result.source)
```

通道只替换拒绝站点，自动已经认证的部分优先；wrapper 自身通过不够，必须在真实父作用域内重编译整个 chunk，零排除地认证。通道失败可能返回原有 hybrid/fallback，所以仅“调用没报错”不能说明提案已被采用。检查 `shipped_proposal` 与整树结果。它不是任意替换器：根函数修复、全部已认证但想改写、或当前通道拼接受限时，直接认证整份手写候选。新任务显式传入自己的映射，不修改历史 `MANIFEST`。

若代码语义正确但暂时无法编译回相同的指令布局，应保留动态证据和 L1 结论，记录阻塞原因。不要为了追求 L3 将 `maxstacksize`、NEWTABLE 参数、常量或指令随意从比较器中屏蔽。新增归一化是独立验证工程，需要明确观察模型、健全性论证、反例测试和阶梯版本更新。

## 6. 交接包与可直接复制的 agent 提示词

选择能阅读 Lua 5.1 VM C 源码、分析控制流/寄存器/闭包、运行本仓库工具并迭代修复的强推理 coding agent；能力通过最小问题上的实际认证结果评估。模型名称会变化，不将某个型号写成验收标准。这里是交接模板，不会自动启动或向其他 agent 发送任务。

建议每个独立任务保存：

```text
task/
  HANDOFF.md              # 目标、命令、进展、下一步、未解决问题
  manifest.json           # 输入/输出/oracle 哈希、仓库 commit、环境、阶梯版本
  original/               # 只读字节码原件
  baseline/               # 自动生成源码 + 初始 report.json
  candidate/              # 当前待认证源码
  proposals/              # 可选的函数级 wrapper
  evidence/               # listing、失配路径、差分 trace、执行日志、覆盖范围
  tests/                  # 目标 API stubs、确定性输入、最小回归
```

可复制的提示词（填写方括号，不需要附带原游戏背景）：

> 任务：将 [输入文件/清单] 反编译为可维护的 Lua 5.1 源码。仓库位置 [路径]，基线 commit [SHA]，环境与复现命令见 [manifest/HANDOFF 路径]。原件 SHA-256 为 [哈希]。输入来自 [VM 版本/平台/ABI]，业务 API 与副作用约定见 [文档]。
>
> 先读 `docs/runbooks/general-lua-starter-guide.md`，再复现 baseline；当前整树结果 [L3.0/L3.1/L1/编译失败]，fallback 路径 [列表]，首个失配 [proto/field/pc]，已尝试方法和失败原因 [列表]。独立任务使用 `load_file` + `decompile_chunk`，不要加载历史文件名清单。
>
> 优先修最小失败函数，可修复可泛化的重建器缺陷，也可手写候选或提供 proposal。依据原字节码与 `vendor/lua-5.1/src/lvm.c` 的语义推导，不凭常见代码风格猜测。保持字节常量、求值顺序、元方法、副作用、闭包和多返回值语义。
>
> 目标：在现有未放宽的认证阶梯上，让最终写盘源码对原始整棵 proto 达到 L3.0；无法保留 debug 信息时争取 L3.1，并列出其观察边界。不得删测试、改 golden/pins、屏蔽失配字段、替换原件或仅凭相似度/少量 stdout 宣称等价。不得将未覆盖 fallback 说成已完成认证。
>
> 验证：先显式重编译，后认证实际交付字节；在新的 Python 进程复验，记录源码与 oracle 哈希、阶梯版本、退出码。跑相关回归与基础整套测试，准确报告 skipped。动态验证使用 [真实环境/明确的 stubs]，覆盖 [关键输入]，保存首个差异与未覆盖范围。
>
> 完成条件：交付可读源码、可复现报告、必要的最小回归、代码提交及剩余问题。若整树 L3 暂不可达，交付最佳已验证版本、每个残留 proto 的具体原因、已证实与未证实的边界、下一步可执行方案。形式化证明需求超出现有 L3 时，先提交证明目标与可信基础方案，不宣称仓库已经提供证明助手级保证。

若还需要更强的形式化保证，交接目标应进一步明确：形式化哪一个 Lua VM、允许哪些环境/元方法/debug 观察、如何表示 heap/closure/异常/非终止，以及源程序和 bytecode 状态间的模拟关系。有限输入 SMT 检查或有界模型检查需写明边界；完整证明则需独立机器可检查的证明工件及其检查命令。预算不足或证明未完成时，保留可复现的 L3 产物作为工程成果，并将形式化部分标为未完成。

## 7. 最终交付检查

- 原件、候选、重编译结果及报告哈希对应；所有润色后重新认证。
- 每个文件编译状态、整树级别、rung、fallback/proposal 和失败原因可查。
- 可读性单独审阅：正常控制流、合理作用域、命名有依据；不以减少行数损害语义。
- 基础测试与目标任务动态测试均记录命令、结果、skip 和覆盖限制。
- 报告区分整树认证、局部认证、动态观测和未证明假设；原语料的成功率不外推到新任务。
