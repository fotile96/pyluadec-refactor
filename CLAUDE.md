# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

本仓库是 **pyluadec（`/root/pyluadec`，Lua 5.1 字节码反编译器）的从头重构**。原项目诞生于 PSP 视觉小说《セカンドノベル》的中文本地化工程（`/root/Zndnovel`）：本地化仓库中的 229 个 lua 剧本（`/root/Zndnovel/lua_scripts`）正是原反编译器的产物（经 `/root/pyluadec/post_process/stage3_input` 链路）。该产物已满足本地化需求；本仓库的目标不是修补原项目，而是以其为参照，重新设计并实现一个工程质量合格的反编译器。

### 重构目标

1. **架构灵活性**：原项目只能在 32 位环境跑（依赖 in-process 加载 32 位 bytecode）。重构后必须能在 64 位开发环境处理这批 32 位 bytecode（即字节码解析对 `sizeof(size_t)`/字长做参数化，而非依赖宿主 ABI）。兼容 Lua 5.2+ 是 stretch goal，不强求（VM 指令集有明显改动）。
2. **精巧的 pipeline + 插件机制**：原项目大量 ad-hoc 特例直接堆进关键函数（见下"工程债"）。重构中，不得不做的特例处理应实现为可注册（register）到基础 pipeline 上的 plugin/pass，而不是拉长核心函数的特殊规则。
3. **语义验证**：设计系统化方案验证反编译产物正确还原了原始 bytecode 语义（原项目重度依赖人工 subagent 审查 + 放回游戏引擎实跑）。原项目已有可继承的思路：重编译后 proto 结构对比、差分执行（stub 环境下同按键序列驱动、diff stdout/trace）。
4. **验收基线**：至少通过原项目已有的全部 testcase 与回归测试（语义类测试直接沿用；文本断言类测试沿用其*意图*，见下）。

### 开发方式

使用 superpowers skill set（brainstorming → writing-plans → TDD → code review），沉淀设计文档与操作文档——原项目正是因为缺这些才选择重开仓库。

## 运行环境

- WSL2（64 位内核）+ **32 位 i686 Gentoo userland**：`uname -m` 报 x86_64，但 `/bin/ls` 等全是 ELF 32-bit，Python `struct.calcsize('P')` = 4 字节。这是原项目为省去重新声明 Lua C 数据结构而选的环境；重构目标之一就是摆脱这个限制。
- 系统 Python 3.13.1（32 位）、CMake 3.30.6、GCC 14.2.1。
- 原项目通过 pybind11 包装 vanilla Lua 5.1（改用 CMake 构建），让 Python 直接操作 C 层数据结构——这个思路如有价值可保留，但不能再是*唯一*的 bytecode 读取路径。

## 目标 bytecode 的关键事实

- 来源：PSP（MIPS32）游戏，Lua 5.1 luac 输出。全量语料在 `/root/pyluadec/others/script_to_decompile/`（229 个文件，扩展名 .lua 但都是字节码；最大的是 124 KB 的 `snr_common.lua`）。
- 头部 12 字节：`1b 4c 75 61 51 00 01 04 04 04 08 00` —— `sizeof(int)=4, sizeof(size_t)=4, sizeof(Instruction)=4, sizeof(lua_Number)=8, is_integral=0`。
- **注意**：原项目 `init_prompt.txt` 声称目标是"32 位字长定点数 lua"——**这是错的**，实际是普通 IEEE double；32 位性只体现在 `sizeof(size_t)=4`。原项目的 lua-5.1 源码是**未打补丁的 vanilla 5.1.5**（仅加了 CMakeLists），内部结构靠 include 内部头（`lobject.h` 等）暴露。
- **语料是 strip 过的**（2026-08-10 实测确认）：229 个文件 / 1944 个 proto，`lineinfo`、`locvars`、upvalue 名称**全部为空**，`source` 是占位符 `=?`；旧 `luac -l -l` 列表里每条指令都是 `[-]`。因此**不存在**"用 debug 段做语句边界/变量名 oracle"这条捷径——所有局部变量名必须合成，语句边界必须从控制流与寄存器生命周期推导。新 bridge 的 debug 字段导出能力本身正常（对新编译的文件能正确导出 locvars），只是这批语料没有。
- **但 `linedefined`/`lastlinedefined` 幸存**：它们属于 `DumpFunction` 主体而非 debug 段，1944 个 proto 中 1715 个非零（为零的 229 个正是各文件的 main chunk）。即每个函数在**原始源码**中的起止行仍然已知，可用于函数排布/嵌套的合理性校验，只是没有语句级粒度。

