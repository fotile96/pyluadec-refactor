# Review：propose-and-certify 通道接线（controller 复核，2026-08-18）

**被审对象**：`43a8b66..44a6098`（6 个提交），分支 `phase8-m8-zero-doubt-handoff`。
**审查依据**：`docs/reports/m8-handoff-proposal-channel.md` 的 A1–A7 与 P1–P7。
**裁决：接线成立，可以合并**——七条验收断言全部由 controller **独立**测量为绿，
北极星门（229/229 文件级字节同一）达成。有 **3 个 Important**、**3 个 Minor**，
其中 Important-1 是一条「文档声称、代码未实施」的不变式，已用实验触发。
三条 Important 都不改产物，修完台账应字节不变。

Controller: Fable 5 起草期 / Opus 5 复核期（会话中途 partner 手动 `/model` 切换；
本文的全部测量在切换后执行）。

---

## §1 独立复核的验收（全绿）

不采信被审方的数字，逐条自测（命令见 §5）：

| 断言 | controller 实测 |
|---|---|
| A1 非 `L3` 行 | **0**（1478/1478 `L3`）|
| A2 fallback occurrence | **0**（`structured` 1929 / `proposal` 15）；`confessions`、`refusal_reason` 全空 |
| A3 `corpus/final/` 的 `__pld_` | **0 个文件** |
| A4 footprint | **229/229 恰为 1.0** |
| A5 文件级字节同一（mod `linedefined`/`lastlinedefined`）| **229/229**（用 survey §8.2 的归一化器，非被审方的实现）|
| A6 ratchet vs `72cb6a8` | **22 升 / 0 降** |
| A7 `git diff src/pyluadec/verify/` | **0 行** |

附加实测：全套件 **1214 passed / 73.88s**（双语料环境变量）；
`./scripts/ratchet_job.sh` 三道门 exit 0；`verify_proposals.py` **9/9**；
`corpus/warranty.jsonl` **1944 occurrence 全 `T3`**（接线前 snr_common 含
`T-` 12 / `T2` 3）；台账 `hybrid` 标志全 `False`。

### 1.1 值得表扬的两处工程判断

- **整树零排除比对**（`_proposal_round`）比 handoff §3 controller 倾向的
  「逐站点内联 + 诊断」更强：任何拼接/改名错误都被同一道门挡下，是 P1 的
  最强形态。
- **深度 2 站点的前缀遮蔽 bug 是他们自己测出来并修掉的**：wrapper 把局部
  拼作 `l1_*`，在 depth-2 站点未 shift 时 `l1_0` 会遮住 `u0` 改名后的标识符，
  把捕获静默变成自引用（三处站点的 `nups` 失配为证）。修法（`l<k>_` 前缀
  按站点深度平移）与证据都写进了 runbook。

### 1.2 controller 自身文档的一处更正

`docs/reports/m8-strategy-survey-fable5.md` §1.1 把 `snr_common:main_25`
记为**继承拒绝**（引自 `m8-petitions.md`，当时已标注「未独立重导」）——
**这是错的**。本次实测：给 `main_25_4` 装上 proposal 后重印 `main_25`，
仍失配，首处分歧在 **pc 1 `NEWTABLE 0 0 2` vs 我方 `0 0 3`**，即
**自有拒绝、K1（NEWTABLE 提示位）族**。

因此第 9 份 proposal **必要且诊断正确**，`corpus/proposals/README.md` 的
「K1 折叠自有拒绝」准确；handoff 坑 H4 要求的「不要去修它，去看 mismatch」
被正确执行。**pack 与 survey 各错一次，被审方的测量纠正了两者。**

---

## §2 Important（建议合并前处置）

### IMP-1 P4 的不变式在代码里不存在；`sites` 是死参数

**事实**。`structured.py::_proposal_round(root, sites, proposals)` 的函数体
**从不引用 `sites`**，把完整的 `proposals` 字典交给
`_print_proto_body`，而 `emit/lua.py::closure_parts` 对字典里**每一个**
出现的 `child_path` 都拼接。调用方算出的 `refusers` 只用于
`shipped_pr` 的**记账**，不参与**文本生成**。

