# pyluadec 重构总体方案设计

- 日期：2026-08-09
- 状态：已经用户逐节确认（5 节），待实施计划（writing-plans）
- 方法：superpowers brainstorming + ADHD 并行发散（5 帧 × 6 想法 → 打分聚类 → 3 支深化）

## 1. 背景与目标

本仓库从头重构 `/root/pyluadec`（Lua 5.1 字节码反编译器）。语料为 229 个 PSP 游戏 bytecode（vanilla luac 5.1.5 输出；header 表明 sizeof(size_t)=4，其余字段与 LP64 一致，lua_Number 为普通 double）。

> **2026-08-10 实测更正**：起草本 spec 时假设语料"未 strip"，据此把 debug 段（lineinfo 单调性、locvars 作用域 PC 区间）当作白送的语句边界与变量命名 oracle（见 §4 ④express、§10 收敛短名单）。**该假设不成立**——229 文件 / 1944 proto 的 lineinfo、locvars、upvalue 名称全为空，`source` 为占位符 `=?`。影响：所有局部变量名必须合成；语句边界必须由控制流与寄存器生命周期推导；§4 中"debug 信息只作命名/物化 hint"的规则保留（对将来自编译的测试用例仍生效），但对本语料永不触发。摄入层无损保留这些字段的能力仍是正确设计（新编译的文件确实带 locvars，且是回归测试的一部分）。
>
> 唯一幸存的行信息是 `linedefined`/`lastlinedefined`（属 `DumpFunction` 主体而非 debug 段，1715/1944 非零），即每个函数在原始源码中的起止行——可作函数排布的弱校验，无语句级粒度。原项目的架构级教训见根目录 CLAUDE.md（无表达式 IR、CFG 未被结构化使用、ad-hoc 特例堆积核心函数、文本断言测试）。

重构目标：
1. 64 位环境处理 32 位 bytecode（Lua 5.2 为 stretch goal）；
2. 精巧 pipeline，ad-hoc 处理以可注册插件形态存在；
3. 系统化的语义正确性验证；
4. 验收：原项目语义类回归全过 + 229 语料质量不回退（原基线 avg_score 0.997）。

## 2. 已定决策（与用户逐项确认）