## 原项目（/root/pyluadec）架构速览

管线：`pipeline.py:44-48` 五步 `enhance_proto → decode_proto → build_cfg → structure_proto → _emit`，模式 `legacy | ir_debug | ir_lua | ir_lua_fidelity`（实用的是最后者）。

- **native bridge**（`native_bridge/proto_extractor.cpp`，165 行 pybind11）：`load_proto(file)` / `load_from_source(code)` / `decode_instruction(word)`，全部返回 plain dict。**缺失**：`maxstacksize`、`lineinfo`、`locvars`、`source`、`nups`、完整 vararg flags；数字常量一律转 float；非 UTF-8 字符串会抛异常。下游一大堆复杂度（upvalue 数量猜测 `structure.py:12`、合成变量名 v0/v1、float 格式化 hack）都是在补偿这些缺失。
- **IR**（`ir.py`）：只是指令流的 1:1 typed 镜像，**没有表达式/语句级 IR**——表达式直接在 emitter 里以 Python 字符串拼接（`EmitState.reg_exprs`: 寄存器 → Lua 源码片段字符串）。
- **CFG**（`analysis_ir.py`）：构建了但**结构化阶段完全没用**（`structure.py:1434` `_ = cfg`），只用于统计 block 数。
- **结构化**（`structure.py`，1448 行）：`_parse_block` 是**单个 1039 行函数**（66 个 if、嵌套深度 9），对线性 PC 区间做 ~14 种硬编码字节码 idiom 的级联匹配（while/repeat/break 变体、"shared fallback"家族 4 个近似重复、OR/AND 链……）。无支配树、无区间分析、不支持 repeat/goto。死循环保护静默退化为平铺指令。
- **发射**（`emitter_structured_lua.py`，**3712 行、124 个方法**）：字符串化发射后，用两层正则/文本重写做清理——emission 期 peephole（`_append_with_peephole` 一族）+ `_postprocess_lines` 固定点循环（魔法迭代次数 3×3，12 个文本 rewriter）。为此还要**重新解析自己刚发出的文本**（数 `do/then/end`、数缩进找块边界）。
- 死代码/历史层：`codegen.py`（legacy 后端）、`control_flow.py` 的 `ControlFlowBuilder`（死，调用即 AttributeError）、`proto_extractor.py`（死 enhancer）、`test.py`（stale）。`emitter_structured_lua.py` + `structure.py` 占全部 Python 的 53%。
- 参考资料：`others/a-no-frills-introduction-to-lua-5.1-vm-instructions.pdf` 是指令语义首选参考，**与官方文档冲突时以 PDF 为准**（原作者验证过官方文档多处语焉不详）。

## 验收基线与测试资产

原项目测试均为 unittest，需先构建并 `export PYTHONPATH=/root/pyluadec/cmake-build-debug/native_bridge:/root/pyluadec`（32 位环境下）：

```bash
cd /root/pyluadec
cmake -S . -B cmake-build-debug
cmake --build cmake-build-debug --target lua luac lua51_proto_extractor
```

可直接沿用为重构验收标准的（语义/结构类，与输出格式无关）：

- `pyluadec/test_semantic_regressions.py`（5 例）：反编译 → 用仓库内 `lua` 实跑 → diff stdout。
- `pyluadec/test_generated_semantic_cases.py`：程序化生成 Lua 用例做差分执行（`PYLUADEC_GENERATED_CASE_LIMIT=N` 限流）。
- `pyluadec/test_ir_structure_roundtrip.py`（6 例）：产物重编译后对比 opcode 计数 / proto shape / CFG shape。
- 229 文件全语料 + 批量评估器：`corpus_eval.py`（TODO/WARN/unknown-reg 计数）、`semantic_eval.py`（proto 语义指纹相似度打分，CLI-only）。
- `blackbox_runtime.py`：差分执行 harness（metatable proxy 自动 stub 未知全局、按名字猜 stub 返回值、录 call trace、步数上限）——in-tree 大部分未接线，但正是重构目标 3 想要的原型。
- `pyluadec/DEBUG_KEY_SEQUENCE_HARNESS.md`：按键序列差分调试playbook，含两个具体历史 bug 检查点（`SystemOption.OptionMain` 双 clamp 互斥；`SystemConfig.ConfigMain` CIRCLE 分支的 gate/wait 保持），可转为回归用例。

