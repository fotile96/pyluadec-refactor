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

**已选定"显式版本化"这条路，产出即 output surface v2（M5 task 7）。** 那条链路其实**早就不兼容**了——我们的合成局部名是 `l<depth>_<reg>`，两个里程碑前就打断了 `v\d+` 锚点。v2 相对 v1 的五处变化（`elseif`、点语法、`-1`、统一 4 空格缩进含函数体、可逆 UTF-8 原样输出）逐条列在 `docs/runbooks/structured-pipeline.md`「Output surface v2」表里，v1 的怪癖一律不保留。**M6 task 11 fix round 1 又加了第六项（表里第 7 行）**：同算符的 `and`/`or` 链平铺（`a and b and c` 而非 `a and (b and c)`，`emit/lua.py::_ASSOCIATIVE`）。它在本语料上**惰性**——中和后重生成 229 个 chunk，0 个文件变（2026-08-14 实测），证据全是合成的，已按本里程碑其它窄规则的写法在常量处标注。每一处都以 `corpus/ledger.jsonl` **逐次提交字节不变**为证据：这就是"呈现层变更"的定义，动了台账的改动即属于走错了范围。

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
  （M5 task 7 的审查提过一个小意见：本节比批准的那一条 bullet 写得**长**。M5 task 12
  逐句核对后**保留**——每一句都是那条 bullet 的作用域说明或其实测依据，没有一句扩大了
  授权范围。红线条款宁可写长也不要留下需要读者自行推断的边界。）
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
- **"等级只升不降"自 M5 task 8 起由机器强制，但强制它的不是 pytest 套件。** 边界（2026-08-12 逐条核对）：
  - **套件断言的**：不许出现 `L0`、`compile_ok` 全真、`shash` 有序且唯一、覆盖 229 文件 / 1944 处出现、以及上面那条不动点（`tests/test_ledger_ratchet.py`）；外加**行内**等级与 confession 的耦合（`tests/test_m3_exit.py`，见下文 M3 一节）、M3 出口比例 `> 0.50` 与 M4 出口比例 `> 0.85`（`tests/test_m4_exit.py`，同时钉住分母 `== 1944` 与 `refusal_reason` 的双向耦合）。
  - **跨版本单调性**由 `scripts/ratchet_diff.py OLD NEW` 判定（spec §5 的完整形态）：逐行等级降级、rung 降级（`l3_level` 变**大**＝证明变弱）、行消失、**某个 occurrence 不再被 walk 到（行还在）**、`L3` 行带上 `refusal_reason`、逐 occurrence `shipped` 从 `structured` 退回 `fallback`、逐 occurrence `l2` 授证丢失（`l2-lost`）或覆盖率下降（`l2-coverage-downgrade`，M5 task 9 新增）、新行落在 `L0`——任一即 exit 1，并按 `refusal_reason` 聚类打印涉事行；升级、新增行、**baseline 一侧缺的**字段 exit 0（反方向不对称：新台账**丢**字段不豁免，实测丢 `level` 出 1478 条降级、丢 `l3_level` 出 1430 条 rung 降级）。它**不在**套件里（baseline 是 git ref 不是 fixture），而是 `scripts/ratchet_job.sh` 的第 2 道门（第 1 道全套件、第 3 道 `PYLUADEC_GENERATED_CASE_LIMIT=24` 全量差分执行扫描），在里程碑收口和任何动台账的合并前跑。套件里的 `tests/test_ratchet_diff.py`（43 个用例，不需要语料；task 8 收口时 37，M5 task 9 为 `l2-lost` / `l2-coverage-downgrade` 两种 kind 又加了 6 个）只负责一件事：证明这个工具**能失败**——每种失败模式一个用例，喂手工改坏的真实台账副本并要求非零退出且**点名那一行**。
  - **退出码：0 好、1 有降级、125 =「这棵树没法判」（git bisect skip）、128 =「工具本身配错了」（git bisect abort）。没有 2。** M5 task 8 原版用 2 表示"不是判决"，那是错的：`git-bisect(1)`（本机 git 2.39.5）明说 1..127 里除 125 外**全部**读作 bad，实测一个永远 `exit 2` 的 predicate 会让 bisect 言之凿凿地指认一个无辜 commit。round 1 一并修掉了"未捕获异常逃出 `main()` 变成 exit 1"（同一类：把仪器故障报成树的判决）。
  - **本仓库没有任何 CI runner 配置**（无 `.github/workflows/`，2026-08-12 核实），所以上面这些是"有人去跑"的命令，不是自动触发的。`git bisect run` 的确切写法（含把脚本与 baseline 拷到树外，因为老 commit 上这两样都不存在；以及**判 skip 的依据是"有没有产出台账"而不是 `run_corpus.py` 的退出码**——它在有文件编译失败时会写完带 `L0` 的台账再返回 1，老写法把这种最响的回归当成 skip 跳过了）见 `docs/runbooks/structured-pipeline.md`「The `git bisect run` predicate」，已用注入**编译**回归的临时分支实跑验证过。
- **台账主键 = `structural_hash` 单独一项，这个假设自 M5 task 8 起被每次生成时断言**（`scripts/run_corpus.py::key_disagreements`；违反即拒绝写台账）。实测 2026-08-12：1478 组里 16 组含多于一个 debug fingerprint（共 462 个），**0 组**在 `(level, rung, refusal_reason)` 上分歧。选择"断言"而非"拆键"的理由、拆键会把台账从 1478 行变成 1924 行这个实测值，见 runbook「The ledger's grouping key」。
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
- `pyluadec.express`（新增）：`expr.py`（表达式节点）、`names.py`（`classify_registers` / `name_for`，外加「`for` 头拥有哪些槽、在哪些 pc 上拥有」这半边分析）、`freereg.py`（`stack_discipline`，另半边；**M5 task 11 从 `names.py` 拆出**，拆点就是原有的四个回调，所以是纯文本搬迁——台账逐次提交字节不变）、`reconstruct.py`（`Reconstructor`：`stmts_for` / `take_expr` / `cond_operand` / `open_scope`+`close_scope`）。**M3 task 8 删除了 `_adjacent_pure` 与 `EffectMode` 旋钮**，改为模拟 `lparser.c` 的 `freereg = nactvar` 分配纪律（`freereg.stack_discipline`）——实测：放宽效应屏障 +0.0 个 proto，freereg 模拟 +63.6 个百分点。
- `pyluadec.emit.lua`（新增）：`print_chunk` / `print_function` / `Printer`。**纯结构折叠**：只走一遍类型化的树，绝不回读或后处理自己发出的字符串（无 peephole、无定点循环、无数 `do/then/end`）。`tests/test_engineering_practice.py` 静态禁止 `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` 里出现 `re`。
- `pyluadec.structure.structured`（新增）：`certify_proto(proto, *, is_chunk_root)`、`emit_certified_chunk(root) -> ChunkOutcome`。
- `pyluadec.verify.certify`（新增）：`certify_l3(original, structured_src) -> CertResult`。

