# Handoff：propose-and-certify 通道接线（controller → M8 工作 session，2026-08-18）

**你接手时的树**：`phase8-m8-zero-doubt-handoff` @ `5f56b83`。
**前情三份文档，按此顺序读**：
1. `docs/reports/m8-strategy-survey-fable5.md` —— 立项依据；§4.4 是机制草图，
   **§9 是你最需要的**：八份 proposal 的逐 proto 编辑说明、拼接测量、对
   petition pack 各决定的影响。
2. `corpus/proposals/README.md` + `verify_proposals.py` —— 你的输入数据与
   它的判定驱动（当前 8/8 pass、已做 neuter 证明）。
3. `docs/reports/m8-petitions.md` —— 历史决策记录。注意其中 Decision B/
   Disposition C 的结论已被 §9.3 **超越**（B1 不再是任何行的必经之路、
   `main_74_18` 的 hold 解除），读它是为了理解八个 proto 的机制归属，
   不是为了继续执行它的建议。

**partner 已批准的事**：propose-and-certify 通道立项（2026-08-18，原话
「我同意把 propose-and-certify 通道立项」）。手工演示已由 controller 推到
8/8，**你的任务是接线，不是搜索**——没有任何一个 proto 还需要你去猜源码。

---

## 1. 任务的性质：一句话与一组验收断言

把 `corpus/proposals/` 里的八份已认证源码接进发射管线，使它们成为产物。
**验收断言现成且全部可机器判定**（接线完成的定义就是这组数字，不多不少）：

| # | 断言 | 当前值 → 目标值 |
|---|---|---|
| A1 | `corpus/ledger.jsonl` 非 `L3` 行 | 15 → **0** |
| A2 | `shipped == "fallback"` 的 occurrence | 15 → **0** |
| A3 | `corpus/final/` 里 `__pld_` 出现次数 | >0 → **0** |
| A4 | 全部 229 文件 `footprint_ratio` | 4 文件 >1 → **全部 1.0** |
| A5 | 229/229 文件级字节同一（mod `linedefined`/`lastlinedefined`）| 225 → **229**（survey §2/§8.2）|
| A6 | `scripts/ratchet_diff.py` 对基线（`ratchet_job.sh` 默认 `72cb6a8`）| — → **只升不降** |
| A7 | `git diff src/pyluadec/verify/` | — → **空** |

A7 值得单独强调：这次接线**一行都不该碰**比较器、阶梯、`LADDER_VERSION`、
`compare_protos`、`structural_hash`、`key_disagreements`。proposal 走的是
认证的正门，门本身不动。如果你发现自己在改 `verify/`，停下来——那说明
设计走岔了，或者你发现了一个 controller 没预见的问题，先记录再升级。

---

## 2. 需求以「性质」陈述（机制自选，但性质缺一不可）

本仓库有过多次教训：plan 里写死的机制到实现时不可满足（见 MEMORY
「prescribe properties, not mechanisms」）。所以下面给的是**必须成立的
性质**；§3 的机制草图只是可选起点，你可以推翻它，只要性质全部保住。

- **P1（认证门不变式，最高优先）**：产物中的每个 proto，要么正是某次
  认证实际编译并逐字段比对过的那串字节，要么由语义精确的 fallback 发射
  并 confess。proposal 文本**不例外**：它必须经与现有认证同一扇门
  （同 oracle、同阶梯、同 strip 判定）后才可进产物；任何拼接/改名步骤
  的错误必须被认证挡下而不是发货。
- **P2（provenance 诚实）**：台账必须能区分「reconstructor 产出的结构化
  文本」与「proposal 产出的文本」。等级（proof record）可以同为 `L3`
  ——两者都被同一门证过——但文本来源是事实，必须可查。
- **P3（ratchet 语义）**：`ratchet_diff.py` 必须理解新 provenance。
  最低要求：`proposal → fallback` 是降级（exit 1）；`fallback → proposal`
  是升级；`structured ↔ proposal` 的相对序你定，但要在 docstring 里写明
  理由并加 `tests/test_ratchet_diff.py` 的失败用例（该套件的存在意义
  就是证明工具能失败，每种 kind 一个点名用例）。
- **P4（proposal 不是回归遮罩）**：proposal 只许解决「源码形状复原」，
  绝不许用来掩盖 emitter 的**新**回归。可执行形式：proposal 集合的枚举
  被钉住（新增/删除 proposal 都要动一个明示的清单），且若某个此前由
  reconstructor 认证的 proto 开始需要 proposal 才能过，那是降级（P3 的
  `structured → proposal` 序至少要让 ratchet 能看见这件事）。
- **P5（红线继续）**：proposal 文件含游戏文本，读它**一律 bytes**
  （`read_bytes`，driver 已是如此）；`ingest`/`lift`/`verify` 一个字节
  不解码；诊断文本（refusal_reason 等）不得包含 proposal 内容。