**文档三处声称相反**，且措辞是「结构性保证」：
- `structure/proposals.py` 模块 docstring：「the registry arm sits AFTER the
  reconstructor text in `closure_parts`, so a proposal cannot mask a
  reconstruction that would have succeeded」——顺带一提，该 arm 在代码里位于
  重建器递归**之前**，所以这句连位置都说反了；
- `structured.py` 提案层注释：「Only refusers consult proposals」；
- runbook 新节：「print the tree with proposal bodies at the **refusing**
  sites only」。

**触发实验**（snr_common；`main_0` 由重建器认证 `L3`；给它一份仅多一行
Lua 注释的 proposal——注释对 strip 后的字节码不可见）：

```
chunk certified at rung: 1
ledger provenance for main_0: structured        <- 台账说重建器
shipped text carries the proposal's marker: True <- 文本实际来自 proposal
```

**后果**（两条，互相咬合）：
1. **P2 provenance 记错**：proposal 产出的文本被记为 `structured`。
2. **P4 的守卫失效**：`ratchet_diff.py` 的 `proposal-mask` kind 正是为
   「proposal 遮蔽了本来能工作的重建」而建，但它读的是台账的 `shipped`，
   而台账在这种情形下**永远写 `structured`**，所以该 kind 在它唯一存在
   理由的场景里**不可能触发**。反方向（重建器退化、proto 变成拒绝者）
   仍能被看见——只有「proposal 静默覆盖一个仍然工作的重建」这一半是盲的。

**今天是潜伏的**：9 份 MANIFEST 全是各自文件里的拒绝者，两个集合重合，
A5 229/229 证明发货文本正确。这是缺陷而非事故。

**修法**：把传给打印器的字典先按 `sites` 过滤（一行），或删掉 `sites`
改由调用方传过滤后的字典；补一个用例：给一个 `L3` proto 挂 proposal，
断言它**不**被拼接（可复用本节的标记注释手法）；三处文档改写成
「保护来自调用方的 refusers 过滤」，并删掉那句位置说反的话。

### IMP-2 两条常驻语义探针悄悄不再覆盖发货文本

**事实**。`pipeline.decompile_file` 没有接 proposals
（`decompile_chunk` 接了，`decompile_file` 仍是 `decompile_chunk(ingest(path))`）。
而 `scripts/probe_behaviour.py`（L1.75 行为探针）与
`scripts/probe_global_state.py`（L1.5 全局状态探针）**都**经
`decompile_file` 取我方文本。

**实测**：

```
snr_graphic.lua: decompile_file == corpus/final?  False
   decompile_file 含 __pld_: True | 发货文本含: False
snr_lib.lua:     decompile_file == corpus/final?  True
```

即那 4 个受通道影响的文件上，**两道具名的语义门验证的是已经不发货的文本**。
`decompile_file` 作为公开 API 也与发货管线不一致了（`warranty_build.py`
改用了 `decompile_chunk`+proposals，探针没改）。

**严重性**：今天不构成正确性缺陷——发货文本与原始字节码逐字节相同，
比 fallback 文本更安全。问题是**一道门的覆盖面变窄却没有任何记录**：
本次改动的文档（提交信息、runbook 新节）里 `probe` / `decompile_file`
**零提及**，说明这不是一个被权衡后作出的决定。

**修法**（二选一，都要落字）：把 proposals 接进 `decompile_file` 并**实测**
探针结果（发货文本与原始字节码同构，预期收敛；若有钉子因此变
`gone`，按 M6 task 12 的先例删钉并记录）；或明确写下「探针刻意跑重建器
基线以保留对重建器本身的观测力」的理由，写进两个探针脚本的 docstring。

### IMP-3 五个 neuter 证明里四个是同义反复

**事实**。`tests/test_proposal_channel.py` 的四个 `*_neuter_*` 用例从不调用
它们声称保护的门：`test_a2_neuter_a_doctored_ledger_fails_both_gates` 在本地
复制的 rows 上改一行再断言 `doctored != []`；`test_a3_neuter_a_planted_marker_fails`
断言 `b"__pld_" in (sample + b"__pld_R[0] = 1\n")`；
`test_a4_neuter_a_doctored_ratio_fails` 改字典再断言改动可见；
`test_neutering_the_manifest_pin_fails` 的函数体是 `assert len(P.MANIFEST) == 9`，
而它的 docstring 描述的是「在磁盘上放一个不在 MANIFEST 里的 stray 文件」。