### 认证门纪律（最重要的一条）

**产物中的每个 proto，要么正是某次认证实际编译并逐字段比对过的那串字节，要么由语义精确的 fallback 发射并在台账里 confess**（`structure/structured.py::emit_certified_chunk`）。永不返回未认证的结构化代码。推论不变：区域识别、寄存器分类、内联的 bug **只会拉低 L3 比例 / 让更多 proto 落到 fallback，不会产出错误代码**。认证是逐 proto 子树独立进行的，所以一个不可结构化的函数不会污染兄弟节点的等级——等级（proof record，逐 proto）与产物（逐 chunk，自 M5 task 6 起 chunk 内还逐 proto）**刻意解耦**。

M3–M4 的旧说法「产物为结构化 ⟺ root proto 认证 `L3`」是**替换集为空**的特例（229 个文件里 216 个仍是这样）。M5 task 6 加了中间档 **hybrid**：root 未认证时，`certify_hybrid` 把无法认证的 CLOSURE 站点换成 fallback 内联函数（`structure/fallback.py::inline_function_parts`），重新编译后跑**未改动的** `compare_protos`，只丢弃落在被替换子树内部的 mismatch——父 proto 自己的 `code`（含 `CLOSURE` 及其后的 `MOVE`/`GETUPVAL` 伪指令）仍逐字段比。被替换子树本身认证管不了，语义门是两条常驻探针。收口值：216 全结构化 / **6 hybrid** / **7 整文件 fallback**（此前 216/0/13）。细节见 `docs/runbooks/structured-pipeline.md`「Hybrid chunks」。

归一化阶梯：`L3.0` 严格 + `L3.1 = strip-lineinfo`，`LADDER_VERSION = "l3-ladder-v1"`。**每级的健全性论证必须与该级本体同处一地**（rung 1 的论证在 `verify/normalize.py::_strip_lineinfo` 的 docstring 里，从"剥完之后 `compare_protos` 还比什么"论起）。加 rung 2 时照此办理并 bump `LADDER_VERSION`。

### 新增常用命令

- 全局状态探针（L1.5 门）：`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_global_state.py`。M4 task 10 起 CLI 认识那 4 条已钉住的发散（钉子已从测试挪到 `scripts/probe_global_state.py`，两个 CLI 与两个门共用 `scripts/probe_common.py::adjudicate_pins`），干净跑法打印 `228/229 identical, 1 pinned divergence(s)` 并返回 0（M6 task 12 让其中三条钉子**收敛**，因此被删除——`adjudicate_pins` 把收敛的钉子报成 `gone` 并让门失败，删除是被强制的不是选的；2026-08-14 实跑复核）；权威判定仍在 `tests/test_global_state_probe.py`。
- **L2 差分执行门（M5 task 9 新增）**：`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_keyseq.py`。
  原始字节码与产出源码在同一 stub 环境、同一**按键序列**下跑，**七个**条件全过才授 `L2`：
  trace 在**探针观测到的范围内**逐字节相同、序列确实被轮询、无运行期 taint 标记、**静态回退
  分析找不到任何「stub 派生值决定了一个没人看见的分支」的位置**、探针没有自身故障、
  **至少有一条序列跑到了自然结束**（不是撞 `MAX_EVENTS=3000` 被截断）、且 **chunk 里每个
  proto 都是 `L3`**。后两条是**最终修复轮**补的，两条都是已经发货的洞：
  (a) `evaluate` 从来没读过 trace 的 `header`，所以两边都撞上限时「逐字节相同」实际只是
  「前 3000 个事件相同」，而这一点在判决、detail、台账里**一处都没记**——合成反例
  `for i=1,5000 do engine.Go(i) end engine.OriginalTail()` 对
  `... engine.COMPLETELY_DIFFERENT_TAIL()` 双方 `CAP|3001`、逐字节相同、零 taint、
  `granted=True, cov=1.0`。刻意是**「至少一条」而不是「每条都要」**：退化序列根本不停机
  （把上限调大 1000 倍实测，`snr_lib.lua` 的 `tail=CIRCLE` 报 `CAP|3000001`），五个文件各有一条，
  「每条都要」会把 reach 永久打到 0。**这条只是把洞收窄，没有堵上**：被截断的 run 不再能
  单独支撑一个**文件**的授证，但仍能单独支撑一个**没有任何完成序列进入过的分支**——把
  `tail=` 走 `else` 臂、把有分歧的尾巴放在 `k=1,CIRCLE` 后面，门就会以 `cov` 1.0 授证，因为
  两条 spec 进入的 proto 集合**相同**，proto 粒度看不见分支。已作为**已知开放路径**入库
  （`tests/test_l2_keyseq.py::test_a_branch_only_a_capped_sequence_enters_is_granted_on_a_truncated_prefix`，
  断言的是**当前会授证**这个事实），并路由到 M6 agenda 2。唯一那个现存授证不是站在这上面，
  这是实测不是论证：`snr_lib.lua` 的 `tail=CIRCLE` 用 10 倍预算重跑、把十进制 token 归一化后，
  **3000 个事件时有 15 种不同事件形状，30000 个事件时还是同样的 15 种，一个新的都没有**。
  **门并不检查这一点**，换一条序列就得重新测。
  (b) 静态回退分析只读**原始**字节码，所以它只在产物与原始逐字段相同时才代表产物——
  形状实测会分叉：`snr_music.lua` 原始 taint 是 `{compare 36, length 1, launder 1, loop 3,
  truthiness 2}`，其发货的 fallback 文本是 `{compare 3, loop 16}`，`__pld_R` 盒模型**藏了** 33 个
  比较点、**凭空造出** 13 个。所以现在的 L2 **只认证逐字段相同的产物**；要扩到 hybrid/fallback
  是 M6 的活，且必须去分析产物本身，而不是放松这条。两条的实测代价都是**零**：reach 前后都是
  1/5（`snr_lib.lua`，其两条完成序列单独给出的覆盖率与三条全跑完全一致），`corpus/ledger.jsonl`
  字节不变。徽章 `cov` 是**完成的**那些 run 进入的
  产物 proto 比例（不是基本块——基本块归属只能靠行号，会随排版移动，
  实测同一程序 16 个块「铺开 0.9375 / 压紧 1.0」，那会打破 CLAUDE.md 对「呈现层变更＝
  台账字节不变」的定义）。干净跑法打印 `L2: 1/5 authored file(s) granted, 4 refused as expected`
  并返回 0。
  **reach 是 1 个文件（snr_lib.lua，L2@100%，台账里 2 行 / 3 处 occurrence），这是实测**：
  语料里只有 9 个文件含 `pressButton`、5 个真的走到轮询、其余 4 个在到达前就报错；
  而这 5 个里有 4 个存在「stub 值与常量比较」这种运行期**看不见**的分支决定
  （`lvm.c::equalobj` 先比类型再谈 `__eq`，所以 `stub == "字面量"` 一个元方法都不触发），
  被静态回退分析整文件拒授。**这个分析连续三轮被评审在「上一轮修复代码本身」里找到新的
  不健全路径**（round 0 十二条、round 2 四条、round 3 八条、round 4 六条，每条都是双方 trace
  逐字节相同、0 个运行期标记、却授证；四轮下来 reach 始终是 1/5——每次修的都是构造出来的
  fixture，没有一次是语料文件），所以 runbook 里「还看不见什么」那份清单只当作*我能构造出来的
  残余*，不是存在性证明。也因此这个分析必须**健全**而不是尽力而为：`l2` 是**入库**字段
  （当前 2 行 `{"cov": 1.0}`、164 处 `{"refused": "taint-static"}`），一次错误授证会写进
  `corpus/ledger.jsonl` 并成为后续 ratchet 的基线。该分析**不做**「chunk 自己定义的全局就不是 stub」豁免——
  `env.__index` 只在写**真的执行过**之后才从 `envfields` 取值，所以「写在读之后」「写所在
  函数没被调用」「把 stub 存进全局再比较」三种形态都能骗过那条豁免；实测删掉豁免不损失
  任何 reach）。132 个撞上限的文件里 101 个是 `vms` 主导、26 个 `wait` 主导、
  5 个 `pressButton` 主导。设计、语法、taint 的「可证/保守/仍看不见」三分、覆盖率口径与
  两处 backstop 见 `docs/runbooks/structured-pipeline.md`「The L2 gate」。