| 决策点 | 结论 |
|---|---|
| 输出面兼容性 | **语义等价即可，风格自由**。不承诺重刷 post_process 链路；旧文本断言测试按意图转译（见 §8）。 |
| bytecode 读取路径 | **pybind11 + 双字长 lua 构建**（用户提案）：对 lua-5.1 打极小的序列化宽度补丁，64 位主机同时编出 sz4/sz8 两套库与 oracle，Python 按 header 派发。 |
| GPU（RTX 5080 16G，位于未来 64 位环境） | 仅作**提议器类插件**（神经提议 + 硬验证门）；端到端 seq2seq 还原被否决（无语义保证、语料不足）。 |
| 总体路线 | **方案甲（证明门控分层管线）为骨架，吸收方案乙（编译器反演）**：乙的归一化 roundtrip 比对器即甲的 L3 验证门；lparser/lcode 插桩规则挖掘留作后期实验插件。 |
| **pass registry（§4 pass 插件协议、§3 布局里的 `passes/`）** | **永久退役，不是推迟**（2026-08-12，human partner；记录于 M5 task 12）。理由：§4 给 pass 协议规定的三件事——`apply` 出候选、`verify` 判定、失败即 rollback 并记 confession——已经被认证门整体承担且承担得更严。`structure/structured.py::emit_certified_chunk` 对**每个 proto**做「打印候选 → 真 `luac_sz4` 重编译 → `compare_protos` 逐字段比 → 不过就退回语义精确的 fallback 并在台账 confess」，即 registry 想要的 apply/verify/commit-or-rollback 循环，只是判定器是重编译比对而不是每个 pass 自带的 `verify`。M2–M5 全程没有出现过一个需要 registry 才能表达的变换：读者可见的特例（`elseif` 折叠、点语法、UTF-8 呈现、hybrid 替换）全部落在打印层或认证层，都是**结构折叠**而非 IR→IR 重写。保留一个零消费者的协议只会让「哪里放特例」这个问题有两个答案。**插件面本身没有被否定**，只是没有客户：真需要它的是 M6+ 的 GPU 提议器（§2 GPU 行、§10 provocation），到那时按提议器的实际接口重新设计，而不是先立一个为 2026-08-09 的猜想服务的协议。**没有代码被删除**——`src/pyluadec/passes/` 从未创建过。 |
| **§1 目标 4 的验收数字 `avg_score 0.997`** | **M5 出口重新划定为 ≥0.96（实测 0.968833）；0.997 整体挪给 M6 作为其出口**（2026-08-12，human partner；记录于 M5 task 12）。理由是实测出来的算术，不是打折：M5 task 3 移植该度量后实测起点 **0.935633**，tasks 4/5/6 推到 0.946390 → 0.950580 → **0.968833**。此时 216 个文件已经是**恰好 1.000000**，于是剩下的 13 个必须平均 **≥0.947** 才能到 0.997；而把剩余 7 个整文件 fallback 全部转成 hybrid、**按实测的 hybrid 质量 0.816791 算**，也只到 **0.9896**。即：0.997 要求几乎每个文件都在 ~1.0，等价于把重构残差（13 个复合 `if` 拒绝 + 4 个 hybrid 发射所**揭露**的 root 重构缺陷，其中 `snr_music.lua:main` 已定性为 `classify_registers` 把 temp 当 local 而把四个嵌套表构造器折叠成一个别名表）全部关掉——那是 M6 的工作量，不是换一种拼装 chunk 的方式能买到的。度量本身未被改动、未被放松；门 `tests/test_m5_exit.py` 的地板同样低于实测值，理由见该文件 docstring。M6 的出口即本行的 0.997。**——本行的最后一句已被下一行推翻（2026-08-13）：0.997 没有成为 M6 的出口，它被整体撤下为观测值。** |
| **§1 目标 4 的验收数字 `avg_score 0.997`（第二次修订）** | **0.997 不再是任何里程碑的出口门槛，降级为面板观测值**（2026-08-13，human partner；记录于 M6 spec §0 与本行，M6 task 13 落地）。原话大意："旧项目的打分指标在现在看不是特别关键的东西，如果它成为掣肘，可以考虑抛弃。" 上一行把 0.997 交给 M6 时，它还是"下一个里程碑的出口"；M6 立项时被整体撤下。**理由不是够不着**：M6 收口实测 **0.977328**（`scripts/quality_score.py`，2026-08-14；M6 起点 0.968833），229 个文件里 **217 个恰好 1.000000**，剩下 12 个拉低均值。真正的理由是这个指标测的是"我们的产物有多像原始 proto 树"，而 M6 的实测结论是**该指标与缺陷检出无关**：M6 在前作已发布产物中确认的 6 个缺陷，全部由静态比对（`scripts/loss_sweep.py` 的四轮扫描 + `compare_protos`）找到，其中 `snr_common.lua:main_75` 的 `cfg_reachable` 分量恰好是 **1.0**——指纹给满分的 proto，唯一的循环没了。指标继续在 `scripts/ledger_dashboard.py` / `quality_score.py` 报告，`tests/test_m5_exit.py` 的 0.96 地板继续有效（M6 未收紧、未放松）；**M6 出口不设质量门**，其出口见 `tests/test_m6_exit.py`。 |
| **M6 Task 7 / Task 8 重新划定范围（2026-08-14）** | **T7 从"全 Class-1 候选集的枚举差分扫描"缩为"在 13 个复合 `if` 叶子上的可行性演示"；T8 从"设计 + 原型"缩为"设计说明"**（human partner；完整论证见 `docs/superpowers/plans/2026-08-13-phase6-m6-cross-corpus.md` 末尾第一条 AMENDED）。**依据是测量，不是取舍**：(a) 6 个缺陷全部由静态臂找到，**其中 5 个对两条动态臂都不可见**（`snr_mainmenu:main_7` 在 18 事件的行为臂上返回 `agree`；`snr_common.lua` 的行为臂是静默的，`truncated:1/79`）；(b) 最便宜的静态工具赢过被设计的那个——`scripts/loss_sweep.py`（每 proto 一次遍历，1944 对 **3.31s**，2026-08-14 实测）找到了分级指纹找到的全部，**外加**一个指纹 `cfg_reachable` 打 1.0 的缺陷，**再加**一个 task 6 聚合 test-op 计数掩盖掉的缺陷；(c) T8 的前提被 task 4 证伪——它把"不终止"当作 Class 2 的**区分性**难点，而实测 **127/162 个候选（当时的候选集）每轮迭代都轮询按键，含 113/113 个 `choice-branch`**（2026-08-14 在收缩后的候选集上复测为 **125/156**，其中 **116** 个的轮询点支配该循环的全部 latch，方法见 `docs/reports/m6-observation.md`），两类不独立。被删掉的全语料枚举扫描与 UI 循环原型转入 M7 seed。 |
| **M6 Task 9 / Task 10 取消（2026-08-14）** | **两项从 M6 移除，记为「前提被测量证伪」，不是未完成的工作**（human partner；完整论证见同一计划文档末尾第二条 AMENDED）。T10（每个叶子 proto 一个 opus 级 subagent 做 LLM 元重建，预算 ~1–2M tokens）立项的前提是"机械式结构参照可能拿不到"；T9 Step 1 正是计划自己为 T10 设的闸门（"若成功率低，参照价值坍塌，报告并停下等裁决"）。实测（task 11，其复审独立复算）：**`build_sir` 在前作对应的 13 个叶子 proto 上成功 12 个 = 92.3%**，唯一失败是 `snr_common.lua:main_76_2`（`pc 63: unrecognized transfer JMP`）。修复前的 **6/13** 是被混淆的数字——它的 7 个失败里有 6 个正是 task 11 关掉的复合 `if` 缺陷，量的是**我们自己的识别器**而非前作质量。机械参照既然几乎免费，那趟 LLM pass 买不到任何它没有的东西。T9 自身的价值也被 task 11 的发现削弱：残差population 的阻塞点是 `Reconstructor.write_reg` 的 `reg not in self.declared` 闸门，一个**寄存器分类**缺陷，而区域树不说明哪些寄存器是局部变量、哪些是临时值。**若将来出现 `build_sir` 在前作侧成功率明显低于 92.3% 的 population，这两项的论据回归，首先要重跑的就是这个测量。** |
| **M7 §5 止损线重设：≤10 行 → 22 行 + 归因完备（2026-08-16）** | **收口残差地板从「≤10 行非 L3 且 snr_common 不在列」重设为「22 行 + 每行具名归因」，snr_common 例外条款按实测改写**（human partner，task 10 期间按 §5 预编程的升级条款裁决；选项：直接接受 28 / 修 K2+O 后重设 22 / 再开 L3.3 rung / 全推 ≤10）。**依据是普查测量，不是放松**：(a) 地板 10 立于「21 行未归因 ≈ 一个机制族」的假设上，campaign 普查证伪——28 行分属 **8 个机制族**，其中 **7 行已被既往决定排除**（K1 int2fb 编码不承认精确比较 5 行、C 常量池顺序 2 行 = L3.2 rung 已裁定 decided-not-doing），即使修尽已知修法也到不了 10；(b) 裁决选 B：先修两个修法已知的族（O 键序屏障 `_bar_key_staged_below_table` −4 行、K2 NEWTABLE 位置前视 −1 行）到 22，`L3 1456/1478（98.5%）`、occurrence `1922/1944`、222 全结构化 / 5 hybrid / 2 整文件 fallback；(c) snr_common 例外条款的**理由**（「147 occurrences 压 fallback 侧太重」）实测已不成立——该文件为 hybrid，147 处 occurrence 里 **106 处发结构化文本**，仅 frontier 6 个替换点及其子树共 41 处 fallback（全语料 1880/1944 = 96.7% 发结构化）；例外条款随之改写为按此测量表述。**L3.3 rung（NEWTABLE 提示位遮蔽，可认证 K1 的 5 行）显式留作 M8 候选，不在本里程碑开**——它改变认证门比对语义，值得自己的评审轮。归因普查（8 cluster、逐行 first-divergence 证据）的家在 `docs/runbooks/structured-pipeline.md`「What is left」。 |
| **字节红线第二次作用域修订（2026-08-15）** | **可逆 UTF-8 呈现判定从 `emit/lua.py::_str_lit` 扩展到 `structure/fallback.py::str_lit`**（human partner 作为独立决定批准，M7 task 5 Step 0；按名反转 2026-08-12 修订的「只落在 `emit/` / 不得扩大这个口子」）。机制：判定本体单一归属在 `structure/fallback.py::str_lit`（M7 task 5 从 emit 搬入），`emit/lua.py::_str_lit` 是薄委托——`emit → structure.fallback` 的 import 方向 M5 就已存在（escape 回退），沿之不产生环。动机：下游是翻译，而 fallback 产物与 hybrid 内联子树的游戏文本此前全为十进制转义（M4 可读性报告点名的最大差距）。机器检验与第一次修订同形：两种拼写编译出相同常量，**`corpus/ledger.jsonl` 逐次提交字节不变（M7 task 5 实测：`run_corpus.py` 重生成后 `git diff --exit-code` 通过）**；实测效果 snr_common 12,159 + snr_novel 42 个常量字节从转义变原样，全语料转义残留 5 处、全是常量内换行控制字节（`\010`，llex 对裸换行会误读，属必转义类）。`ingest`/`lift`/`verify` 一个字节不解码，前后皆然。spec §4 原文的抽查例名 `doScriptScene` 在反编译产物中零站点——实际文本载体按语料实测记录（snr_common 的原样输出为证）。**收口精确化（2026-08-16，task 12）**：「零站点」在**直接调用形式** `doScriptScene("…")` 口径下成立且复测为 0；但该标识符作为**子串**在仍发 fallback 文本的文件里有 8 处引用（其中 5 处本身是 `doScriptScene = __pld_R[n]` 箱形态），且 fallback 子树里的游戏台词以 `__pld_R[n] = "<日文>"` 形式出货——全语料 **52 行**（snr_common 49、snr_story_main 2、snr_novel 1）。**§4 验收的编码分句达标（17727/17727 原样 UTF-8，floor 门在 `tests/test_m7_exit.py`）；调用语境分句对这 52 行未达标，普查由钉子测试钉死、修复路由到 M8**（controller review 2026-08-16 判为 M8 量级，不在收口轮开工）。 |
| **M7 §3 go/no-go 处置：0.0067 < 0.70，按 partner 指令继续（2026-08-16）** | **pred 再认证率在修正 T 映射后为 (T3 10 + T2 3)/1944 = 0.0067，远低于 §3 的 0.70 政策线；human partner 指令 Task 11 照常推进**（2026-08-16，本会话）。该政策线「存在以强制报告，不是编码预测」的目的已达成：机制 F（前作样板死局部变量→根 `maxstacksize` 失配→整文件回退）在 task 2 指令级走查、task 11 修正幻影等级后完整归因。**后果是算术不是裁量**：pred 侧要在 T 上严格更优才能赢（E=id 使平级全归我方），仅 `config.lua` 达 T3 且输在 E 平级决——229/229 全选我方，`*-verbatim` 残差结构性为空（无等级即不资格）。合并退化（`corpus/final/` 逐字节等于我方产物）的诚实表述是「判据度量的是**经我方管线的可重认证性**，pred 因一个已诊断的良性原因 99.3% 过不了」，不是质量判决；结论另由独立理由支撑（我方 fallback 语义精确、pred 有 6 个已确认缺陷）。同日落地 **T 映射顺序修正**（shipped-first，spec §2 的 T- 定义）：703 个 pred 幻影 T3 与 49 个我方幻影 T3 改记 T-，文件级选择在两种顺序下同分布（229/229 复测），修正是记录诚实不是结果变更。 |
| **M7 收口：warranty 记录的 T- 单符号双语义留作 M8 schema 候选（2026-08-16）** | **`warranty.jsonl` 里我方 `T-`（64 处 occurrence，M2 地板：构造性语义精确、可编译、L1.5/L1.75 探针覆盖）与 pred `T-`（无任何正面验证）同形不可辨**（spec §2 条款的忠实实现；controller review Important 3）。拆分符号会 churn 已提交产物而不动任何选择，故记入生成器 docstring 与报告、路由 M8，不在收口轮改。同轮落盘两条结构性事实：**Factor E 从不判别选择**（36 组合穷举，12 种 pred 胜全为严格 T 优，`tests/test_m7_exit.py` 钉住）；**task 4 的裁决欠账因选择结果失效而结清**（欠账人群零行出货，机制未被绕过——若 pred 赢文件其 unpinned 行仍会取消其资格）。 |

