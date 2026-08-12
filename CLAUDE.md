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
- 参考资料：`others/a-no-frills-introduction-to-lua-5.1-vm-instructions.pdf` 是指令语义首选参考，**与官方文档冲突时以 PDF 为准**（原作者验证过官方文档多处语焉不详）。**已知该 PDF 自身有一处勘误**（p. 37，`OP_TESTSET`）：其伪代码、`and`/`or` 操作数映射说明、配套的手算示例三者互相一致且与 `lvm.c` 一致；但紧接着的一句叙述性文字把匹配/不匹配的映射说反了（"If R(B) matches C, the next instruction is skipped, otherwise R(B) is assigned to R(A)..."——应为匹配时赋值并跳转，不匹配时跳过赋值直接落到下一条指令）。以伪代码/`lvm.c`为准，丢弃该句叙述。详见 `docs/runbooks/structured-pipeline.md`（`_match_cond_value` 一节）。

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

**已选定"显式版本化"这条路，产出即 output surface v2（M5 task 7）。** 那条链路其实**早就不兼容**了——我们的合成局部名是 `l<depth>_<reg>`，两个里程碑前就打断了 `v\d+` 锚点。v2 相对 v1 的五处变化（`elseif`、点语法、`-1`、统一 4 空格缩进含函数体、可逆 UTF-8 原样输出）逐条列在 `docs/runbooks/structured-pipeline.md`「Output surface v2」表里，v1 的怪癖一律不保留。每一处都以 `corpus/ledger.jsonl` **逐次提交字节不变**为证据：这就是"呈现层变更"的定义，动了台账的改动即属于走错了范围。

## 工程红线（跨阶段，改代码前必读）

- **字节码派生字符串一律 `bytes`，不解码。** 常量池里的字符串是日文游戏文本，decode 成
  `str` 再流进分析层/比对层/诊断文本，正是原项目 bridge 抛异常的老路。诊断文本（
  `refusal_reason`、confession）**绝不**包含语料内容，只许出现 opcode / pc / 寄存器（见
  `emit/lua.py::_ident` 的 docstring）。
  **2026-08-12 经 human partner 批准的作用域修订，M5 task 7 落地**：

  > 字节红线适用于 ingest/lift/比对层；打印层允许做**有回退的呈现判定**（UTF-8 可逆则原样输出，否则十进制转义）——两种写法编译出相同常量，认证门裁决不变性。

  修订**只落在 `emit/`**，实现是唯一的 `emit/lua.py::_str_lit`：strict UTF-8 解码成功、
  重新编码回原字节、且非纯 ASCII 时原样输出，否则回退到 `structure/fallback.py::str_lit`
  的十进制转义。`structure/fallback.py` 本身未改（fallback 产物仍全转义），
  `ingest`/`lift`/`verify` 一个字节都不解码。不得扩大这个口子。
- **实测更正（2026-08-12）**：语料里**没有**非 UTF-8 字符串常量。229 文件 / 1944 proto /
  49063 个字符串常量，其中 17411 个非 ASCII，非 UTF-8 的 **0** 个。M4 计划文档里
  "frequently non-UTF-8 — the predecessor crashed on exactly this" 的说法**没有复现**；
  CLAUDE.md 记的"非 UTF-8 字符串会抛异常"是对**原项目 bridge**的描述，不是对语料内容的
  断言。因此转义回退路径的证据全部是合成的（`tests/test_emit_readability.py` 里的
  `_LONE_CONT` / `_TRUNCATED`），语料绿说明不了它——参见 MEMORY.md「语料是比它看起来更弱
  的 oracle」。

## 本仓库现状

Phase 1（M0）已完成：uv 骨架、vendored pristine Lua 5.1.5、序列化宽度补丁（`native/patches/0001-serial-sizet.patch`）、双宽度构建（sz4/sz8）、两条 pybind bridge、header-dispatched `pyluadec.ingest`、只读 golden baseline（`corpus/golden/`）、roundtrip 与 golden-parity 两道校验门，均已跑通并在当前 32 位环境全绿。常用命令：