- **P6（不动点与生成纪律）**：`corpus/ledger.jsonl` 仍只由
  `scripts/run_corpus.py` 整体生成，仍是自身的不动点；proposal 入库、
  内容确定，所以不动点性质自动保持——但要实测一次，不要推理。
- **P7（工程守卫不放松）**：`src/pyluadec/{...,emit,structure}` 的 `re`
  禁令照旧（这对你有实际影响，见 §3 的坑 H1）；发射层「绝不回读/后处理
  自己发出的字符串」照旧——proposal 是**输入数据**不是自己发出的字符串，
  对它做词法处理不违反该纪律，但要在 docstring 里把这个区分写清。

---

## 3. 机制草图与已知的坑（草图可推翻，坑不会消失）

### 草图（survey §4.4 的展开）

消费点在 `structure/structured.py` 的 chunk 装配层：某 CLOSURE 站点的
proto 自身认证失败时，fallback 之前先查 proposal 注册表；有则以 proposal
文本为候选走认证，`L3` 才内联。两条可选路线：

- **路线 a（逐站点）**：proposal 单独认证（driver 现在做的事），然后其
  函数体内联进父文本。优点：与 hybrid 机制同构；缺点：需要 upvalue 改名
  （坑 H1）。
- **路线 b（整树重认证）**：站点全部填上 proposal 后，对 root 跑一次
  完整的 `certify_proto(is_chunk_root=True)`——树上不再有被排除的子树，
  root 逐字段比对整棵树。**优点：改名或拼接的任何错误都被这一步兜住
  （P1 的最强形态），且台账各行自然全 `L3`**。缺点：与现有 hybrid memo
  的交互要想清楚。
- controller 倾向 b 为主、a 为诊断，但这是倾向不是指令。

### 坑（每一条都是 controller 实测或核对过的）

- **H1（upvalue 改名 without `re`）**：proposal 以 wrapper 形式存
  （`local u0, ...` + `return function(...)`），内联时 `u<i>` 要换成
  外围实际局部名。engineering-practice 测试静态禁止这些模块 import `re`
  ——写一个边界感知的手工扫描器（`u` + 数字 + 非标识符字符），或者换一种
  不需要改名的装配方式。controller 的拼接演示用了 regex，**那是 /tmp 里
  的演示代码，不是给你抄的**。
- **H2（upvalue 捕获序）**：内联后闭包的 upvalue 索引由**首次词法引用**
  定序。八份 proposal 的体都来自打印器（`code` 字段与原始逐字相同），
  首用序必然单调，所以按原索引升序改名即正确——这个论证在 survey §9.2，
  内联实现完成后仍应对四个文件各跑一次整文件字节比对来确证（A5 顺带
  就是这件事）。
- **H3（strip 判定）**：候选编译的 strip 模式必须继续走
  `carries_debug(original)`（`predcorpus` 曾为此付过 260 个伪失配的
  代价）。driver 已是如此；接线时别另写一份。
- **H4（`main_24`/`main_25` 的连带记账）**：`main_24_0/1`、`main_25_0..3`
  六个 occurrence 的行本身已是 `L3`，接线后只有 `occurrences[].shipped`
  翻转；`main_25` 行是继承拒绝，八叶落地后应自动转 `L3`。若它没转，
  不要去「修」它——那说明装配层还有你没看见的失配，去看 mismatch。
- **H5（memo cache 键）**：`certify_proto` 的进程级 memo 以 proto 内容 +
  oracle 身份为键。proposal 认证结果如果进同一个 cache，键必须把
  「是否用了 proposal、用的哪一版」纳入，否则编辑 proposal 后同进程内
  会拿到陈旧判决。最省事的做法是 proposal 认证不进那个 cache——先测量
  它的耗时（8 次 `luac` 子进程，估计毫秒级），确认省这点钱不值得引入
  键风险。**测了再决定，别拍脑袋**（这句是本仓库的第一戒律）。

### 记账蔓延清单（每一项都有现值，改动都要「测量→更新钉子」）

| 对象 | 现值 | 预期动向 |
|---|---|---|
| `tests/test_footprint_gate.py::RATIOS` | 4 文件 {1.1555, 1.9509, 3.5598, 1.6956} | 全部 1.0（钉子跟随现实，非放松——方向单调向下）|
| `tests/test_m7_exit.py` 盒模型钉 | `{"snr_common.lua": 3, "snr_story_main.lua": 2}` | `{}`（该测试 docstring 说钉子防「静默增长」；归零是它盼着的方向，改钉值时把这句话也更新）|
| `tests/test_ledger.py` 巧合钉（fallback occ == 非L3 occ）| 15 == 15 | 0 == 0，巧合平凡保持；实测确认而非假设 |
| `tests/test_m3_exit.py` 行内耦合 | fallback ⟺ confession ⟺ shipped | 若引入新 shipped 值，耦合断言要扩展成三值完备 |
| `corpus/warranty.jsonl` | snr_common 等 4 文件 `t_hist` 含 `T-` | 重生成（`warranty_build --all`，需双语料环境变量）；proposal-shipped = 认证文本 ⇒ T 按内容分级。`t_grade` 的 shipped-first 逻辑要认识新 provenance——这是 M7 task 2/11 两轮返工的老坑，改前把 §1 的修订史读一遍 |
| `scripts/ledger_dashboard.py` | 直方图 | 若加 provenance 字段，面板顺手加一列 |
| runbook | 无通道章节 | `structured-pipeline.md` 加一节；「What is left」census 归零后改写为指向 proposal 机制 |