## 3. 架构分层与仓库布局

六层管线，每层输入输出为可序列化工件（可快照、可 diff、可单独测试）：

| 层 | 职责 | 关键纪律 |
|---|---|---|
| ① ingest | 双字长 pybind bridge 无损加载 bytecode → Proto 树 | 字符串是 bytes、数字带原始 8 字节 payload、lineinfo/locvars 全保留 |
| ② lift | 指令 → 带效应标注的低层语句（reads/writes/effect-class） | 纯查表，零聪明处理；38 opcode 效应表是全项目公理层 |
| ③ structure | CFG + 支配树 → PC 划入结构区域 | 每条 PC 必须被恰好一个区域认领否则 hard fail；识别失败 → 函数降级为 pc 派发状态机（丑但语义精确） |
| ④ express | 寄存器 → 表达式树 | 内联需活跃性证明（单次使用 + 无干预副作用）；debug 信息只作命名/物化 hint，不授权合并 |
| ⑤ beautify | 注册制 IR→IR pass 链 | 每 pass 逐函数 apply→verify→commit/rollback；一切特例处理是这里的插件 |
| ⑥ print | AST → Lua 源码 | 纯格式化，不做语义决策 |

仓库布局（Python 用 uv 管理）：

```
pyluadec-refactor/
├── CLAUDE.md / docs/superpowers/specs/     # 设计与操作文档
├── vendor/lua-5.1/                          # vanilla 源码；序列化宽度补丁以 patch 文件单独管理
├── native/                                  # C++：sz4/sz8 两个 pybind 扩展模块 + CMake
├── src/pyluadec/
│   ├── ingest/      # header 派发 + Proto 数据类
│   ├── lift/        # effects.py（opcode 效应表）+ 提升
│   ├── cfg/         # 基本块、支配树
│   ├── structure/   # 区域识别 + fallback 状态机发射
│   ├── express/     # 证明门控表达式提升
│   ├── passes/      # 美化 pass 插件（一个特例一个文件）+ registry
│   ├── verify/      # 归一化比对器（L3）、差分执行（L2）、台账
│   └── emit/        # 打印层
├── tests/                                   # 单元 + 语义回归 + 生成型用例
└── corpus/                                  # golden 档案 + ledger.jsonl（语料本体路径可配置，见 §6）
```