- 装依赖：`uv sync`
- 构建原生产物（vendored lua/luac 的 sz4/sz8 变体 + 两个 pybind bridge `.so`，产出到 `build/` 与 `src/pyluadec/_native/`）：`./scripts/build_native.sh`
- 跑全部测试（文档化的默认调用方式——务必带上语料环境变量）：
  `PYLUADEC_CORPUS_DIR=/path/to/script_to_decompile uv run pytest`（或加 `-v`）。
  **不带这个环境变量的 `uv run pytest` 不是"全部测试"**：语料门控用例会被
  静默 `pytest.skip`（而不是报错中断），其中包括 M2 出口门
  `test_corpus_compile.py`、golden/parity 两道门、台账不动点测试
  `test_ledger_ratchet.py`、以及 L1.5/L1.75 两道探针门——裸跑仍会打印绿色结果，
  但这不代表这些门跑过了（M4 收口实测，2026-08-12：裸跑 `462 passed, 50 skipped`（4.4s），
  带语料 `512 passed`（40.0s）；这个数字随测试增加而变，别把它当常量抄）。`tests/conftest.py` 装了一个 `pytest_terminal_summary`
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
- `pyluadec.lift`（新增）：`opcodes.py`（解码器 + `OP_SPECS`，golden listing 全语料核对）、`effects.py`（38 opcode 效应表，公理层，STRICT/NO_METAMETHOD/TRUSTING 三档；**档位标定已于 M4 task 11 完成**，结论见下文 Phase 4 一节与 `structured-pipeline.md`「The effect lattice」——简言之：`STRICT` 仍是唯一默认且是 `src/` 里唯一被选用的档位，`NO_METAMETHOD` 是允许的逐 pass opt-in 但只限脚本自建的表，`TRUSTING` 不建议任何 pass 使用）、`lift.py`（`lift_proto` → LIR，pc 认领审计覆盖全语料 1944 proto）。
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
- 台账是自身生成脚本的不动点（同语料、同 oracle 构建再跑一次必须字节级复现），由 `tests/test_ledger_ratchet.py` 守护。
- **"等级只升不降"是纪律，不是机器强制的。** 说清楚各自的边界（2026-08-11 逐条核对了断言本体）：
  - **被断言的**：不许出现 `L0`、`compile_ok` 全真、`shash` 有序且唯一、覆盖 229 文件 / 1944 处出现、以及上面那条不动点（`tests/test_ledger_ratchet.py`）；外加**行内**等级与 confession 的耦合（`tests/test_m3_exit.py`，见下文 M3 一节）、M3 出口比例 `> 0.50` 与 M4 出口比例 `> 0.85`（`tests/test_m4_exit.py`，同时钉住分母 `== 1944` 与 `refusal_reason` 的双向耦合）。
  - **没有被断言的**：**跨版本单调性**。没有任何测试拿当前台账去比历史 baseline，所以一份重新生成并提交的、L3 行数变少的台账，只要比例仍 > 50% 且不出现 `L0`，整套测试照样全绿。真正的 ratchet CI（baseline diff、降级即失败、`git bisect` 接线）是 spec §5 的完整形态，M4 结束时**仍未落地，已顺延到 M5**（M4 只是让台账多了 `refusal_reason` 这个能按原因聚类的字段）——见 `docs/runbooks/m3-backlog.md` 的 M5 议程。因此审 PR 时台账的 diff 要人眼看。
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

**产物中的每个 proto，要么正是某次认证实际编译并逐字段比对过的那串字节，要么由语义精确的 fallback 发射并在台账里 confess**（`structure/structured.py::emit_certified_chunk`）。永不返回未认证的结构化代码。推论不变：区域识别、寄存器分类、内联的 bug **只会拉低 L3 比例 / 让更多 proto 落到 fallback，不会产出错误代码**。认证是逐 proto 子树独立进行的，所以一个不可结构化的函数不会污染兄弟节点的等级——等级（proof record，逐 proto）与产物（逐 chunk，自 M5 task 6 起 chunk 内还逐 proto）**刻意解耦**。