---

## 4. 建议的工作方式（partner 要求多说的部分）

这些不是客套，每一条背后都有本仓库付过的具体学费。

1. **接线前先跑三个基线并存档输出**：全套件（双语料环境变量）、
   `verify_proposals.py`、`ratchet_job.sh`。你改完之后的每一个数字都要和
   这三份存档比。M6/M7 多次返工的根源是「改完才发现起点数字没记」。
2. **一次只动一层，每层出口做一次台账重生成 + `ratchet_diff`**。预期的
   健康轨迹：接线中间态可以出现「部分文件翻转」，但**任何时刻**都不该
   出现降级。一旦 ratchet 报降级，当场停下修复，不要「先接完再说」——
   M8 tasks 4/5 战役能保持 0 降级，靠的就是这个节奏。
3. **每一句写进报告/docstring 的行为性陈述，先测后写**。这是 M5→M7
   连续三个里程碑的头号缺陷（「散文断言了没人量过的行为」，M6 有 9 个
   fix 提交全是在修上一轮写下的假句子）。特别提防最高级词：唯一/总是/
   全部/从不——每个都要么带一次测量，要么改写。引用比例连分母一起引。
4. **新守卫必须自带 neuter 证明**。你会新增：proposal 枚举钉、ratchet
   新 kind、A1–A5 出口断言。每一个都要演示「改坏一个字节 → 非零退出并
   点名」，像 `verify_proposals.py` 已经做的那样（篡改 `main_24` 一个
   常量 → exit 1 点名）。四轮评审从绿树里删掉守卫的历史（MEMORY
   「guards must be proven load-bearing」）不要再加一轮。
5. **套件预算要归因**。新增耗时里，proposal 认证（约 8 次 luac）与
   A5 的整文件比对（229 次编译——若复用 `run_corpus` 已产出的编译结果
   则近零）都属于形式化验证拨款；给出实测秒数和归属，别写估计值。
   A5 若做成独立 job 而非套件成员，按 CLAUDE.md 的 out-of-suite 四条件
   办（有名字的家、写明触发时机、一条命令非零退出点名、最近一次运行
   有落点）。
6. **提交粒度**：机制代码 / 台账翻转 / 钉子更新分开提交，台账翻转的
   提交信息里写 ratchet_diff 的升降数字。台账**永远**由
   `run_corpus.py` 生成后整体提交，禁止手编（老规矩，但值得重复，
   因为这次的诱惑特别大——你知道目标值是什么）。
7. **卡住的升级路径**：如果某个文件的整树重认证怎么都差几个字节，
   先用 controller 的工作流自查（survey §9.1：`_print_proto_body` 出
   近失配文本 → 并排反列 → 定点看）；如果失配出现在 proposal 覆盖
   **之外**的区域，那可能是新发现，记录进报告并告诉 controller，
   不要为了赶 A1–A5 去改 proposal 掩盖它（P4）。
8. **不要顺手做的事**：命名 pass、text-unit 清单、迁移指南（plan
   tasks 7–9）都不在本次接线范围内；A1–A5 全绿、文档收口后先停，
   让 controller/partner 看一眼再进下一段。范围蔓延的修复成本在这个
   仓库的历史上从来高于等待成本。

---

## 5. 一份可以直接抄的验证 battery（接线完成时全部跑一遍）

```bash
export PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/script_to_decompile
export PYLUADEC_PRED_CORPUS_DIR=<Zndnovel/lua_scripts 检出>

uv run python corpus/proposals/verify_proposals.py          # 8/8, exit 0
uv run python scripts/run_corpus.py                          # 229/229, 台账重生成
uv run python scripts/ratchet_diff.py /tmp/base.jsonl corpus/ledger.jsonl  # 只升不降
uv run pytest                                                # 全套件
./scripts/ratchet_job.sh                                     # 三道门
# A3/A5 的临时判定（正式形态由你落成守卫）：
grep -rc "__pld_" corpus/final/ | grep -v ":0" | wc -l       # 0
# 整文件字节同一：survey §8.2 的归一化器，229/229
```

预期台账终态（供对账，不是钉死——以你的实测为准并写进报告）：
1478 行全 `L3`、1944 occurrence 全 structured 系 provenance、
`refusal_reason` 全 null、`confessions` 全空。若与此有任何出入，
每一处出入都要在报告里给出指令级解释。

---

*Controller: Fable 5（per /model；会话 env 块自称 Opus 5，出入已在
survey 出处节记录）。本文所有现值均实测于 `5f56b83`。*