语料本体（229 个 bytecode）不入本仓库，通过配置（环境变量 `PYLUADEC_CORPUS_DIR` 或 config 文件）指向；golden 档案与台账则 check-in，保证换机（如 macOS 开发机）后仓库自足。代码中禁止绝对路径（原项目有 67 处 `/root/pyluadec/...` 硬编码的教训）。

## 4. IR 数据模型与 pass 接口

三种核心 IR，均为不可变数据类（修改 = 产生新节点，旧节点即快照）：

- **LIR**（②输出）：指令的 1:1 语句化镜像。每条带 `pc`、`op`、已解 RK 的操作数、`reads/writes: set[Reg]`、`effect: EffectClass`。效应格：`PURE < READ_HEAP < WRITE_HEAP < ARBITRARY`（CALL 与一切可触发元方法的操作；元方法风险的默认档位可配置，见 §9 风险 R1）。
- **SIR**（③输出）：区域树 `Seq / If / While / Repeat / NumericFor / GenericFor / Break / Return / FallbackStateMachine`，叶子为 LIR 语句。每区域带 `claimed_pcs`；全树认领集合必须恰好等于函数 PC 全集（审计 pass 强制，防静默吞指令）。
- **AST**（④⑤工作对象、⑥输入）：常规 Lua AST，每节点带溯源三元组 `(proto_path, pc_range, producing_pass)`。字符串字面量全程 bytes（打印层直接转义，不经 str 解码，Shift-JIS 无损）。