**慎用**：`pyluadec/test_ir_pipeline.py`（86 例，1294 行）62% 断言是对旧 emitter 输出文本的子串匹配，换实现必然大面积挂。把它当作**已知难还原字节码形态的目录**，逐条以语义等价方式重新表达，而不是照抄断言。

## 下游耦合（改 emitter 输出格式前必读）

`post_process/` 工具链（stage1 重命名 → translation_ir → stage2 锚点 → stage3 overlay → luac 重编译）用**行锚定正则**匹配 emitter 的确切输出风格：`v\d+` 命名、每行一条语句、顶层无缩进、`name = function(...)` 形式（而非 `function name(...)`）、双引号字符串。`rename_semantic_locals.py` 还用 `load_from_source` 做改名前后 proto 结构等价校验。Zndnovel 侧已冻结在 stage3 产物上，重构**不必**字节级复刻旧输出；但若要重新打通全链路，要么保持这个文本表面，要么显式版本化并改造 post_process 的匹配层。

## 本仓库现状

Phase 1（M0）已完成：uv 骨架、vendored pristine Lua 5.1.5、序列化宽度补丁（`native/patches/0001-serial-sizet.patch`）、双宽度构建（sz4/sz8）、两条 pybind bridge、header-dispatched `pyluadec.ingest`、只读 golden baseline（`corpus/golden/`）、roundtrip 与 golden-parity 两道校验门，均已跑通并在当前 32 位环境全绿。常用命令：

- 装依赖：`uv sync`
- 构建原生产物（vendored lua/luac 的 sz4/sz8 变体 + 两个 pybind bridge `.so`，产出到 `build/` 与 `src/pyluadec/_native/`）：`./scripts/build_native.sh`
- 跑全部测试（文档化的默认调用方式——务必带上语料环境变量）：
  `PYLUADEC_CORPUS_DIR=/path/to/script_to_decompile uv run pytest`（或加 `-v`）。
  **不带这个环境变量的 `uv run pytest` 不是"全部测试"**：13 个语料门控用例会被
  静默 `pytest.skip`（而不是报错中断），其中包括 M2 出口门
  `test_corpus_compile.py`、golden/parity 两道门、以及台账不动点测试
  `test_ledger_ratchet.py`——裸跑仍会打印形如 "107 passed" 的绿色结果，但这不
  代表这些门跑过了。`tests/conftest.py` 装了一个 `pytest_terminal_summary`
  钩子，语料目录缺失时会在测试结束后打印醒目的警告横幅，提醒你这一点；但**不会**
  让裸跑本身失败——语料门控用 skip 而非 error 是有意为之（本地/CI 环境不一定都
  能拿到 229 个语料文件），这条 CLAUDE.md 记录只是把"文档化默认值"和"裸跑的真实
  后果"讲清楚，不改变这个行为。
- 跑单个测试：`uv run pytest tests/test_x.py::test_y -v`
- 一键迁移验证（三道门 + 全量测试，spec §6 Step 2；32 位与 64 位环境均可跑，64 位跑绿是 M1 出口）：`./scripts/verify_migration.sh`
- 语料位置约定：语料从不硬编码进代码，一律经环境变量 `PYLUADEC_CORPUS_DIR` 获取（指向 229 个 `.lua` 字节码文件所在目录，参照原项目的 `/root/pyluadec/others/script_to_decompile/`）。未设置或目录不存在时，依赖语料的 pytest 用例会 `pytest.skip`（见 `tests/conftest.py` 的 `corpus_dir` fixture），不会报错中断其余测试。

64 位新机开荒（Linux x86_64 / macOS arm64）的完整步骤、双平台验收要求、门失败时的排查方法，见 `docs/runbooks/64bit-migration.md`。

Phase 2（M2：fallback closed loop）已完成，收口于 `docs/runbooks/decompile-pipeline.md`（全文档，含逐层模块说明、fallback 产物阅读指南、台账字段语义）——本节只给定位与速查，细节一律以该 runbook 为准，不在此重复。

### 管线模块布局

```
ingest -> lift -> cfg -> structure.fallback -> oracle 编译验证 -> ledger
```