M3–M4 的旧说法「产物为结构化 ⟺ root proto 认证 `L3`」是**替换集为空**的特例（229 个文件里 216 个仍是这样）。M5 task 6 加了中间档 **hybrid**：root 未认证时，`certify_hybrid` 把无法认证的 CLOSURE 站点换成 fallback 内联函数（`structure/fallback.py::inline_function_parts`），重新编译后跑**未改动的** `compare_protos`，只丢弃落在被替换子树内部的 mismatch——父 proto 自己的 `code`（含 `CLOSURE` 及其后的 `MOVE`/`GETUPVAL` 伪指令）仍逐字段比。被替换子树本身认证管不了，语义门是两条常驻探针。收口值：216 全结构化 / **6 hybrid** / **7 整文件 fallback**（此前 216/0/13）。细节见 `docs/runbooks/structured-pipeline.md`「Hybrid chunks」。

归一化阶梯：`L3.0` 严格 + `L3.1 = strip-lineinfo`，`LADDER_VERSION = "l3-ladder-v1"`。**每级的健全性论证必须与该级本体同处一地**（rung 1 的论证在 `verify/normalize.py::_strip_lineinfo` 的 docstring 里，从"剥完之后 `compare_protos` 还比什么"论起）。加 rung 2 时照此办理并 bump `LADDER_VERSION`。

### 新增常用命令

- 全局状态探针（L1.5 门）：`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_global_state.py`。M4 task 10 起 CLI 认识那 4 条已钉住的发散（钉子已从测试挪到 `scripts/probe_global_state.py`，两个 CLI 与两个门共用 `scripts/probe_common.py::adjudicate_pins`），干净跑法打印 `225/229 identical, 4 pinned divergence(s)` 并返回 0；权威判定仍在 `tests/test_global_state_probe.py`。
- 行为探针（L1.75 门，M4 task 10 新增）：`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_behaviour.py`。在打桩环境下**实际调用**每个 chunk 定义的全局函数并比对事件轨迹，干净跑法打印 `227/229 identical, 2 pinned divergence(s), 398196 recorded events`。设计、能力边界、两条钉子的指令级证据见 `docs/runbooks/m3-backlog.md`「Behaviour probe (L1.75)」节。
- 效应表-发射器一致性门：`uv run pytest tests/test_effects_emitter_consistency.py`（语料臂 + 合成操作数网格，无需语料也能跑合成臂）。
- 单文件结构化反编译 / 看认证结果 / 调试某个未认证函数：命令见 `structured-pipeline.md`「Common operations」节。

### 台账新字段

- `level`：`L3`（重编译后按阶梯逐字段匹配）/ `L1`（能编译，未验证）；`L0` 禁止出现。
- `l3_level`：通过的归一化级号（`L3` 行非空，当前恒为 `1`）；非 `L3` 行为 `null`。
- `fallback`：布尔。**M5 task 6 改了定义**——现在是"该 proto 形状至少有一处 occurrence 实际发的是 fallback 状态机"，不再是 `level != "L3"`（chunk 非全结构化即全 fallback 时两者等价，hybrid 之后不再等价）。
- `confessions`：`fallback` 为真 ⟺ 恰有一条覆盖全 pc 区间的 `fallback-state-machine` confession，为假 ⟺ 空。
- `occurrences[].shipped`（M5 task 6 新增）：`"structured"` / `"fallback"`，这一处 occurrence 的文本由哪个发射器产出——`fallback` 字段的逐 occurrence 精确形式。
- `occurrences[].hybrid`（M5 task 6 新增）：这处 occurrence 所在的 chunk 是否发的是 hybrid 产物。
- **`level` 与 `shipped` 是两个问题，且已不再一致**：`level` 是该 proto 单独（连同其整棵子树）的证明记录，与邻居怎么发无关；`shipped` 是产物事实。语料上两向都出现：6 行 `L1` 却发结构化（自己的字段被 `certify_hybrid` 精确比对过，只有被替换的后代没有），150 行 `L3` 却发 fallback（它们住在仍整文件回退的 7 个文件里）。
- `refusal_reason`（M4 task 6 新增）：非 `L3` 行**为什么**没认证；`L3` 行为 `null`。
  confession 只说"回退了"，这个字段说"回退的原因"——`build_sir` 拒绝与"打印成功但
  认证失败"以前在台账里长得一模一样。四种 kind：`structure:` / `reconstruct:` /
  `compile:` / `mismatch: <字段名>`，词表与"绝不写入字节码派生字符串"的规矩都记在
  `structure.structured.ProtoCert.reason`。`tests/test_m4_exit.py` 断言双向耦合
  （非 `L3` 必须有、`L3` 必须没有、kind 必须在词表内）。面板
  `scripts/ledger_dashboard.py` 直接打这个字段的直方图，残差普查因此是常驻数据而
  非一次性脚本。