数字常量在 IR 中携带原始 8 字节 payload；打印用 `%.14g`（不足以 roundtrip 时升 `%.17g`），但验证比较的是重编译后常量表的 payload 逐位一致——十进制打印丢失精度的值（-0.0、16.000000000000004 等）不会漏过验证门。

pass 插件协议 —— **已退役（2026-08-12，见 §2 决策表「pass registry」行）。以下保留为设计
记录，不是当前契约**：`src/pyluadec/passes/` 从未创建，registry 从未存在，其
apply/verify/commit-or-rollback 职责由 `structure/structured.py` 的逐 proto 认证门
承担。⑤beautify 层因此在实现中不存在，特例落在⑥print 的结构折叠里。

```python
class Pass(Protocol):
    name: str
    requires: list[str]                            # 前置 pass
    reads: set[NodeKind]; writes: set[NodeKind]    # 契约，运行时强制，越权即崩
    def apply(self, fn: FunctionIR) -> FunctionIR | None   # None = 不适用
# 管线对每个 (pass, function)：
#   candidate = pass.apply(fn)
#   if candidate is not None and verify(candidate, fn): commit(candidate)
#   else: rollback + confession 记录
```

原项目 14 种硬编码 idiom 与 20 余个 `_fold_*` 文本重写，各自成为一个独立 pass 文件；核心管线代码不随特例数量增长。外部提议器（GPU 模型）与普通 pass 接口相同，仅 `apply` 实现走模型推理——提议不可信没有关系，验证门是唯一落地关口。