- 行为探针（L1.75 门，M4 task 10 新增）：`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_behaviour.py`。在打桩环境下**实际调用**每个 chunk 定义的全局函数并比对事件轨迹，干净跑法打印 `behaviour: 228/229 identical, 1 pinned divergence(s), 398196 recorded events on the original side`（2026-08-14 实跑：M6 task 12 让 `snr_mainmenu.lua` 收敛，钉子从 2 降到 1；事件总数 398196 未变）。**钉子的键是两条完整轨迹的 SHA-256**（M6 收口评审改，此前是「首个差异行」，实测那个键能吸收一处无关缺陷——见 `scripts/probe_behaviour.py::pin_evidence`）。设计、能力边界、钉子的指令级证据见 `docs/runbooks/m3-backlog.md`「Behaviour probe (L1.75)」节。
- 效应表-发射器一致性门：`uv run pytest tests/test_effects_emitter_consistency.py`（语料臂 + 合成操作数网格，无需语料也能跑合成臂）。
- **Ratchet 门（M5 task 8）**：`PYLUADEC_CORPUS_DIR=... ./scripts/ratchet_job.sh [BASELINE_REF]`——全套件 + 台账 baseline diff + 24 例全量差分执行扫描，**实测 57.9–58.2s（2026-08-14，M6 收口树，1077 个用例，两次）**，`BASELINE_REF` 默认 **`0957364`**（M5 合并点 = 上一个里程碑合并点；M6 task 13 把默认值从 `eb08890` 前移，那行注释本来就写着「最近一个已合并的里程碑」）。只要 diff：`git show <ref>:corpus/ledger.jsonl > /tmp/base.jsonl && uv run python scripts/ratchet_diff.py /tmp/base.jsonl corpus/ledger.jsonl`。
- 单文件结构化反编译 / 看认证结果 / 调试某个未认证函数：命令见 `structured-pipeline.md`「Common operations」节。

### 台账新字段

- `level`：`L3`（重编译后按阶梯逐字段匹配）/ `L1`（能编译，未验证）；`L0` 禁止出现。
- `l3_level`：通过的归一化级号（`L3` 行非空，当前恒为 `1`）；非 `L3` 行为 `null`。
- `fallback`：布尔。**M5 task 6 改了定义**——现在是"该 proto 形状至少有一处 occurrence 实际发的是 fallback 状态机"，不再是 `level != "L3"`（chunk 非全结构化即全 fallback 时两者等价，hybrid 之后不再等价）。
- `confessions`：`fallback` 为真 ⟺ 恰有一条覆盖全 pc 区间的 `fallback-state-machine` confession，为假 ⟺ 空。
- `occurrences[].shipped`（M5 task 6 新增）：`"structured"` / `"fallback"`，这一处 occurrence 的文本由哪个发射器产出——`fallback` 字段的逐 occurrence 精确形式。
- `occurrences[].hybrid`（M5 task 6 新增）：这处 occurrence 所在的 chunk 是否发的是 hybrid 产物。
- **`level` 与 `shipped` 是两个问题，且已不再一致**：`level` 是该 proto 单独（连同其整棵子树）的证明记录，与邻居怎么发无关；`shipped` 是产物事实。语料上两向都出现：6 行 `L1` 却发结构化（自己的字段被 `certify_hybrid` 精确比对过，只有被替换的后代没有），150 行 `L3` 却发 fallback（它们住在仍整文件回退的 7 个文件里）。
- `occurrences[].l2` / `l2`（M5 task 9 新增）：前者是逐 occurrence 的**逐文件**事实——
  `{"cov": 0.xx}` 授证、`{"refused": <kind>}` 有序列但被拒、`null` 没有序列；后者是行级
  聚合（`verify/ledger.py::row_l2`），**每一处** occurrence 都授证才授，取最小 cov。
  `l2` **没有**并进 `key_disagreements` 的 verdict：那条 pin 管的是
  `(level, rung, refusal_reason)`（`_memo_key` 声称是 `(shash, dfp)` 的函数），而 `l2`
  跟 `compile_ok`/`hybrid` 一样是**文件**属性——实测 1478 个 shape 里 13 个跨多文件、
  最多跨 27 个，其中 **2 个**同时落在「有按键序列」与「没有按键序列」的文件上，台账里
  正好 **2 行**的 occurrence 在 `l2` 上不一致。把它并进去只会制造假分歧并逼出一次
  没有健全性内容的拆键（拆键也解决不了：`l2` 随**文件**变，不随 debug fingerprint 变）。
  `key_disagreements` 一字未动。