- `tests/test_m3_exit.py` 断言的是**行内耦合**（M5 task 6 按新 schema 重述）：`L3` 行 ⇒ `l3_level` 非空、`refusal_reason is None`；非 `L3` 行 ⇒ `l3_level is None`、`refusal_reason` 非空；并且**对每一行**，`fallback` ⟺ 有那条 `fallback-state-machine` confession ⟺ 有 occurrence 的 `shipped == "fallback"`。也就是说"confession 摘了但产物没变"、"产物变了 confession 没摘"、"行级聚合与逐 occurrence 记录对不上"三种**记账不一致**都会被抓到。旧的 `L3 ⇒ fallback is False` 已随 `fallback` 改定义而作废（那 150 行 `L3` 确实发的是状态机文本，硬要求它们 `confessions == []` 才是真正的 confession 漏洞）。
- **"等级只升不降"本身没有被任何测试断言**——没有历史 baseline 比对，见上文「台账约定」。跨版本单调性是纪律 + 人眼看 diff，机器强制留给 **M5** 的 ratchet CI（M4 未做）。

### 能力边界（实测，别当成"差不多都做完了"）

`corpus/ledger.jsonl` 收口值：1112/1478 唯一 proto（75.2%）、1577/1944 处出现（81.1%）达 `L3`；229 个文件里 **92 个**发结构化源码，其余 137 个仍发 fallback。未覆盖的部分（169 + 139 + 58 = 366 = 1478 − 1112）：`while`/`repeat`/混合与不可归约回边（169 个唯一 proto 被 `build_sir` 拒绝——162 个因为带回边，另 7 个是无环拒绝）、因后代闭包不可结构化而连带失败的祖先（139 个）、打印成功但认证失败的残差（58 个）。M4 议程见 `docs/runbooks/m3-backlog.md`。

**这一段是 M3 收口快照，已被 M4 超越**——当前值见下文 Phase 4 一节。


## Phase 4（M4：loops and verification hardening）现状

Phase 4 已完成。**能力边界与残差普查的权威仍是 `docs/runbooks/structured-pipeline.md`**（「Current capability boundary」节，M4 期间逐任务重测），效应档位的权威是同文件「The effect lattice」节，可读性评估在 `docs/reports/m4-readability.md`，**尚未完成的工作全部在 `docs/runbooks/m3-backlog.md` 末尾的「M5 agenda」**（编号条目，可引用）。本节只给定位与速查。

### 收口数字（2026-08-12 实测于 `3ae72c6`）

- `L3`：**1389/1478 唯一 proto（94.0%）、1855/1944 处出现（95.4%）**（M3 收口为 75.2% / 81.1%）。出口门 `tests/test_m4_exit.py` 的地板是 **0.85**（双基），外加分母 `== 1944` 与 `refusal_reason` 的双向耦合。**地板故意留了 ~9 个百分点余量**：把地板设在实测值上就不是地板而是绊线，而绊线的标准修法是改阈值——那就是门失去意义的过程。
- **229 个文件里 212 个发结构化源码**（M3 为 92），其余 17 个仍发 fallback。
- 测试：**512 passed in 40.0s**（上限 45s）。裸跑（不带语料）`462 passed, 50 skipped`。
- 语料里剩下的 **89 处未认证 proto 全部落在那 17 个文件内**，并且连带拖住了同文件内 **692 处已单独认证 `L3`** 的 proto——`print_chunk` 在每个 `CLOSURE` 处内联整棵树，祖先链上任何一处拒绝就作废上面全部。这是目前最大的一个杠杆（M5 agenda 3）。

### 新增区域类型与识别器

`sir/regions.py` 增加 `While` / `WhileTrue` / `Repeat` / `EndIter` / `CondValue`，识别器在 `sir/build.py`（`_match_while` / `_match_while_true` / `_match_repeat` / `_match_cond_value`）。纪律不变：**识别或 `StructureError`，绝不猜结构**。