## 5. 验证体系与认证台账

三级证据（pass 验证门与最终产物认证共用）：

- **L3 proved**：产物经仓库内 `luac_sz4` 重编译，与原始 proto 树做归一化比对。归一化阶梯 L3.0（严格逐字段相等）→ L3.k（每级引入一个单独论证过健全性的归一化：寄存器重编号、常量池排序、行号剥离、等价跳转拓扑），归一化集合版本化。比对器是独立子模块 `verify/normalize.py`（吸收自方案乙），用自造正负例测试（同源两次编译 = 正例，微改源码 = 负例）。
- **L2@cov%**：差分执行——原始 bytecode 与重编译产物在同一 stub 环境运行（metatable proxy 自动 stub、录 call trace、步数上限；继承原项目 blackbox_runtime 思路），trace 一致即过，徽章附带分支覆盖率；stub 被内省（type/rawequal/getmetatable）即标 taint，taint 污染分支决策则拒授。游戏脚本另配按键序列 harness（继承原 playbook）。
- **L1 unverified / L0 refused**：未验证 / 拒绝（输出带注释的反汇编）。L0 是诚实状态而非失败，留在台账上等待后续 pass。

**台账** `corpus/ledger.jsonl`（check-in）：每条 = 一个 proto，主键为归一化结构哈希（同内容函数跨文件去重）；字段：等级、L3 归一化级数或 L2 覆盖率、confession 列表（pc 区间 + opcode 窗口指纹 + 所属 pass）、猜测计数、oracle 版本（仓库内 lua 构建 commit hash）。

**Ratchet CI**：全量重算 229 语料与 baseline diff——任何 proto 降级、confession/猜测计数上升即 fail；升级自动更新 baseline；台账是单调谓词，可直接喂 `git bisect` 自动定位回归提交；oracle 升级触发全量重认证，其 diff 亦受 ratchet 约束。

**Confession 的第二用途**：聚类得"未结构化 idiom 排行榜"= 开发 backlog；GPU 提议器也从该榜取任务。

## 6. 构建体系与 64 位迁移

**双字长构建**：
- 补丁（预计 20-30 行，patch 文件管理）：`lundump.c`/`ldump.c` 中序列化 size_t 改为编译期类型 `LUAC_SERIAL_SIZET`（默认 `size_t`；`-DLUAC_SERIAL_SIZET=uint32_t` 即 sz4 模式），header 校验字节随之参数化。LP64 上 int/Instruction/double 与 PSP 格式本就一致，size_t 是唯一差异点。
- CMake 一次配置产出：`liblua_sz4`/`liblua_sz8` 静态库；`luac_sz4`/`lua_sz4`/`luac_sz8`/`lua_sz8`（sz4 对 = 32 位格式的编译/执行 oracle，也是未来游戏重打包工具）；`bridge_sz4.so`/`bridge_sz8.so`（各自静态链接对应 liblua，`-fvisibility=hidden` 隔离符号）。
- `ingest/dispatch.py` 读 header 第 9 字节（sizeof size_t）选 bridge。Lua 5.2 = 第三对构件 + 派发表一行。