- `refusal_reason`（M4 task 6 新增）：非 `L3` 行**为什么**没认证；`L3` 行为 `null`。
  confession 只说"回退了"，这个字段说"回退的原因"——`build_sir` 拒绝与"打印成功但
  认证失败"以前在台账里长得一模一样。四种 kind：`structure:` / `reconstruct:` /
  `compile:` / `mismatch: <字段名>`，词表与"绝不写入字节码派生字符串"的规矩都记在
  `structure.structured.ProtoCert.reason`。`tests/test_m4_exit.py` 断言双向耦合
  （非 `L3` 必须有、`L3` 必须没有、kind 必须在词表内）。面板
  `scripts/ledger_dashboard.py` 直接打这个字段的直方图，残差普查因此是常驻数据而
  非一次性脚本。
- `tests/test_m3_exit.py` 断言的是**行内耦合**（M5 task 6 按新 schema 重述）：`L3` 行 ⇒ `l3_level` 非空、`refusal_reason is None`；非 `L3` 行 ⇒ `l3_level is None`、`refusal_reason` 非空；并且**对每一行**，`fallback` ⟺ 有那条 `fallback-state-machine` confession ⟺ 有 occurrence 的 `shipped == "fallback"`。也就是说"confession 摘了但产物没变"、"产物变了 confession 没摘"、"行级聚合与逐 occurrence 记录对不上"三种**记账不一致**都会被抓到。旧的 `L3 ⇒ fallback is False` 已随 `fallback` 改定义而作废（那 150 行 `L3` 确实发的是状态机文本，硬要求它们 `confessions == []` 才是真正的 confession 漏洞）。
- **"等级只升不降"由 `scripts/ratchet_diff.py` 判定，不由 pytest 套件判定**（M5 task 8 落地）——套件里没有历史 baseline 比对，见上文「台账约定」。

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
- `tests/test_behaviour_probe.py`（L1.75 行为探针）：**229 文件、228 字节一致、1 条钉住的发散、398196 个事件**（M4 收口时是 227/2；M6 task 12 让 `snr_mainmenu.lua` 收敛，2026-08-14 实跑复核）。**读它的 reach 分裂再决定信多少**：3000 事件上限截断了 132/229 个文件，这 132 个贡献了 99.5% 的事件，另外 97 个中位数只有 **10** 个事件。
- `tests/test_effects_reconstructor_consistency.py`：把 `lift/effects.py` 与**结构化**路径对账（`reconstruct.py` → `emit/lua.py` 是 `lvm.c` 的第三份独立手抄）。0 违规，靠插桩而不是第四份手抄。它自己的 docstring 记了**它不断言什么**。
- `tests/test_effects_modes.py`：档位标定的普查与钉子，含「`STRICT` 是唯一被 `src/` 选用的档位」这条静态检查。

### 效应档位标定结论（M4 task 11）

`STRICT` 仍是唯一默认；`NO_METAMETHOD` 是允许的逐 pass opt-in，但**只对脚本自建的表成立**（普查在 71414 个常量里找到 0 个元方法相关常量，但语料读取的 164 个全局名里有 56 个从不被写入，来自引擎，普查看不见）；`TRUSTING` 不建议任何 pass 使用（它相对 `NO_METAMETHOD` 只动 3 行，而语料**证伪**了这三行）。`lift/effects.py` 行为未变。两行被判定分级过松、按公理层变更协议留待处理：`LEN` 在 `NO_METAMETHOD` 下应为 `READ_HEAP` 而非 `PURE`（**这是确认的缺陷**，M5 agenda 1）、以及 `NEWTABLE`/`CLOSURE` 的 GC 路径（不建议改）。

### 可读性（与原项目产物对比，`docs/reports/m4-readability.md`）

结构化产物的行数是原项目的 **0.98 倍**（212 个文件全部落在 0.78×–1.03×），`__pld_*` 残留 **0**，212 个文件上 `while`/`break` 的行首计数与原项目**完全相同**（190/190、175/175）。**读得更差的五处（打印器层面）**：非 ASCII 字符串打成十进制转义（这是个日文视觉小说，下游就是翻译——这是最大的一处）、不发 `elseif`（208 个变成嵌套 `if`，最坏 61 层缩进对原项目的 5 层）、字符串键不用点语法（`t["k"]` 对 `t.k`）、函数体不缩进（可能是有意的下游耦合，见「下游耦合」一节）、一元负号打成 `(-1)` 而非 `-1`。外加第六处、结构性的：那 17 个 fallback 文件**按行数占语料的 47.6%**，所以"229 里 212 个"是往好里数的数法。

**这五处打印器层面的差距已由 M5 task 7 全部关闭**（output surface v2，见「下游耦合」与 `docs/runbooks/structured-pipeline.md`）；台账逐次提交字节不变，认证门未做任何放松。第六处（fallback 文件的体量）由 M5 task 6 的 hybrid 发射处理，17 个整文件回退降到 7 个。

**那个 47.6% 的处置，M5 task 12 定案（此前两次说法都不完整）**：它**按 M4 自己写明的口径精确复现**——重测 2026-08-13，M4 那 17 个文件占原项目产物 27623/57998 行 = 47.6%。M5 task 3 说的「五种口径下都不复现」是真的，但它测的是**另外五种**口径（我方产物行、字节码指令、字节码字节、原始源码行、proto 出现次数），没测 M4 声明的那一种。两句话都对，只是分母不同——教训是**引用比例必须连分母一起引**。post-hybrid 的完整五口径表在 `docs/reports/m5-quality.md` §2；不依赖口径的那个数是逐 occurrence 的 **1747/1944 = 89.9% 发结构化文本**。

### 仍未做（都在 M5 agenda）