**`repeat` 有识别器但这批语料一条都没有**（229 个反编译产物里 `repeat`/`until` 行数为 0，`while` 为 971），所以它的证据完全是合成的——语料全绿对这个节点不构成任何证据。

真正的瓶颈不是循环而是寄存器分类：task 13 把 `RegClass` 从「每个寄存器号一个判决」改成「每个 `(寄存器, 定义点)` 一个判决」，打印成功但认证失败的残差从 283 降到 **35**。

### 新增门（都在默认套件里）

- `tests/test_m4_exit.py`：出口比例 + `refusal_reason` 词表与耦合。
- `tests/test_behaviour_probe.py`（L1.75 行为探针）：**229 文件、227 字节一致、2 条钉住的发散、398196 个事件**。**读它的 reach 分裂再决定信多少**：3000 事件上限截断了 132/229 个文件，这 132 个贡献了 99.5% 的事件，另外 97 个中位数只有 **10** 个事件。
- `tests/test_effects_reconstructor_consistency.py`：把 `lift/effects.py` 与**结构化**路径对账（`reconstruct.py` → `emit/lua.py` 是 `lvm.c` 的第三份独立手抄）。0 违规，靠插桩而不是第四份手抄。它自己的 docstring 记了**它不断言什么**。
- `tests/test_effects_modes.py`：档位标定的普查与钉子，含「`STRICT` 是唯一被 `src/` 选用的档位」这条静态检查。

### 效应档位标定结论（M4 task 11）

`STRICT` 仍是唯一默认；`NO_METAMETHOD` 是允许的逐 pass opt-in，但**只对脚本自建的表成立**（普查在 71414 个常量里找到 0 个元方法相关常量，但语料读取的 164 个全局名里有 56 个从不被写入，来自引擎，普查看不见）；`TRUSTING` 不建议任何 pass 使用（它相对 `NO_METAMETHOD` 只动 3 行，而语料**证伪**了这三行）。`lift/effects.py` 行为未变。两行被判定分级过松、按公理层变更协议留待处理：`LEN` 在 `NO_METAMETHOD` 下应为 `READ_HEAP` 而非 `PURE`（**这是确认的缺陷**，M5 agenda 1）、以及 `NEWTABLE`/`CLOSURE` 的 GC 路径（不建议改）。

### 可读性（与原项目产物对比，`docs/reports/m4-readability.md`）

结构化产物的行数是原项目的 **0.98 倍**（212 个文件全部落在 0.78×–1.03×），`__pld_*` 残留 **0**，212 个文件上 `while`/`break` 的行首计数与原项目**完全相同**（190/190、175/175）。**读得更差的五处（打印器层面）**：非 ASCII 字符串打成十进制转义（这是个日文视觉小说，下游就是翻译——这是最大的一处）、不发 `elseif`（208 个变成嵌套 `if`，最坏 61 层缩进对原项目的 5 层）、字符串键不用点语法（`t["k"]` 对 `t.k`）、函数体不缩进（可能是有意的下游耦合，见「下游耦合」一节）、一元负号打成 `(-1)` 而非 `-1`。外加第六处、结构性的：那 17 个 fallback 文件**按行数占语料的 47.6%**，所以"229 里 212 个"是往好里数的数法。

**这五处打印器层面的差距已由 M5 task 7 全部关闭**（output surface v2，见「下游耦合」与 `docs/runbooks/structured-pipeline.md`）；台账逐次提交字节不变，认证门未做任何放松。第六处（fallback 文件的体量）由 M5 task 6 的 hybrid 发射处理，17 个整文件回退降到 7 个。M4 报告里那个 47.6% 在重测时**没有在任何口径下复现**，别再引用。

### 仍未做（都在 M5 agenda）

完整 ratchet CI（baseline diff、降级即失败）**M4 没做**——M4 只交付了让它能按原因聚类的 `refusal_reason` 字段；`LEN` 重新分级；那 89 处残差；L2 差分执行认证与按键序列 harness；`_stack_discipline`（462 行、33 个 if、11 个内嵌闭包）的拆分。
