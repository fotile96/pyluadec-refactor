# pyluadec 重构总体方案设计

- 日期：2026-08-09
- 状态：已经用户逐节确认（5 节），待实施计划（writing-plans）
- 方法：superpowers brainstorming + ADHD 并行发散（5 帧 × 6 想法 → 打分聚类 → 3 支深化）

## 1. 背景与目标

本仓库从头重构 `/root/pyluadec`（Lua 5.1 字节码反编译器）。语料为 229 个 PSP 游戏 bytecode（vanilla luac 5.1.5 输出；header 表明 sizeof(size_t)=4，其余字段与 LP64 一致，lua_Number 为普通 double）。

> **2026-08-10 实测更正**：起草本 spec 时假设语料"未 strip"，据此把 debug 段（lineinfo 单调性、locvars 作用域 PC 区间）当作白送的语句边界与变量命名 oracle（见 §4 ④express、§10 收敛短名单）。**该假设不成立**——229 文件 / 1944 proto 的 lineinfo、locvars、upvalue 名称全为空，`source` 为占位符 `=?`。影响：所有局部变量名必须合成；语句边界必须由控制流与寄存器生命周期推导；§4 中"debug 信息只作命名/物化 hint"的规则保留（对将来自编译的测试用例仍生效），但对本语料永不触发。摄入层无损保留这些字段的能力仍是正确设计（新编译的文件确实带 locvars，且是回归测试的一部分）。原项目的架构级教训见根目录 CLAUDE.md（无表达式 IR、CFG 未被结构化使用、ad-hoc 特例堆积核心函数、文本断言测试）。

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

pass 插件协议：

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
| M5 长尾与插件 | confession 榜驱动补齐 idiom pass + L2 门 + 按键序列回归 | 达到/超越原项目 229 语料质量基线 |
| M6+ 实验（可选） | GPU 提议器、lparser/lcode 插桩规则挖掘、Lua 5.2 摄入 | 按台账 L3 比例评估收益 |

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