完整 ratchet CI（baseline diff、降级即失败）**M4 没做**，已由 **M5 task 8 落地**（`scripts/ratchet_diff.py` + `scripts/ratchet_job.sh`，见上文「台账约定」；本仓库无 CI runner 配置，是命令不是自动触发）；`LEN` 重新分级（M5 task 1）；L2 差分执行认证与按键序列 harness（**M5 task 9 落地**，见上文；reach 仅 1 个文件，两个历史检查点的*断言*仍是 task 10，且 snr_common 目前被静态 taint 拒授）；那 89 处残差；`_stack_discipline` 的拆分（**M5 task 11 落地**：拆成 `express/freereg.py`，`names.py` 968 → 494 行、被拆的走查本体 467 → 308 行；顺带发现「四道屏障各有一个 neuter 用例钉在 `tests/test_express_liverange.py`」这句只对前三道成立，第 4 道的钉子在 `tests/test_sir_loops_longtail.py` 与台账不动点测试上。**round 1 更正**：该任务原先还给这条结论捎带了一句「第 4 道是四道里唯一一动就让台账变的」——没量过，且是错的。逐道 neuter 后重生成台账实测：`_same_block` 改 28 个 proto、动 9 行台账，`MOVE d, s` 改 3 个、动 2 行，第 4 道改 3 个、动 2 行；**唯一不动台账的是第 2 道**（`_bar_literal_operands` 的字面量判定，语料上 0/1944），也就是说它是四道里语料完全看不见、证据全靠合成用例的那一道）。


## Phase 5（M5：长尾、L2 门、质量基线）现状

Phase 5 已完成（12 个任务）。**能力边界、认证门不变式、归一化阶梯、L2 门的权威仍是 `docs/runbooks/structured-pipeline.md`**；质量评估在 `docs/reports/m5-quality.md`；**尚未完成的工作全部在 `docs/runbooks/m3-backlog.md` 末尾的「M6 agenda」**（编号条目，可引用）。本节只给定位与速查，细节一律以那两处为准，不在此重复。

### 收口数字（2026-08-13 实测）

- `L3`：**1430/1478 唯一 proto（96.8%）、1896/1944 处出现（97.5%）**（M4 收口 94.0% / 95.4%）。
- **产物**：229 个文件里 **216 全结构化 / 6 hybrid / 7 整文件 fallback**（M4 收口 212/0/17）。逐 occurrence：**1747/1944（89.9%）发结构化文本**；按指令量算 85.8%（M5 起点 65.6%）。
- 移植的质量分（原项目 `semantic_eval.py` 的口径）：**0.968833**（M5 起点 0.935633）。216 个全结构化文件**全部恰好 1.000000**；低于 0.997 的 13 个正好是那 13 个非全结构化文件，一个不多。
- 测试：**867 passed**，本机（macOS 15.2 / Apple M4，arm64）**42.1–44.1s**（最终残余轮 5 次实测）。M5 收口时上限是 45s，最坏一次只剩 0.9s 余量。
  **上限已于 2026-08-13 由 human partner 提高到约 120s，但这是定向拨款而不是放松**（原话大意："收益足够大的话完全可以考虑放宽 test suite 总时间预算。到 2min 这个数量级我觉得都是合适的，但是要明确新的口子是为这个创造收益的形式化验证方案开的，其他边角坏行为（如以前提过的 regex 滥用）就不应该去争夺这些预算"）。
  **可执行形式**：新增的套件耗时必须**可归因到 M6 的形式化验证仪器**（枚举差分驱动及其支撑测量——计划里的 Track 1.1 arm 4 / Task 7、Task 8 的原型，以及它们的不动点门）。**其它一切仍按旧纪律办**：与形式化验证无关的新增耗时要像 45s 时代一样论证，全语料扫描仍然是 job 而不是默认套件成员，`tests/test_engineering_practice.py` 的 regex 禁令等既有守卫不因预算变宽而放宽。每个任务报告新增耗时时**必须给出归属**（"这 Xs 属于/不属于形式化验证"），否则视为未论证。

  **out-of-suite 检查（human partner 2026-08-14 追加）**：有价值但会撑破 120s 的测试**可以不进默认套件**，改为在关键时刻单独派发任务去跑。**但"移出套件"不等于"不再运行"**——本仓库已经为这件事付过两次代价：`scripts/ratchet_diff.py` 至今是「得有人记得去跑」的命令（无 CI runner），而 M6 task 4 一度把观察不动点挪出套件，复审实测发现那是**树里唯一**能抓到那类变异的守卫，随即挪了回来。因此 out-of-suite 的检查必须同时满足四条，缺一条就仍按套件成员对待：
  1. **有名字的家**——落进 `scripts/*.sh` 的一道门（`ratchet_job.sh` 的先例）或一个自带 CLI 的 job 脚本，不是"存在但没人调用的测试文件"；
  2. **写明触发时机**——里程碑收口前、合并前、或"改动了 X 之后必跑"，写在该脚本的 docstring 里，不是口头约定；
  3. **一条命令可跑**，且失败时**非零退出并点名**是哪个对象出的问题；
  4. **最近一次运行结果有可追溯的落点**（任务报告或 runbook），否则"跑过了"是无法核验的声称。

  判断顺序：**先问它是不是唯一的守卫**。如果某类回归只有这一个检查能抓到（用中和实验证明，不是估计），它就应当留在套件里并为它腾预算；只有在存在其它守卫、或它的成本确实与全语料规模成正比时，才移出。

  **"放不下"必须是测量，不是预测（2026-08-14 收紧，起因见下）。** 申请 out-of-suite 的检查还要交代三件事，否则"这个会很慢"就成了万能借口：
  1. **实测耗时 + 当时的输入规模**（"在 N=13 的叶子集上 5.38s"），不是估计值；
  2. **成本的增长量纲**——写明成本随哪个量增长。**如果那个量是数据驱动的，它就可能在没人改代码的情况下爆掉**；
  3. **自带上界并在越界时拒绝**，采用 `probe_enum` 的 `budget-exceeded` 形态：显式报出空间大小、**拒绝集被钉住且进入退出码**、**绝不静默采样也绝不无界运行**。若日后要加采样，必须是一个**独立的判决值**，不能混进"跑过了"。
     **这条第三点在写下时（2026-08-14）对它自己指的那个样例是假的，M6 收口评审补上了实现**：当时 `scripts/probe_enum.py::main` 的退出码只看发散（`return 1 if (unexpected or moved or gone) else 0`），`budget-exceeded` 与 `never-reached` 一个字都不贡献——全量跑法打印 `budget-exceeded 1, never-reached 2` 然后 exit 0。现在 `EXPECTED_REFUSALS` 用与发散**同一个** `adjudicate_pins` 规则钉住这两类拒绝，多一条 / 少一条 / 换个理由都非零退出并点名那个 proto。实跑（2026-08-14）：
     `uv run python scripts/probe_enum.py` → `enum: identical 9, divergent 1, budget-exceeded 1, never-reached 2; 1 pinned divergence(s); 3 pinned refusal(s); budget=4096`，exit 0；把 `snr_s4_10_s.lua:main_58` 从钉子表里删掉再跑同一行 → `UNEXPECTED refusal(s) -- proto(s) no longer driven: ['snr_s4_10_s.lua:main_58']`，exit 1。单 proto 调试跑法只对**它实际跑过的**那些 proto 判钉子（`pins_for`），所以 `uv run python scripts/probe_enum.py snr_s4_10_s.lua main_58` 也 exit 0——此前它会把整张钉子表判成 `gone` 而恒返回 1。

  **收紧的起因，作为本条的样例记下来**：M6 task 7 实测 `snr_s4_10_s:main_58` 的**可枚举空间是 23616，而 `corpus/observation/classes.json` 发布的是 1152**——差 20 倍。原因是 `classes.json` **把所有字符串常量塌成 `"str"`**，而那个值恰恰决定走哪条 `== "..."` 分支。连带结论：**task 4 的「110/113 能塞进 4096」是对粗粒度空间说的，不能用来给真正的枚举做规模估算**，要用 `probe_enum.channels_of` 重新推导。教训一般化：**用一个为别的用途构造的投影去给自己的成本做预算，会在你不知情时错一个数量级。**
  （原先这里还接着一句"这个区间是本机同一会话内向上漂移……`ratchet_job.sh` exit 0"——那是 M6 收口时对**套件耗时区间**的说明，被误接在这段 `input_space` 文字后面，"这个区间"在此没有先行词。已移到下面 Phase 6「收口数字」的测试那一行。）
  **测试顺序从来没有被真正变动过**（2026-08-13 实测）：本仓库**没有装任何随机化插件**——`pytest --trace-config` 里唯一的第三方插件是 `pytest-timeout 2.4.0`，`find_spec("pytest_randomly")` 是 `None`，而 `-p no:randomly` 关掉的是一个不存在的插件，pytest 对此**静默当成 no-op**（`uv run pytest -p no:randomly --co -q` → 867 collected，exit 0）。所以 M5 task 11 的 5 对、task 12 的 5 对、以及审查者在另一台主机上的 10 次，两臂跑的都是**同一个 collection order**：task 11 断言有差别、task 12 「证伪」了它，两边都没检查这个旋钮是否接上。**唯一站得住的结论**：本套件有 1–2 秒的 run-to-run 抖动（42.25–43.39s 与 42.57–43.09s 是同一种配置的两组样本；另一台主机 39.36–41.13s），**跨会话的单次对比分不出任何东西**——本里程碑那些争议时间数正出于此。顺序到底影响不影响，**目前是未测量的**。
