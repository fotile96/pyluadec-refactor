# M8 命名对齐：T0 普查与裁决记录（2026-08-18）

**任务**：`docs/reports/m8-handoff-naming-alignment.md`（T0–T3）。
本文件落盘 T0 的全部测量、不收敛清单的逐条裁决，与 T1 实装后的验收数字。
所有「现值」实测于 `3222d51`（proposal 通道收口树）之上的本任务接线。

**Partner 决策（2026-08-18，开工前一次问齐）**：
① 残余局部不做旧 `v\d+` 兼容模式；② `corpus/naming/` 布局与 name_map
入库（+生成器 job）；③ 改进名字（超出对齐）不排本期。

---

## 0. 启用前提复核（handoff 第 6 行要求，全部实测）

| 前提 | 实测 |
|---|---|
| `corpus/proposals/verify_proposals.py` | **9/9** 认证通过（handoff 写 8/8 是其 6fa03ab 时点值；通道后来加了第 9 份 proposal，以现测为准） |
| `grep -rc "__pld_" corpus/final/` 非零文件数 | **0** |
| A5 文件级字节同一（survey §8.2 归一化器） | **229/229** |
| 全套件（正确 env） | **1215 passed**（接线前基线） |
| `./scripts/ratchet_job.sh` | exit 0（baseline `72cb6a8`） |
| `git diff 43a8b66..HEAD -- src/pyluadec/verify/` | **0 行**（阶梯未被本任务触碰） |

## 1. 旧链路事实（T0a）

- **文本权威**：`post_process/stage1_output/`（229 文件）。
  `Zndnovel/lua_scripts/` = stage1 + `-- tr_line:N` 标记
  （实测 227/229 纯标记差异）+ 2 个下游补丁文件（`snr_common.lua`
  字体替换、`snr_s4_10_s.lua` 代码修复）。命名 harvest 以 stage1 为准。
- **报告只做交叉验证**：七份 apply 报告（scene/semantic 各含 refresh 轮、
  story_shared、story_helpers、crd_prefix）。报告合计 1248 条改名，
  与最终文本交叉验证 **892 条命中、3 条失配**（见 §4 裁决 A）。
- **branch_key 规则零触发**：工具里有该规则（≥3 次常量比较），但对本
  语料 0 次发货。handoff 第 1 节层 2 清单中的 branch_key 实际不存在。

## 2. 命名面分布（对 stage1 全量编译取 locvars，229 文件）

| 类 | 数量 | 处置 |
|---|---|---|
| main 层可读函数名 | **846** | 移植（层 1） |
| 参数语义名（454 `scene_id` + 454 `scene_title`） | **908** | 移植（层 2） |
| 旧自引用物化（`local NAME` 在函数体内，389 处，全部 card_* 族） | 389 | 不移植——我方 `local function` 糖 + upvalue 名线程自动跟随父行 |
| 残余：`v\d+`/`p\d+` 局部与参数、`i\d+`/`g\d+`、`arg`、`(for ...)` | 4046 局部 + 205 参数 + 285 编译器内部 + 33 main 层旧自动名 | 决策 ①：保留我方 `l<depth>_<reg>` |

## 3. 对齐构造（为什么不按寄存器号移植）

M6 已实测：旧文本重编译与原始字节码**从不满指令级同一**（229 文件
3903 处实质差异；`snr_s1_10_s.lua` 单文件 173 处）。寄存器分配两边不同，
locvar 槽位不能直接当寄存器号用。采用的构造：

- **函数名**：锚在 CLOSURE 指令的 **Bx 操作数**（= subproto 序号，两边
  同构——M6 tree parity 229/229 路径集全等）。旧编译里第 j 个 CLOSURE
  的目标槽上活着的 locvar 名 = 旧名；原始字节码里 Bx==j 的 CLOSURE 的
  目标寄存器 = 我方 `l0_<reg>`。同名 j ⇒ 同函数，全程不需要代码相等。
- **参数**：按位置。`numparams` 229/229 文件零失配（实测）。

**可移植率（口径：分母 = 旧文本中该类的全部名字）**：
函数名 **846/846**（0 槽冲突、0 坏锚、0 个我方未打印）；参数
**908/908**。合计 **1754 行**入 `corpus/naming/name_map.jsonl`。

## 4. 不收敛清单（逐条裁决）

**A. 报告 vs 文本（3 条）**：`snr_crd_102.lua` 的 crd_prefix 报告声称
改了 `card_s6s_110_hint_first/hint_retry/quiz_prompt`，最终文本中这
三个名字**不存在**（`grep -c hint` = 0；报告与文本同分钟落盘，多轮
互相覆盖的痕迹）。**裁决：文本为权威**（handoff §2 明示），报告记为
过期；表按文本。

**B. 移植 vs 重推（2 条）**：对我方产物跑派发规则（路径 B，341 个
`doScriptScene == "KEY"` 站点）与移植表（路径 A）对拍：**339 收敛**、
2 处分歧（`snr_e2_10_s.lua` reg3、`snr_s2_10_s.lua` reg7）。机制：
同一派发 KEY 出现两次（如 `"e2s_20"` 两个不同 title 的站点），旧工具
`_unique_name` 的消歧顺序与朴素首见规则不同（旧文本把裸名给了后见
站点）。**裁决：文本胜**——这些字符串是 translation_ir 的单元 ID，
对齐旧 ID 正是本任务的目的。另：505 个表名无派发站点（card_*、
dispatch/shared/helper 等），341 个站点 100% 有表名，0 个站点无表名。

