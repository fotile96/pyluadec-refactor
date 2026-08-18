# Handoff/Spec：命名对齐（旧 post_process 可读化产物 → 我方产物）——备用，通道落地后启用

**性质**：半 handoff 半 spec，controller（Fable 5，per /model）2026-08-18 起草备用。
**启用前提（硬性）**：`docs/reports/m8-handoff-proposal-channel.md` 的 A1–A7 全绿
（零 fallback、`__pld_` 归零、229/229 文件级字节同一、`verify/` 无 diff）。
接手第一件事就是**复核这组前提**；没绿就停，回去问 controller。
本文所有「现值」实测于 `6fa03ab` 时点——通道落地会重生成 `corpus/final/`，
引用前先重测（本仓库的头号教训：散文断言了没人量过的行为）。

**难度定位**：本任务**没有反编译层面的困难**（partner 原话），是数据工程 +
呈现层改造。需要的是纪律，不是洞察力。

---

## 1. 目标与价值结构（为什么做、做到什么程度算完）

**目标**：让我方 `corpus/final/` 的命名表面尽量对齐旧项目 post_process
可读化重命名后的产物（`/Users/fotile96/pyluadec/post_process/stage1_output/`，
其下游即 `/Users/fotile96/Zndnovel/lua_scripts/`），使翻译资产迁移的摩擦最小。

**价值结构（controller 实测，2026-08-18）**——对齐分三层，价值悬殊：

1. **顶层函数名**（约千个：`scene_s1s_10`/`scene_s1s_35_sel`、
   `scene_s1s_{shared,dispatch,helper}_vN`、crd 前缀）：**全部价值的大头**。
   旧翻译中间格式 `post_process/translation_ir/` 以函数为单元、
   **以重命名后的函数名做单元 ID**（实例：`card_100_s6s_60_sel_intro/`）——
   函数名对齐 = 翻译资产直接可再锚定。
2. **参数与少量语义局部**：`p0/p1 → scene_id/scene_title`、`branch_key`、
   `doScriptScene` 转发变量。规则少而明确，顺手做。
3. **残余局部**：旧产物自己也没给它们语义名（单个章节文件残留 335 处
   `v\d+`）。**建议保留我方 `l<depth>_<reg>` 方案**，只在迁移指南里给映射
   规则。若要做旧 `v\d+` 兼容模式（最大化文本 diff 亲和），那是复活
   output surface v1 表面的决定——**partner 决策点，不要自作主张**。

「算完」的定义在 §5 验收，核心是：对齐度是**被测量的数字**（逐类的
名字相等比例），不是一句「已对齐」。

---

## 2. 旧链路事实清单（controller 已勘察，直接用，出处齐全）

三个重命名器，全在 `/Users/fotile96/pyluadec/post_process/tools/`，
apply 报告在同级 `reports/`（`renames` 字典 = 现成的移植源）：

| 工具 | apply 报告实测 | 名字来源 |
|---|---|---|
| `rename_scene_locals.py`（363 行）| 450 renames / 23 章节文件 | **数据驱动**：`main` 派发块 `doScriptScene` switch 标签 → `scene_<sanitized_id>`（`_sanitize_scene_name`，行 49）|
| `rename_semantic_locals.py`（705 行）| 365 / 161 文件 | 启发式：`scene_` 函数的 `p0/p1`→`scene_id/scene_title`；`shared/dispatch/helper` 角色前缀（按调用方分类）；`branch_key`（≥3 次与常量比较且赋值 ≤3 次）；`doScriptScene` 转发变量 |
| crd 前缀轮（同工具另一配置）| 321 / 137 文件 | 卡片文件前缀 |

合计约 1136 个名字，三轮全部 0 例校验失败。旧校验 =
`load_from_source` canonical-proto 比对（opcode+常量），**弱于**我方的
字节同一——我们能用更强的门（§4 P1）。

**两个降低难度的关键事实**：
- 场景名所需数据在我方产物里**原样存在且字节精确**（实测
  `corpus/final/snr_s1_10_s.lua:2580`：
  `elseif doScriptScene == "s1s_10" then l0_0(doScriptScene, "オープニング")`）。
  所以第 1 层名字可以**移植**（从旧产物 harvest）也可以**重推**（对我方
  产物跑同一规则），两条路应收敛——收敛本身就是校验。
- proto 树 229/229 文件 1:1 对应（M6 parity 普查），顶层函数名按
  `(file, proto_index)` 移植无歧义。

**警惕**：apply 报告可能只是多轮中的一轮。最终依据是
`stage1_output/` 与 `Zndnovel/lua_scripts/` 的**文本本身**，报告只做
交叉验证。两个旧目录都是**只读**的（Zndnovel 整树、`/Users/fotile96/pyluadec`
整树，一个字节不许动）。

---

## 3. 任务序列（T0–T3，串行）

### T0：harvest + 对照表 + 可移植率测量

产出一份入库数据文件（建议 `corpus/naming/name_map.jsonl`，布局你定）
+ 一份报告。内容：
- 从 stage1_output/Zndnovel 文本提取全部命名实体，键为
  `(file, proto_index_path, kind, position)`（kind ∈ 顶层函数/参数/局部）；
- 与我方产物建立对应，逐类实测：可无歧义移植的比例、需重推的比例、
  两条路（移植 vs 重推）不收敛的清单（逐个人工裁决并记录理由）;