- 出口门 `tests/test_m5_exit.py`：四条地板（唯一 `L3` **≥0.94**、occurrence `L3` ≥0.96、结构化 reach ≥0.85、质量分 ≥0.96），全部**刻意低于实测值**，理由写在该文件 docstring 里。唯一 `L3` 那条在最终修复轮从 0.96 放宽到 **0.94（= M4 出口）**：0.96 只剩 12 行（0.75pp）余量，正落在该文件自己描述的 churn 范围内——那是绊线不是地板，而绊线的标准修法就是改阈值。逐行单调性本来就由 `scripts/ratchet_diff.py` 逐行守着（更细的仪器），这条地板只负责粗粒度的「M5 不得低于 M4 收口」。代价已写明：41 行降级至少要付 41 个 occurrence，所以在这两个数下 **occurrence `L3` 才是紧的那条，唯一 `L3` 无法单独触发**（`tests/test_m5_exit.py::FORCED_COUPLING`，并且该耦合被断言为算术强制而非偶然）。

### spec 决策表新增两条（**这是本里程碑最需要被读到的部分**）

两条都是**改动 spec 已确认条款**的决定，因此按流程记进了 `docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md` §2 决策表，不只是记在 runbook：

1. **pass registry 永久退役**（不是推迟）。spec §4 给 pass 协议规定的 apply/verify/commit-or-rollback + confession，已被逐 proto 认证门整体承担且更严；M2–M5 没出现过一个需要它才能表达的变换（可读性特例全在打印层的结构折叠里）。`src/pyluadec/passes/` 从未创建，没有代码被删。插件面本身没被否定，只是客户在 M6+（GPU 提议器）。
2. **§1 目标 4 的 `avg_score 0.997` 从 M5 出口挪给 M6**，M5 出口改为 ≥0.96（实测 0.968833）。理由是算术不是打折：216 个文件已是恰好 1.0，剩 13 个要平均 ≥0.947 才够；把剩余 7 个 fallback 全转 hybrid、按实测 hybrid 质量 0.816791 算也只到 0.9896。0.997 等价于把重构残差全关掉，那是 M6 的量。度量本身未改、未放松。

### 新增 / 变化的东西（速查）

- **hybrid chunk 发射**（task 6）：root 不认证时，`certify_hybrid` 把无法认证的 CLOSURE 站点换成 fallback 内联函数，父 proto 自己的字段仍逐字段比。台账 `fallback` 字段随之**改了定义**，并新增 `occurrences[].shipped` / `occurrences[].hybrid`——细节见上文「台账新字段」。
- **output surface v2**（task 7）：`elseif`、点语法、`-1`、统一 4 空格缩进（含函数体）、可逆 UTF-8 原样输出。字节红线的呈现层修订也在这里，见「工程红线」。**可读性因此在原项目最强的那条轴上反超**：最大缩进深度 61 → **8**，而原项目是 **10**；216 个文件里我们更深的有 **0** 个。
- **ratchet 工具链**（task 8）：`scripts/ratchet_diff.py` + `scripts/ratchet_job.sh`，退出码 0/1/125/128，见上文「台账约定」。本仓库仍无 CI runner 配置。
- **L2 门**（task 9）：按键序列差分执行 + 覆盖率 + 静态 taint 拒授，台账新增逐 occurrence 的 `l2` 字段与行级纯聚合 `verify.ledger.row_l2`。**实测 reach 是 1 个文件**（`snr_lib.lua` L2@100%，2 行 / 3 处 occurrence），另有 164 处 occurrence 记 `{"refused": "taint-static"}`。
- **两个历史按键序列检查点**（task 10）：`tests/test_keyseq_checkpoints.py`，性质同时断言在**原始字节码的 trace** 上，**10** 个注入用例证明断言会红（2026-08-13 重数：该模块收集 12 个用例 = 2 个性质 + 10 个注入；task 10 的报告写的 7 是它 round 0 的数）。**「both-sides」的保证来自性质函数在要求 trace 相等之后被分别施加于两条 trace，不是来自注入**：入库的参数化只改**产物那一侧**，both-sides 形态是文件里明确写着的树外练习——把注入称作 both-sides 是夸大了入库的东西。**注意**：这两个检查点都住在 `snr_common.lua`，而该文件被 L2 静态 taint **拒授**（`doScriptScene == "<字面量>"` 这个语料主力惯用法对运行时 harness 结构上不可观测），所以「检查点绿」与「该文件拿到 L2 徽章」是两件事，后者没有发生也不该靠放松门去发生。
- **`express/freereg.py`**（task 11）：`_stack_discipline` 从 `names.py` 拆出。
- **`refusal_reason` 带上了 `Mismatch.path`**（task 12，M5 agenda 8）：非 root 的失配现在记成 `mismatch: <字段> at <路径>`。实测语料上 22 条 `mismatch` 里 20 条在 `root`、2 条不在（两个 hybrid root），台账因此动了 2 行，ratchet 0 降级。