**C. 旧产物 vs Zndnovel（2 文件）**：见 §1。命名不受影响，无表级动作；
迁移指南（T3）记为下游补丁注记。

## 5. 缺陷区与通道交集（P4）

6 个 M6 缺陷 proto（`snr_music:main_3`、`snr_common:main_76_2`/`main_75`、
`snr_mainmenu:main_7`、`snr_graphic:main_4`、`snr_memory:main_4`）+
路径级 intentional-edit（`snr_common:main_83`）：**与 1754 行命名面
交集为 0**（实测；那些 proto 的旧名全是 v/i 残余）。4 个 proposal 文件
（snr_common/snr_graphic/snr_mainmenu/snr_story_main）同样 **0 行**
——它们在我方 161 个有条目文件之外，旧文本里本就没有可读表面。
生成器仍带 flag 逻辑（`defect-zone`/`proposal-site`），表一旦演进，
`verify_naming.py` 的完整性检查保证 zone 行必须带 flag。
**T2 的单元映射同样 0 个缺陷区 flag**（实测：5 个缺陷文件在
translation_ir 里一个单元都没有——缺陷全在库文件，翻译单元全在
剧本/卡片文件），但映射器带同一 zone 判定，演进时自动生效。

## 6. T1 实装与验收（handoff §5 battery，全实测）

接线：`structure/naming.py`（加载器，加载时校验：标识符/关键字/
`l<k>_<r>`、`u<k>` 合成名冲突/`__pld_` 前缀）→ `emit/lua.py`
`Printer.local_name`（7 处合成点全部改道：声明、引用、子参数、
upvalue 名线程）→ `structured.py`（root 认证打印、proposal 轮、
hybrid 轮；认证 memo key 加入 naming 内容 token）→ `pipeline.
decompile_file` 自动装载 → `run_corpus`/`warranty_build` 接线。

| 验收 | 实测 |
|---|---|
| P1（survey §8.2 归一化器，`verify_naming.py`） | **229/229 字节同一** |
| 台账 | `git diff corpus/ledger.jsonl` **零字节**（重生成前后） |
| warranty 工件 | `git diff corpus/warranty.jsonl` **零字节**；选择 ours=229 |
| `__pld_` | 0 |
| A1/A2（套件） | 全绿；全套件 **1232 passed**（+17 个新测试） |
| ratchet | exit 0 |
| P2 对齐度 | 层 1 函数名 **846/846**、层 2 参数 **908/908** 在我方 final 与旧文本双侧同名出现（词边界匹配）；161 文件文本变化，68 文件不变 |
| P6 neuter | `verify_naming.py --tamper`：三守卫（P1/不动点/flag）全部「改坏→非零退出并点名」 |

**运行时防线（比守卫更强的一条）**：名字表走普通打印路径，任何改变
名字解析的改名（局部遮蔽体内引用的全局 ⇒ GETGLOBAL→MOVE、关键字 ⇒
编译失败）会直接改变编译产物、被认证阶梯的整树比对拒绝——坏名字只能
降级台账，不可能发货。套件内以
`test_a_shadowing_rename_is_refused_by_certification` 端到端钉住
（构造：改名局部辖域覆盖后续全局引用；注意在自身初始化器内的引用
按 Lua 作用域解析为全局、字节码不变——测试注释里记了这个反直觉点）。

**工程红线**：`structure/naming.py` 无 `re`（标识符检查手写）；
表内容只有 ASCII 标识符与文件名；tamper 演示对副本操作，
`/Users/fotile96/pyluadec` 与 `Zndnovel` 只读未动。

## 7. T2：text-unit 清单与单元 ID 映射

旧翻译资产 `post_process/translation_ir/`：**1003 个单元**（319
`card_*` + 498 `scene_*` + 186 `file__main`）。只读目录名（meta.json
含游戏文本，P5 不触碰）。与 846 行函数名的连接：

- **817/817** 名称键单元全部命中表行（**既有翻译资产 100% 可再锚定**）；
- 29 个表名无单元（无文本的调度/共享函数）；
- 186 个 `file__main` 单元：全局 `main` 函数，从原始指令流定位
  （回扫 SETGLOBAL "main" 的 CLOSURE 来源，Bx ⇒ proto 序号；
  229 文件实测每文件恰一个）。

产物：`corpus/naming/build_unit_map.py` + `unit_map.jsonl`
（见该目录 README）。**新单元 ID = 旧单元 ID**（对齐的本意），
坐标（file, proto_path[, reg]）与 flag 是增量价值。

与原 plan task 8 的形态差异：plan 的 per-vms-message 清单
（`{"id", "file", "proto_path", "pc"}`）在 handoff 中被改写为
「键改用对齐后的名字」+「映射表是核心工件，价值高于 inventory」。
消息级连续性不需要新工件：vms 消息号是常量池事实，字节同一
⇒ 消息集合同一，Zndnovel 侧 `build_ledger.py` 在新基座上重跑即得
（迁移指南 §5 的对账建议正是这么写的）。

## 8. 遗留与移交

- 决策 ③ 排期外的「改进名字」：改 `name_map.jsonl` 数据行 + 重跑
  再生成即可，成本一次 battery。
- 旧 `v\d+` 兼容模式（若未来要最大化文本 diff 亲和）：那是复活
  output surface v1 的决定，partner 已裁定不做。
- `snr_common.lua`（39 个旧 main 局部全为残余名，我方构造器折叠后
  main 打印 9 个局部）：两边都没有可读表面，无动作空间，记录在案。