- `pyluadec.ingest`：`load_file`/`load_bytes` → `Proto`（Phase 1 已交付，header-dispatched sz4/sz8）。
- `pyluadec.lift`（新增）：`opcodes.py`（解码器 + `OP_SPECS`，golden listing 全语料核对）、`effects.py`（38 opcode 效应表，公理层，STRICT/NO_METAMETHOD/TRUSTING 三档——**只有 STRICT 有论证依据，标定档位属 M4**）、`lift.py`（`lift_proto` → LIR，pc 认领审计覆盖全语料 1944 proto）。
- `pyluadec.cfg`（新增）：`blocks.py`（`build_cfg`）、`dom.py`（`immediate_dominators`，CHK 算法，对不可归约图安全）——CFG 在 M2 被 `structure.fallback` 实际消费，不是原项目那种建而不用的摆设。
- `pyluadec.structure.fallback`（新增）：`emit_chunk(root) -> bytes`，pc 派发状态机，38/38 opcode 全覆盖。这是 M2 的地板（floor）：语义精确、故意丑，**M3 起由结构化识别（if/while/for 还原）逐步替换**，fallback 本身不会去美化。
- `pyluadec.verify`（新增）：`normalize.py`（L3.0 严格比对器 + 空的归一化阶梯骨架 `NORMALIZATIONS`/`LADDER_VERSION`）、`ledger.py`（`structural_hash`、`LedgerEntry`、`write_ledger`/`read_ledger`）。
- `pyluadec.pipeline`（新增）：`walk_proto_paths`、`decompile_chunk`、`decompile_file` —— 驱动整条管线的入口。
- `pyluadec.oracle`（新增）：包装 `build/luac_sz4`/`build/lua_sz4`，`compile_source`/`run_bytes`，供编译验证与差分执行使用。

### 新增常用命令

- 全语料编译门 + 台账重生成：`PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py`（产出 `build/decompiled/*.lua`——不入库；重写 `corpus/ledger.jsonl`——入库）。干净跑法应打印 `compiled 229/229`。
- 台账面板：`uv run python scripts/ledger_dashboard.py [--markdown]`（只读，从不写台账）。
- 单文件反编译、差分执行调试单个用例（`tests/diffexec.assert_fallback_roundtrip`）：命令与用法见 runbook「常用操作」节。

### 台账约定（ratchet 纪律）

- `corpus/ledger.jsonl` **入库**（1478 条唯一 proto 结构哈希、覆盖 1944 处出现、229 文件，M2 收口时全部 `L1`）；`corpus/discrepancies.json` **不入库**（gitignored，纯门产物，"最近一次验证干净"的可追溯性应落在 CI 或本文件而非该 JSON——Phase 1 遗留的正式决定）。
- 台账只能由 `scripts/run_corpus.py` 整体重新生成后提交，**禁止手编**任何一行。
- 台账是自身生成脚本的不动点（同语料、同 oracle 构建再跑一次必须字节级复现），由 `tests/test_ledger_ratchet.py` 守护；等级只升不降，禁止出现 `L0`。
- `oracle` 字段记录的是 `git log -1 -- vendor native`（oracle 构建产物的溯源），**不是** `git rev-parse HEAD`——用 HEAD 会导致每次纯文档/纯测试提交都让全部台账行看起来"变了"，淹没真实回归；原因与修复过程见 runbook 对应小节。

详见 `docs/runbooks/decompile-pipeline.md`：管线每层的函数签名、fallback 产物的 `__pld_R`/`__pld_U`/盒模型/`__pld_pc` 状态机阅读指南（含与 `luac_sz4 -l -l` 原始 listing 对照调试的实操示例）、效应表三档的语义与限度、台账字段的完整语义。

## Phase 3（M3：structured backbone）现状

Phase 3 已完成，收口于 `docs/runbooks/structured-pipeline.md`（全文档：逐层模块、认证门不变式、归一化阶梯与其健全性论证、freereg 寄存器模型、能力边界实测、日常命令）——本节只给定位与速查，细节一律以该 runbook 为准，不在此重复。M2 的 fallback 路径**没有被废弃**，它仍是地板，细节继续以 `decompile-pipeline.md` 为准。

### 新增模块布局（接在 M2 之后）

```
ingest -> lift -> cfg -> sir.build -> express.reconstruct -> emit.lua
                                   -> verify.certify(L3) -> structure.structured -> pipeline -> ledger
```