## Phase 6（M6：跨语料交叉验证）现状

Phase 6 已完成。计划 13 个任务，实际执行 11 个（**T9/T10 取消、T7/T8 缩范围，两条决定都记进了 spec §2 决策表**，见下）外加 3 个计划外任务（两轮前作缺陷手工修复 + loss sweep 门）。**能力边界、认证门不变式、归一化阶梯、L2 门的权威仍是 `docs/runbooks/structured-pipeline.md`**；交叉语料的全部证据在 `docs/reports/m6-cross-corpus.md`（含每个缺陷的指令级走查）、观察数据在 `docs/reports/m6-observation.md`、Class-2 设计说明在 `docs/reports/m6-uiloop-design.md`；**尚未完成的工作全部在 `docs/runbooks/m3-backlog.md` 末尾的「M7 agenda」**。本节只给定位与速查。

### 头条不是一个比率，是已发布软件里的 6 个缺陷

前作产物被重编译、打包回 PSP ISO、由真人通关验证过（十几轮 human-in-loop 修复）。M6 把我们的仪器对准它，**确认了 6 个缺陷，其中 4 个此前未知**，每一个都在指令级走查过：

1. `snr_music.lua:main_3` —— 轮询循环整个消失，音乐鉴赏进去就弹回主菜单，不可用。
2. `snr_common.lua:main_76_2` —— 一个无条件 `break` 让回想模式误开存档界面；一个空 `else` 卡住帧。**两条都逐字对应前作自己 debug playbook 里的历史检查点。**
3. `snr_mainmenu.lua:main_7` —— **四处** gate site 被删（每处各读 `systemSave`/`novelFlag`/`musicFlag` 三个 flag 一次；三个 flag、四处 site，此前这里写成"三道 gate"是把 flag 数当成了 site 数），两条互斥分支同时执行。1-based gate 头在 pc **207 / 745 / 1280 / 1825**，实测计数 `systemSave` 24→16、`novelFlag` 12→8、`musicFlag` 8→4（2026-08-14 复核）。
4. `snr_graphic.lua:main_4` —— 一个 `== 6` / `== 4` 比较被丢掉，出现两次。
5. `snr_memory.lua:main_4` —— 同一个缺陷、同一个形状，同样出现两次。
6. `snr_common.lua:main_75` —— 一个重试 `while` 变成了 `if`。

**6 个全部由静态比对找到；其中 5 个对两条动态臂都不可见。** 两个计划外任务已按缺陷逐个手工修复，产物在 `corpus/pred_repairs/`（指令级 + 运行时双验证，专用驱动脚本同目录；**上游 `$PYLUADEC_PRED_CORPUS_DIR` 一个字节没动**）。

### 收口数字（2026-08-14 实测）

- `L3`：**1438/1478 唯一 proto（97.3%）、1904/1944 处出现（97.9%）**（M5 收口 96.8% / 97.5%）。
- **产物**：229 个文件里 **217 全结构化 / 8 hybrid / 4 整文件 fallback**（M5 收口 216/6/7）。逐 occurrence **1763/1944（90.7%）发结构化文本**。
- 质量分 **0.977328**（M5 收口 0.968833）。**它不再是任何门**——见下文决策日志第一条。
- `scripts/ratchet_diff.py` 对 M5 合并基线 `0957364`：**8 升级、0 降级**。
- 测试：M6 任务收口时 **1077 passed，55.07–55.61s**（macOS 15.2 / Apple M4 arm64 / Darwin 24.2.0，那次会话三次实测）。**收口评审修复轮后：1087 passed，三次实测 52.73 / 56.18 / 56.83s**（同一台机器，2026-08-14；修复轮加了 10 个用例，`--durations` 单测合计 **0.29s**，全部可归因到形式化验证仪器——`probe_enum` 的拒绝集契约与单 proto 判钉、L1.75 钉子键的注入证明、`classes.json` observed 半边的摘要钉）。同一棵树上修复前的基线是 **1077 passed，57.90s**——修复后的两次都比它低，所以这 10 个用例埋在会话内漂移里。都对约 120s 的定向拨款。
  **这两个区间不要跨会话直接比**：本机在**同一会话内向上漂移**（仓库里已记为 thermal），且本套件有 1–2 秒的 run-to-run 抖动——这也是这一段被从上面那条 `input_space` 说明里搬回来的原因（"这个区间"在那里没有先行词）。
  `./scripts/ratchet_job.sh` 三道门 exit 0：M6 收口时端到端 **57.9–58.2s**，修复轮后同一台机器实测 **60.05s**（`time` 实测，2026-08-14）。**它现在要求 `PYLUADEC_PRED_CORPUS_DIR`**：不设就在第 35 行直接非零退出，因为不设时 32 个 M6 门用例会静默 skip（实测 `1054 passed, 32 skipped`——`test_cross_corpus.py` 22、`test_loss_sweep.py` 8、`test_predcorpus.py` 2）。
- 前作语料 parity 普查：**229/229 可编译、229/229 proto 树 1:1 对应、0/229 字节精确**（3903 处实质失配 / 1433 条路径 / 2989 个信号，由 `tests/test_predcorpus.py` 断言）。
- 分歧队列：**18 行 / 16 个文件**，裁决为 **6 `real-bug` / 12 `equivalent-transform`**；`intentional-edit` 作为**路径级**裁决出现 1 处（`snr_common.lua:main_83` 的字体资源路径，行级裁决仍是 `real-bug`）；`probe-artifact` 与 `suspect` **各 0 行**。
- Loss sweeps：1944 对 proto 里 **25 个丢了东西**，**3.31s**；按扫描 `global_reads` 1 / `n_natural_loops`+`n_back_edges` 4 / `test_ops` 24 / 第四组（`global_writes`、`call_targets`、`call_shapes`、`return_arity`）**0**。

### 新增的东西（速查）