**证明**（照那份 docstring 实际做一次）：

```
$ cp corpus/proposals/snr_common/main_24.lua corpus/proposals/snr_lib/main_0.lua
$ uv run pytest tests/test_proposal_channel.py -k manifest
FAILED test_manifest_matches_the_committed_files      <- 真钉子红了（承重）
1 failed, 1 passed                                    <- 「neuter 证明」照样绿
```

**门本身是承重的**（上面这次实验就是证据），**证明是装饰性的**。这正是 M7
IMP-1 与 MEMORY「guards must be proven load-bearing」记录的那一类：假证明
比没有证明更坏，因为它让后来的评审停止检查。

**修法**：照 `corpus/proposals/verify_proposals.py` 的先例——改坏真实产物的
**副本**（`tmp_path`），调用门自身的谓词，断言它红**并点名**。四个各一次。

---

## §3 Minor

- **MIN-1**：`structure/proposals.py` 的 `MANIFEST` 注释写「8 leaves …
  (8/8 at the wiring tree)」，而元组是 **9** 条、驱动实测 **9/9**。同一文件
  里的测试还写着 `assert len(P.MANIFEST) == 9`——代码知道是 9，注释说 8。
- **MIN-2**：`ratchet_diff.py` 的摘要行打印
  `64 occurrence(s) fallback -> structured`，实测拆分是
  **49 `fallback→structured` + 15 `fallback→proposal`**（计数对、标签错）。
  三值词表既然进了判定，也应进摘要。
- **MIN-3**：`tests/test_ledger.py` 删去了 `assert reasons`（合理：该人群已空，
  且写了注释）。但其后的 `for r in reasons` 循环现在是构造性空转，值得在注释
  里点明「本断言当前为空转，一旦有新 refusal reason 发货即自动恢复」——
  现有注释说了前半句，没说它已经不是活检查。

---

## §4 处置建议与顺序

1. **IMP-1**（半小时量级）：一行过滤 + 一个用例 + 三处文档改写。
2. **IMP-3**（半小时量级）：四个 neuter 重写为真实篡改—跑门—点名。
3. **IMP-2**：先做**测量**（接上 proposals 后探针输出如何），再据实择路。
4. MIN-1/2/3 顺手。

三条 Important **都不改产物**：修完重跑 `verify_proposals.py` 与
`ratchet_job.sh` 即可，`corpus/ledger.jsonl`、`corpus/final/` 应字节不变
（IMP-2 若选择接线，`corpus/final/` 仍不变——变的是探针读到的文本）。
**请以实测确认这句话，不要推理。**

---

## §5 复现命令

```bash
export PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/script_to_decompile
export PYLUADEC_PRED_CORPUS_DIR=/Users/fotile96/Zndnovel/lua_scripts

# A1/A2/A3/A4：读提交产物
python3 -c "..."                         # 见 §1 表；ledger/warranty 直接统计
# A5：survey §8.2 的归一化器逐文件比对   -> 229/229
# A6
git show 72cb6a8:corpus/ledger.jsonl > /tmp/base72.jsonl
uv run python scripts/ratchet_diff.py /tmp/base72.jsonl corpus/ledger.jsonl
# A7
git diff 43a8b66..HEAD -- src/pyluadec/verify/ | wc -l    # 0
# 套件与三门
uv run pytest -q                          # 1214 passed / 73.88s
./scripts/ratchet_job.sh                  # exit 0
uv run python corpus/proposals/verify_proposals.py        # 9/9

# IMP-1 触发实验：给一个 L3 proto 挂带注释标记的 proposal，
#   emit_certified_chunk(root, {**real, "main_0": marked})
#   -> proposal_rung 1；"main_0" not in proposal_paths；out.source 含标记
# IMP-2：decompile_file(C/"snr_graphic.lua").source 含 __pld_ 且 != corpus/final
# IMP-3：放 stray proposal 文件 -> 真钉子红、neuter 绿（§2 已录）
```