- `pyluadec.sir`（新增）：`regions.py`（冻结区域节点 + `all_claimed`）、`build.py`（`build_sir(fn) -> Region`、`has_back_edge`、`StructureError`）。支配树在此被**真正消费**（`_verify_single_entry` 用 `immediate_dominators` 校验分支/循环体单入口），不是建而不用。纪律：**识别或 `StructureError`，绝不猜结构**；每次 `build_sir` 出口强制 pc 认领审计 `all_claimed(region) == set(fn.instrs)`。
- `pyluadec.express`（新增）：`expr.py`（表达式节点）、`names.py`（`classify_registers` / `name_for`）、`reconstruct.py`（`Reconstructor`：`stmts_for` / `take_expr` / `cond_operand` / `open_scope`+`close_scope`）。**M3 task 8 删除了 `_adjacent_pure` 与 `EffectMode` 旋钮**，改为模拟 `lparser.c` 的 `freereg = nactvar` 分配纪律（`_stack_discipline`）——实测：放宽效应屏障 +0.0 个 proto，freereg 模拟 +63.6 个百分点。
- `pyluadec.emit.lua`（新增）：`print_chunk` / `print_function` / `Printer`。**纯结构折叠**：只走一遍类型化的树，绝不回读或后处理自己发出的字符串（无 peephole、无定点循环、无数 `do/then/end`）。`tests/test_engineering_practice.py` 静态禁止 `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` 里出现 `re`。
- `pyluadec.structure.structured`（新增）：`certify_proto(proto, *, is_chunk_root)`、`emit_certified_chunk(root) -> ChunkOutcome`。
- `pyluadec.verify.certify`（新增）：`certify_l3(original, structured_src) -> CertResult`。

### 认证门纪律（最重要的一条）

**产物为结构化 ⟺ root proto 认证 `L3`**（`structure/structured.py:222-226`）；否则发 fallback。永不返回未认证的结构化代码。推论：区域识别、寄存器分类、内联的 bug **只会拉低 L3 比例，不会产出错误代码**。认证是逐 proto 子树独立进行的，所以一个不可结构化的函数不会污染兄弟节点的等级——等级（proof record，逐 proto）与产物（逐 chunk 的保守选择）**刻意解耦**。

归一化阶梯：`L3.0` 严格 + `L3.1 = strip-lineinfo`，`LADDER_VERSION = "l3-ladder-v1"`。**每级的健全性论证必须与该级本体同处一地**（rung 1 的论证在 `verify/normalize.py::_strip_lineinfo` 的 docstring 里，从"剥完之后 `compare_protos` 还比什么"论起）。加 rung 2 时照此办理并 bump `LADDER_VERSION`。

### 新增常用命令

- 全局状态探针（L1.5 门）：`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_global_state.py`。**注意 CLI 不认识那 4 条已钉住的发散**，它会打印 `225/229` 并返回 1；权威判定在 `tests/test_global_state_probe.py`（套件绿即门绿）。
- 效应表-发射器一致性门：`uv run pytest tests/test_effects_emitter_consistency.py`（语料臂 + 合成操作数网格，无需语料也能跑合成臂）。
- 单文件结构化反编译 / 看认证结果 / 调试某个未认证函数：命令见 `structured-pipeline.md`「Common operations」节。

### 台账新字段

- `level`：`L3`（重编译后按阶梯逐字段匹配）/ `L1`（能编译，未验证）；`L0` 禁止出现。
- `l3_level`：通过的归一化级号（`L3` 行非空，当前恒为 `1`）；非 `L3` 行为 `null`。
- `fallback`：布尔，`level != "L3"`。
- `confessions`：`L3` 行必须为空；非 `L3` 行必须恰有一条覆盖全 pc 区间的 `fallback-state-machine` confession。
- ratchet 两半都被断言（`tests/test_m3_exit.py`）：**等级只升不降，confession 只降不升**。

### 能力边界（实测，别当成"差不多都做完了"）

`corpus/ledger.jsonl` 收口值：1112/1478 唯一 proto（75.2%）、1577/1944 处出现（81.1%）达 `L3`；229 个文件里 **92 个**发结构化源码，其余 137 个仍发 fallback。未覆盖的部分：`while`/`repeat`/混合与不可归约回边（162 个唯一 proto 被 `build_sir` 拒绝）、因后代闭包不可结构化而连带失败的祖先（139 个）、打印成功但认证失败的残差（58 个）。M4 议程见 `docs/runbooks/m3-backlog.md`。