- `src/pyluadec/predcorpus.py`（task 2）：前作源码 → `oracle.compile_source` → `ingest`。**`strip` 参数必须由调用方按 `strip=not carries_debug(original)` 显式选**，否则 260 个 `nups > 0` 的 proto 会凭空多出 `upvalues` 长度失配（这个伪影已经污染过一次普查数字）。
- `src/pyluadec/lift/footprint.py` + `scripts/footprint_dump.py`（task 3）：静态交互面（全局读写、表键读写、调用、`dynamic_reads` 诚实计数），产出 `corpus/observation/footprints.json`。
- `scripts/observation_classes.py` + `corpus/observation/classes.json`（task 4）：**156 个候选** proto（29 个叶子拒绝 + 132 个 CAP 主导，5 个两者兼是）的分类与交互面，`choice-branch` 113 / `ui-keyloop` 9 / `neither` 34。
- `scripts/cross_corpus.py` + `tests/test_cross_corpus.py`（task 5/6）：指纹 / L1.5 / L1.75 三条臂的跨语料扫描 + `PRED_PINS`（与我方钉子**分表**，spec 明令不得复用）。全语料扫描是 job，不是套件成员。
- `scripts/loss_sweep.py` + `tests/test_loss_sweep.py`（计划外 task X3）：四组「原始有、前作没有」的逐 proto 丢失扫描。**这是本里程碑最划算的仪器**——比被设计的分级指纹便宜，而且**把缺陷排到了 proto 粒度并点名**。（此前这里写"多抓到两个缺陷"，报告没有这么说，也不成立：6 个 `real-bug` 文件**全部**被指纹钉住，`main_75` 本来就在指纹队列里排第 9/18；报告说的"聚合掩盖掉的那一个"比的是 §3.7 自己更早的**聚合**扫描，不是指纹。）
- `scripts/probe_enum.py` / `.lua`（task 7，已缩范围）：枚举差分驱动，在 13 个复合 `if` 叶子上做可行性演示，`EnumVerdict` 带 `budget-exceeded`（**绝不静默采样**）。
- `tests/test_m6_exit.py`（task 13）：出口门，13 个用例，**0.15s**，不需要语料。地板见该文件 docstring。

### spec 决策表新增三条（**本里程碑最需要被读到的部分**）

三条都改动了 spec 已确认条款，因此按流程记进 `docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md` §2 决策表：

1. **`avg_score 0.997` 不再是任何里程碑的出口门槛**（2026-08-13，human partner），降级为面板观测值。**理由不是够不着**（收口实测 0.977328）：M6 实测该指标与缺陷检出无关——6 个缺陷全由静态比对找到，其中 `snr_common.lua:main_75` 的 `cfg_reachable` 分量**恰好 1.0**，而它唯一的循环没了。`tests/test_m5_exit.py` 的 0.96 地板继续有效，未收紧未放松。
2. **Task 7 / Task 8 缩范围**（2026-08-14）：T7 从全语料枚举扫描缩为 13 个叶子上的可行性演示，T8 从「设计 + 原型」缩为设计说明。依据是测量：5/6 个缺陷对动态臂不可见；最便宜的静态工具赢过被设计的那个；T8 的前提（「不终止是 Class 2 的区分性难点」）被证伪——**当时的候选集 127/162 每轮迭代都轮询按键，含 113/113 个 `choice-branch`**（收缩后的候选集上复测 **125/156**）。
3. **Task 9 / Task 10 取消**（2026-08-14），记为**前提被测量证伪**而非未完成：`build_sir` 在前作对应的 13 个叶子 proto 上成功 **12 个（92.3%）**，机械参照几乎免费，那趟 ~1–2M token 的 LLM pass 买不到任何新东西。修复前的 6/13 是被我们自己的缺陷污染的数，别再引用。

### task 11 / task 12：残差收口的技术要点

- **task 11：compound `if` 条件树。** `sir/regions.py` 新增 `CondTest` / `CondOp` / `CondNode` / `cond_claimed`，识别器 `sir/build.py::_match_cond_chain`，重建 `express/reconstruct.py::cond_tree_expr`，打印是 `emit/lua.py::Printer.condition` 的新分支（纯折叠）。**派发顺序被测量证明过**：先单比较、失败才试链，反过来会降级 5 个 proto。`structure:` 家族 **21 → 1** 个台账形状（幸存者 `snr_common.lua:main_71` 不是条件缺陷，是 `_match_loop` 认不出那个 `while true`）。**仍是缺口**：`while <a and b> do`、`repeat ... until a or b`，由 `tests/test_sir_condtree.py::WHILE_HEADER_GAP` 钉住，语料上没有 proto 需要它们。
- **task 12：`write_reg` 的 `declared` 闸门。** 该闸门至少是**五个机制**：A 构造器字段存储（已关）、B 逐定义的闭包捕获（已关）、C `_same_block`（40 行里 6 行，未关）、D clamp / 条件值形状（3 行，未关）、E A 的 `hazard` 集后果（未关）。`snr_music.lua:main` 的别名表（M5 的诊断）**是对的，且已关**。
- **残差记账（2026-08-14 实测）**：40 个非 `L3` 台账行 = **29 个自身拒绝 + 11 个继承祖先**；已归因 9 行（6 `_same_block`，其中 1 行是继承的 root；3 clamp，全是自身拒绝），**未归因 21 个自身拒绝 + 10 个继承 = 31 行**。这两个口径都出现在旧文档里，指的是同一件事的不同分母。

### 本里程碑反复出现、值得带进 M7 的那个缺陷

**「散文断言了没人量过的行为」**——M5 的 task 8/9 各花四轮；M6 有 **9 个 `fix:` 提交（8 轮复审 + 1 轮计划外修复）**，而**每一轮的主题就是上一轮写下的假句子**，commit 标题本身即证据：task 2「strip-mode asymmetry」、task 4「loops are headers」、task 5「two false sentences」、task 7「a false headline mechanism」、task 8「a misattributed verdict」、task 11「a tautology sold as evidence」、task 12「a false convergence story in five places, a wrong axiom citation」——最后这条是**公理层的错误引用**，也是这类缺陷能造成的最大伤害。本里程碑另有一类同形错误：**用一个为别的用途构造的投影去给自己做预算**（`classes.json` 的 `input_space` 把字符串常量塌成 `"str"`，于是 1152 与真实的 23616 差 20 倍）。写任何行为性句子之前先量它，包括没有测试断言的那些；最高级词（唯一 / 总是 / 从不 / 全部 / 完整 / 停止）每出现一次都要么有一次测量，要么改写。**文档是这类缺陷活得最久的地方。**

