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

尚无代码与构建体系（空仓库，无 commit）。上述命令均指原项目；本仓库的构建/测试命令确立后应回填到此文件。