**macOS（Apple Silicon）兼容关注点**：未来 64 位开发主要在 Mac mini（arm64 macOS）上进行，仅 CUDA 相关开发使用 Linux。arm64 与 LP64 Linux 同为小端、LP64、IEEE double，sz4 补丁与派发逻辑不受影响；需要注意的是工程层面：

- CMake 平台条件化：`LUA_USE_LINUX`（readline + dl）仅限 Linux，macOS 用 `LUA_USE_MACOSX`；不无条件链接 `m`/`readline`；编译器为 AppleClang，`-fvisibility=hidden` 通用。
- pybind 扩展一律经 `pybind11_add_module` 生成（后缀/链接方式由其处理），Python 由 uv 管理以统一双平台版本。
- 迁移 Step 2 的三道门在**两个 64 位平台都要过**：golden 比对与 sz4 往返测试进 CI，x86_64-linux 与 arm64-macos 双跑（防止隐性平台假设，如结构体填充、char 符号性）。
- APFS 默认大小写不敏感：语料/产物文件名不得仅靠大小写区分（现语料全小写，满足）。
- GPU 提议器（M6+）的模型推理依赖（CUDA/torch 等）做成 optional extra，macOS 环境不安装也能跑全部核心管线与测试；CUDA 实验固定在 Linux 环境。

**迁移三步**：
- **Step 0（32 位）固化 golden**：旧 bridge + `luac -l -l` 对 229 语料产出 golden（原始文件 SHA256 + 逐字段 proto dump + listing），入 `corpus/golden/`。Golden 派生自原始字节码与旧工具双源，此后永不由新工具重新生成。
- **Step 1（32 位）新构建就位**：双字长构建 + 新 bridge 在 32 位开发编译；新 bridge 输出与 golden 逐字段比对，差异清单留档（预期差异 = 新 bridge 补回的字段，与 listing 交叉确认）。
- **Step 2 切换**，三道门：① 64 位下全套构件编译通过；② `lua_sz4`/`luac_sz4` 对 229 语料"加载→重 dump→字节一致"往返；③ 64 位 bridge 输出与 golden 完全一致。

**切换时点：尽早——在写任何反编译逻辑之前完成（M0-M1）**。摄入层闭环后，上层是纯 Python 数据处理，与宿主位宽无关；此后 32 位环境仅作不可解释差异的仲裁复现现场。

## 7. 测试策略与里程碑

测试金字塔：
1. **公理层属性测试**：effects 表与 lift——程序化生成源码 → luac → lift → 门控内联 → 打印 → 重编译 → 归一化比对（hypothesis 风格）。
2. **组件单元测试**：归一化比对器（自造正负例）；CFG/支配树（手工构造图，含不可归约）；fallback 发射器（任意 CFG 必须产出可编译且语义等价的状态机）。
3. **语义回归**（移植原项目）：5 个差分执行用例 + 生成型用例（保留 `PYLUADEC_GENERATED_CASE_LIMIT`）+ 按键序列两个历史 bug 检查点（OptionMain 双 clamp、ConfigMain CIRCLE gate）。
4. **全语料 ratchet**：台账 diff 即回归测试本体。

里程碑（每个有可验证出口）：