- **6 个缺陷修复区**（M6 确认的 6 个 real-bug，见
  `docs/reports/m6-cross-corpus.md`）单独标注：那些区域的旧名与旧翻译
  单元锚定在错误代码上，映射表必须带 flag，否则下游会把旧翻译回填到
  修复后的新代码上而不自知。

### T1：命名 pass 实装

- 形态：printer 的**输入名字表**——打印时查表选名，查不到落回
  `l<depth>_<reg>`。**不是文本后处理**（「绝不回读自己发出的字符串」
  照旧；`src/pyluadec/{...,emit,structure}` 的 `re` 禁令照旧——注意
  harvest/生成器脚本在 `scripts/` 或 `corpus/naming/` 下，**可以**用 re，
  禁令只覆盖 src 下那些模块，别把两件事搞混）。
- 名字表是入库数据 + 生成器 job + 不动点（`ledger.jsonl` 的既有纪律
  照搬：只由生成器整体重生成，禁止手编单行）。

### T2：text-unit inventory（原 plan task 8，键改用对齐后的名字）

逐文本单元 `(新函数名, 我方坐标)`，并产出**旧单元 ID ↔ 新单元 ID
映射表**——这张表是翻译资产迁移的核心工件，价值高于 inventory 本身。

### T3：迁移指南（原 plan task 9）

引用 T0/T2 的表。Zndnovel 侧受影响设施先读后写指南（partner 已定的
方式：整体修改面可控 + 出具指南供那边自行调整）。

---

## 4. 性质要求（机制自选，性质缺一不可）

- **P1（完整守卫，最强的一条）**：对每个文件，命名 pass 前后
  `luac_sz4 -s` 产物**逐字节相同**。名字不进 strip 后的字节码，所以
  碰撞、全局遮蔽（局部改名撞上作用域内全局引用会翻转 GETGLOBAL→MOVE）、
  关键字冲突，任何一种都会破坏字节同一而被这一条兜住。它同时蕴含
  「台账字节不变」（呈现层变更的既有定义）与「229/229 文件级字节同一
  保持」。**不要**只做旧项目那种 canonical 比对——我们有更强的门就用
  更强的。
- **P2（对齐度可测）**：报告必须给出逐类数字（第 1/2 层名字与旧产物
  逐个相等的比例、不收敛清单长度），并把口径连分母写清（本仓库教训：
  引用比例必须连分母一起引）。
- **P3（先对齐后改进，两个 pass）**：T1 只许对齐，**不许顺手起更好的
  名字**——否则 P2 没有定义。改进名字是 T1 验收后的另一个活，届时改
  名字表数据行即可，成本极低。
- **P4（缺陷区标注）**：映射表里 6 个修复区的条目必须带 flag 并在
  迁移指南里单独成节。
- **P5（红线照旧）**：名字表、inventory 都会含游戏文本派生内容，读写
  一律 bytes 纪律按既有规矩；诊断文本不含语料内容。
- **P6（新守卫自带 neuter 证明）**：名字表不动点、P1 断言、映射表
  flag 完整性——每个新守卫演示一次「改坏一个字节 → 非零退出并点名」
  （先例：`corpus/proposals/verify_proposals.py` 的 tamper 演示）。

---

## 5. 验收 battery

```bash
# 前提复核（通道遗产未回退）
uv run python corpus/proposals/verify_proposals.py            # 8/8
grep -rc "__pld_" corpus/final/ | grep -v ":0" | wc -l        # 0
# P1：命名前后字节同一（实现为守卫后一条命令可跑，非零退出点名文件）
# P2：对齐度报告数字（逐类、带分母）
# 台账与套件
uv run python scripts/run_corpus.py && git diff --stat corpus/ledger.jsonl   # 无 diff
PYLUADEC_CORPUS_DIR=... PYLUADEC_PRED_CORPUS_DIR=... uv run pytest
./scripts/ratchet_job.sh                                      # 0 降级
```

预期钉子动向：`corpus/final/*.lua` 大量文本变化（名字），但
`corpus/ledger.jsonl`、`footprint_ratio`、warranty 的 `t_hist`（T 因子
只看字符串常量，与局部名无关）**都应不动——逐一实测确认，不要推理**。
`tests/test_m7_exit.py` 的正则扫 `corpus/final/`（字面量普查），改名
不应影响其计数——同样实测。

## 6. 工作方式提要（完整版见 proposal-channel handoff §4，此处只列增量）

1. 动手前存三份基线：全套件、`run_corpus` 输出、`corpus/final/` 的
   目录哈希。名字表每长一段就重跑 P1，别攒到最后。
2. T0 的「不收敛清单」逐条裁决要落字（哪个为准、为什么），它就是
   将来 partner 与 Zndnovel 侧问「这名字怎么来的」时的答案。
3. 提交粒度：harvest 数据 / pass 代码 / `corpus/final` 重生成，分开
   提交；重生成的提交信息里写 P1 与对齐度数字。
4. 升级路径：发现旧名与我方结构对不上且原因不明的（既不是缺陷区
   也不是移植歧义），记录并报 controller——那可能牵涉两边 emitter 的
   语义差异，属于「反编译层面的事」，不在本任务内自行处置。

**Partner 决策点汇总（开工前问一次，别打断多次）**：
① 残余局部要不要 v-scheme 兼容模式（controller 建议不要）；
② `corpus/naming/` 布局与 name_map 是否入库（controller 建议入库+生成器 job）；
③ 改进名字（超出对齐）的 pass 要不要排进本期。