| 里程碑 | 内容 | 出口 |
|---|---|---|
| M0 基建 | 仓库骨架 + uv + CMake 双字长 + golden 固化（迁移 Step 0-1） | 32 位下新 bridge 输出与 golden 一致 |
| M1 六四切换 | 迁移 Step 2 | 三道门通过；此后开发全在 64 位 |
| M2 保底闭环 | lift + CFG + fallback 发射器 + L3.0 比对器 + 台账初版 | 229 语料 100% 可编译输出；台账面板上线 |
| M3 结构化主干 | 支配树区域识别 + PC 认领审计 + 归一化阶梯 L3.1-k | 多数函数脱离 fallback |
| M4 表达式与美化链 | 证明门控内联 + 效应格三档语料标定 + pass registry + 首批美化 pass | 语义回归全绿 + 可读性对齐评估 |
| M5 长尾与插件 | confession 榜驱动补齐 idiom pass + L2 门 + 按键序列回归 | ~~达到/超越原项目 229 语料质量基线~~ → **重新划定为 ≥0.96（实测 0.968833）**，见 §2 决策表；「插件」一项随 pass registry 退役而作废（同表）。 |
| M6 交叉验证（实际执行的形态） | 前作 229 语料的双向利用：我们的仪器查它的缺陷；它的人工验证过的结构反哺我们的残差收口 | ~~继承 M5 让出的 `avg_score ≥ 0.997`~~ → **该门 2026-08-13 被整体撤下**（§2 决策表第二次修订行）。实际出口见 M6 spec §3 与 `tests/test_m6_exit.py`：观测数据覆盖全部叶子拒绝与 CAP 主导 proto、分歧队列逐条裁决、`L3` 不回退。收口实测（2026-08-14）：`L3` **1438/1478 唯一 / 1904/1944 处出现**，在前作已发布产物中确认 **6 个缺陷（4 个此前未知）**。 |
| M6+ 实验（可选，未启动） | GPU 提议器、lparser/lcode 插桩规则挖掘、Lua 5.2 摄入 | 按台账 L3 比例评估收益。**三项在 M6 均未开工**，随 M7 议程重新排序（`docs/runbooks/m3-backlog.md`「M7 agenda」）。 |

每个里程碑收尾走 superpowers 流程（requesting-code-review + verification-before-completion）。

## 8. 旧测试资产的转译原则

- `test_semantic_regressions.py`、`test_generated_semantic_cases.py`、`test_ir_structure_roundtrip.py`：直接移植（机制等价重写，断言语义不变）。
- `test_ir_pipeline.py`（86 例文本断言）：**不照抄断言**。每例转译为"对应函数在台账中达到 ≥L2 且非 fallback"的断言；其针对的字节码形态逐条登记为 idiom 清单，作为 M3-M5 的 pass backlog 输入。转译清单在 M2 台账上线后生成（届时有逐函数等级数据可对照）。
- `DEBUG_KEY_SEQUENCE_HARNESS.md` 两个行为检查点：转为固定语义回归（见 §7）。

## 9. 风险登记

| # | 风险 | 对策 |
|---|---|---|
| R1 | **效应模型粒度**：任何表读理论上可触发 `__index`；全当屏障则内联门永远关闭，输出退化为临时变量汤 | 效应格三档（strict / no-metamethod / trusting）在 229 语料实测内联率 × 语义回归矩阵，用数据定默认档；档位开关兼作调试二分工具 |
| R2 | **L2 空洞授证**：stub 环境下浅层路径即 trace 一致 | 覆盖率进徽章（L2@cov%）并纳入 ratchet；taint 盲区占比显式呈现 |
| R3 | **归一化比对器误拒/漏放**：做严则函数冤枉停在丑代码层，做松则等价性 bug 漏网 | 独立子模块 + 自造正负例充分测试；归一化逐级引入、各级单独论证健全性、版本化 |
| R4 | **proto 身份漂移**：反编译器改版导致嵌套 proto 切分变化，台账 diff 误判新增+删除 | 主键用归一化结构哈希（随内容走），不用文件路径/序号 |
| R5 | **golden 污染**：用新工具刷新基线会继承其 bug | golden 只在 Step 0 由旧 bridge + luac listing 双源产出，此后只读 |

## 10. 设计空间探索记录（ADHD 摘要）

- 发散帧：卸掉承重假设、敌对破坏者、3am 值班、审计员、速通玩家（5×6=30 想法，6 聚类）。
- 收敛短名单：先丑后美分层；分级认证台账 + ratchet；证明门控表达式 IR + debug 段 oracle；★双向 PC 认领纪律。
- 判定为陷阱：ensemble 赛马旧代码（拖旧包袱）；IR 参考解释器（重实现 VM 语义且自身需验证）；superoptimizer 作主路径（组合爆炸，仅配作插件）；端到端 seq2seq（无语义保证）。
- Provocation 留档：lparser/lcode 插桩自动挖掘逆模式表，可能大幅替代手写规则库——作为 M6+ 零风险实验。
