# M8 务虚清点：残差的性质已经变了——从「算法能力」到「搜索」（2026-08-18）

**文档性质**：应 human partner 要求做的务虚（strategic）清点与建议，不是 spec/plan
修订，不承载任何已批准的决定。M8 的 spec/plan 条款以其原文件为准；本文与它们冲突处，
本文只是建议。

**出处（per 本仓库的多模型 provenance 约定）**：本文由 Claude Code 会话产出，会话
起始 env 块自称 Opus 5，但 partner 已于本文撰写前手动 `/model` 切到 **Fable 5**，
故以 Fable 5 记名。本文所有测量在该会话内、于分支
`phase8-m8-zero-doubt-handoff` @ `0e9755e`（clean tree）实跑，复现命令全部在 §8。

**一句话结论**：8 个残差叶子 proto 全部是「源码形状复原」问题而不是「语义等价」
问题；本仓库的认证架构（法官不挑原告）天生适合接一个**不需要可信**的搜索式
proposer。把这扇门装上，「8 个 proto 清零」「彻底排除 fallback 输出」
「229/229 文件级字节同一」是同一件事的三个名字。本文用两个新测量支撑这句话，
其中一个是**已演示的实例**（§3：`snr_common:main_24` 的手写 proposal 在未改动的
阶梯上 rung 1 通过）。

---

## §1 现状快照（全部实测于 2026-08-18）

### 1.1 台账结构

- `corpus/ledger.jsonl`：**1478 唯一行 / 1944 处 occurrence；L3 1463 行（99.0%）**。
- 非 L3 仅 **15 行**，`structure:` / `reconstruct:` 家族已被 M8 task 2/3 清零，
  幸存的全部是 `mismatch:*`。
- **15 行的真实结构：真正的叶子拒绝只有 8 个 proto**。其余 7 行全是继承：
  4 个文件根（`snr_common`/`snr_mainmenu`/`snr_graphic`/`snr_story_main` 的
  `main`，refusal 带 `at root/N` 路径）+ `main_74` / `main_76`（同型继承）+
  `main_25`（petition pack 的判定：其残余失配全部住在后代 `main_25_4` 里，
  行本身是继承——此判定引自 `docs/reports/m8-petitions.md`，本文未独立重导）。

### 1.2 八个叶子（尺寸经 `pyluadec.ingest` 实测）

| proto | 指令数 | maxstack | 常量数 | 失配 | 机制 |
|---|---:|---:|---:|---|---|
| `snr_mainmenu:main_7` | **2182** | 12 | 80 | maxstacksize | busy-slot（`u1.library` 双求值，`226b980`）|
| `snr_graphic:main_4` | 769 | 11 | 73 | code | busy-slot |
| `snr_story_main:main_3` | 461 | 19 | 91 | code | busy-slot |
| `snr_common:main_71` | 450 | 28 | 77 | code | 构造器级联 + 27 项常量池重排 |
| `snr_common:main_76_2` | 174 | 9 | 41 | maxstacksize | busy-slot |
| `snr_common:main_25_4` | 90 | 8 | 21 | maxstacksize | busy-slot |
| `snr_common:main_74_18` | 86 | 9 | 22 | maxstacksize+code | 死寄存器保留（bytecode 不可见）|
| `snr_common:main_24` | **8** | 2 | 4 | code | NEWTABLE hint（原始 C=1，我方重编译 C=3）|

注意：这 8 行的 refusal 全是 `mismatch:*`——意味着**每一个的结构化文本都已能
打印、已能编译**（mismatch 只有走到比对那一步才会出现），差的只是最后一段
「与原始逐字段相同」。

### 1.3 occurrence 记账

- fallback-shipped occurrence **15 处** = 9 个 L1 叶行（上表 8 个 + 继承的
  `main_25`）+ **6 个自身 L3 却因住在 fallback 内联子树里而发状态机文本的
  连带者**（`main_24_0/1`、`main_25_0..3`）。清掉 8 个叶子，6 个连带者与
  `main_25` 自动解放。
- 非 L3 occurrence 也是 15 处，但**是另一个集合**（含 6 个发结构化文本的继承
  祖先行，不含 6 个连带者）；两个 15 同数纯属当前巧合，
  `tests/test_ledger.py::test_fallback_and_non_l3_occurrences_currently_coincide`
  已把它钉为「当前事实、明确非不变量」。
- 整文件 fallback **0**（M8 task 4/5 战役成果）；hybrid 文件恰为上述 4 个。

### 1.4 脚注（footprint）与其绝对量

| 文件 | 原始字节 | 比例（钉值）| 绝对膨胀 |
|---|---:|---:|---:|
| `snr_mainmenu.lua` | 18043 | 3.5598 | ≈ +46 KB |
| `snr_common.lua` | 124517 | 1.1555 | ≈ +19 KB |
| `snr_graphic.lua` | 11939 | 1.9509 | ≈ +11 KB |
| `snr_story_main.lua` | 9984 | 1.6956 | ≈ +7 KB |

出口条款 3 的 1.5× **比例**口径与 PSP 堆风险（绝对字节）不对齐：1.16× 的
snr_common 绝对膨胀比 1.95× 的 snr_graphic 还大。若 §4 的建议落地此题整体消失；
若不落地，重定条款时建议改为绝对字节预算（见 §7.2）。

### 1.5 盒模型游戏文本的真实分布（逐行看过内容）

M7 出口钉住的 5 行 `__pld_R[n] = "<非 ASCII>"`：

- `snr_common.lua`（3 行，行号 947/981/983）：`■デバッグ：`、`Ｋｅｙ＿`、
  `：Ｖａｌｕｅ＿`——**全是调试输出串**，不面向玩家。
- `snr_story_main.lua`（2 行，行号 377/382）：两条『■おしらせ』Fragment 模式
  公告——**这才是仅有的面向玩家、需要翻译的 fallback 文本**，都在 `main_3`。

即「5 行游戏台词」这个数字对本地化的压力被高估了 60%：真实压力集中在
`snr_story_main:main_3` 单点。

### 1.6 B1 与 M8 剩余任务

B1（busy-slot 的逐语句 slot-liveness 释放）处于 iteration 3，三次
implemented-and-reverted-green；`226b980` 的测量表明即使 B1 完全成功，
`main_7` 的字节精确仍被 STRICT 的双求值禁令挡住（对**自动重建**而言——见 §4.2
对这句话适用域的澄清）。M8 plan 的 task 7（命名）/ 8（text-unit 清单）/
9（迁移指南）/ 10（收口）未动。

---

## §2 新测量一：225/229 文件级字节同一（仅差行号元数据）

### 2.1 方法

对 `corpus/final/` 每个文件：`./build/luac_sz4 -s` 重编译 → 与
`$PYLUADEC_CORPUS_DIR` 原始字节码比。比对前用一个 ~40 行的归一化器**只**把
双方 `DumpFunction` 主体里的 `linedefined`/`lastlinedefined` 两个 int 清零
（完整解析 5.1 dump 格式，`assert pos == len(buf)` 保证没有静默跳段；脚本全文
在 §8.2）。

### 2.2 结果

> **225/229 个文件在清零两个行号字段后与原始 PSP 字节码逐字节相同。**
> 残差恰为 4 个 fallback 载体文件（size 就不同）。其中 **`config.lua` 连
> 归一化都不需要——raw `cmp` 逐字节相同**。

抽样细节（`snr_lib.lua`，1656 字节）：raw diff 仅 4 个字节，全部落在嵌套
proto 的 `linedefined`/`lastlinedefined`（我方 1/2/3/120 对原始 10/11/15/144
——即原始源码的函数起止行号，语料 strip 后唯一幸存的行信息，CLAUDE.md
「`linedefined` 幸存」一节早已记载它不属于 debug 段、`-s` 剥不掉）。

### 2.3 为什么这不是新证明、却是新陈述

逐 proto 的 L3@rung1 已经蕴含这件事（rung 1 恰好把 `source`/`linedefined`/
`lastlinedefined`/`lineinfo`/debug 名清零后逐字段比）。但**文件级**的说法对
下游的力度完全不同：对 225 个文件，「翻译工程拿到的文本重编译后就是 PSP 上
跑的那串字节（除了行号元数据）」是一条一个命令可复核、无需理解认证阶梯的
陈述。它也顺带说明：**只要翻译不改变代码结构，重编译回填是无损的**。

### 2.4 建议：把它立为 M8 的北极星门

`229/229 文件级字节同一（mod linedefined/lastlinedefined）`。这个门一旦达成：

- footprint 门恒为 1.0000×，出口条款 3 被**蕴含**（不是被重定）；
- 质量分、occurrence 比例、L3 比例全部被蕴含；
- 「排除未知语义不一致」收缩为两个已被守护的点：oracle 忠实性（golden parity
  门）与比较器正确性（字节比对，无解释层）。

它比现有四条出口门加起来更强、更便宜、且下游可读。

---

## §3 新测量二：`main_24` 的 propose-and-certify 演示（本文最重要的一节）

### 3.1 hint 是源码形状的函数——先在合成例上验证

`main_24` 原始码流（golden dump）：`NEWTABLE C=1` + 3 条 SETTABLE +
2 个 CLOSURE + `RETURN R0 2`。我方发射器把三个字段全折进构造器 → 重编译
`C=3`。两种拼法实测（`luac_sz4 -l`）：

```
xxx = { startMenuState = 0, debagMsg = ..., debagPairs = ... }   → NEWTABLE 0 0 3
xxx = { startMenuState = 0 }; xxx.debagMsg = ...; xxx.debagPairs = ...
                                                                  → NEWTABLE 0 0 1
```

即原始源码的形状是「1 个字段内联 + 2 个后置赋值」。hint 不需要 rung 去遮蔽
——它需要 proposer 去**拼对**。

### 3.2 整个 proto 子树的手写 proposal，未改动的阶梯，rung 1 通过

按 1-based 码流走查读出两个闭包体的语义后，手写候选（wrapper 形式与
`certify_proto` 对非根 proto 的约定一致，`main_24` nups=0 故无 upvalue 前奏）：

```lua
return function()
    local t = { startMenuState = 0 }
    t.debagMsg = function(msg)
        if debagFlag then
            vms(1, "NONVOICE", "■デバッグ：" .. msg)
        end
    end
    t.debagPairs = function(t2)
        if debagFlag then
            for k, v in pairs(t2) do
                vms(2, "NONVOICE", "Ｋｅｙ＿" .. k .. "：Ｖａｌｕｅ＿" .. v)
            end
        end
    end
    return t
end
```

经 `oracle.compile_source(strip=True)` → `load_bytes` → 取 `subprotos[0]` →
对原始 `main_24` 跑**未改动的** `compare_protos` 阶梯：

```
rung 0 (strict):        linedefined/lastlinedefined 失配（预期内，语料常态）
rung 1 (strip-lineinfo): PASS
```

**这正是全语料 1463 行 L3 通过的同一个 rung。** 8 指令的 `main_24`——
Petition A 想为它开一个带 `pairs()` 序漏洞的比较器 rung 的那一行——被一段
15 行的手写 proposal 在完全未触碰认证逻辑的情况下拿下。复现脚本在 §8.4。

### 3.3 对 Petition A 的含义

pack 的 DECLINE 推荐**继续成立且加强了**：不仅那个 rung 有漏洞，它根本
**不必要**——该行可以通过源码形状复原走正门。「想要这一行就得先做 pairs
缺席分析」的前置条件随之作废，因为不再需要遮蔽任何东西。

### 3.4 诚实边界

- 这是 8 个叶子里**最小**的一个；演示的是通道可行性，不是对其余 7 个的许诺。
- 演示在 proto 子树粒度（正是台账行度量的东西）；进产物还要经 hybrid 机制在
  父 proto 的 CLOSURE 站点组装——那套机器已存在（M5 task 6），但 override
  接入点需要新代码（§4.4）。
- 手写走查花的功夫 ≈ 半小时（含读码流）。2182 指令的 `main_7` 不是这个量级，
  见 §4.5 的路线建议。

---

## §4 建议一（最大甜头）：给 8 个叶子开 propose-and-certify 通道

### 4.1 架构论点：法官不挑原告

`certify_proto` 只问「这段文本编译出来的字节与原始是否逐字段相同」，不问文本
从哪来。当前唯一的原告是自动 reconstructor——它必须对全语料 sound，所以被
STRICT、`declared` 闸门、35/157/8 三次回归教训层层束缚，这是**对的**（它要对
1478 个形状负责）。但 proposer 不需要 soundness：**字节相等本身就是全部证明**。
猜错了法官拒收、错误代码一行都发不出去——认证门纪律（「要么正是认证比对过的
那串字节，要么 confess」）在 override 通道下不仅不被削弱，反而对这些行从
「fallback + confess」升格为「认证字节」。

### 4.2 对 `226b980` 的重解读（B1 僵局的溶解点）

「STRICT 禁止 `u1.library` 双求值，两个修复方向都救不了 `main_7`」——这句话
的适用域是**自动重建**：reconstructor 不被允许把一次求值改写成两次，因为它
无法证明该表达式无副作用。但**原始源码本来就求值了两遍**；proposer 把它写回
两遍是**转写**（transcription），不是变换（transformation），其正确性由字节
相等事后担保，不需要任何效应推理。busy-slot 五兄弟的失配全是「我们物化了
局部、原文逐次重读」——从已能打印、已能编译的近失配文本出发，按失配位置
定点改回逐次重读形态，是有 diff 反馈的定点编辑。

### 4.3 逐机制族的源码形状解

- **`main_24`（hint）**：已演示，§3。
- **busy-slot ×5**：如上；起点是近失配文本 + `Mismatch.path`，不是从零写。
- **`main_71`（构造器级联 + 常量池重排）**：常量池顺序由源码里常量**首次出现
  顺序**决定，构造器拆分形状由拼法决定；自动 fold cap（157 回归被拒）走不到
  的地方，proposer 自由拼写可以到。197 指令的重排让它成为 `main_7` 之外第二
  难的目标。
- **`main_74_18`（maxstack 低于原始 + code）**：要复原一个 bytecode 里不可见
  的死寄存器保留——「带失配反馈迭代猜源码」这种搜索最擅长、sound 算法结构性
  不擅长的题型。

### 4.4 机制草图（务虚粒度）

- `corpus/overrides/<file>/<proto_path>.lua`（入库，地位同 `corpus/final/`：
  是我方书写的源文本、可含游戏文本原样 UTF-8）。
- `emit_certified_chunk` 在 CLOSURE 站点落 fallback **之前**查 override：
  存在则走**同一个** `certify_proto` 门，`L3` 才内联，否则忽略并照旧
  fallback——比较器、阶梯、`LADDER_VERSION` 一字不动。
- 台账 provenance：`shipped` 增值 `"override"`（或并列新字段）；
  `ratchet_diff.py` 增 kind：`override → fallback` 是降级。
- 记账蔓延要诚实列出：`test_m3_exit` 的行内耦合（override 行是认证 L3 →
  无 confession）、warranty 的 shipped-first `t_grade`（override-shipped =
  认证文本 → T 随内容分级，不再强制 T-）、`run_corpus.py` 不动点照旧成立
  （overrides 入库、生成确定）。有界的簿记工作，但不是零。
- 这正是 spec §2 决策表「pass registry 永久退役」条目里预留的座位：
  「插件面本身没被否定，只是客户在 M6+（GPU 提议器）」——坐进来的客户是
  人/LLM proposer 而已，且它比 pass 协议更简单：无 apply/rollback，只有
  propose + 既有的 certify。

### 4.5 路线与产出核算

建议第一增量：**`main_76_2`（174 指令，busy-slot 中最小）上重复 §3 的手工
演示**——它能同时验证「近失配文本 + 定点编辑」这条工作流（`main_24` 没用到，
是从零写的）。成功后再装通道、再攻大目标。产出核算：8 叶清零 → `main_25` 与
6 连带 + 6 继承祖先自动解放 → 台账 15 行归零、fallback occurrence 15 处归零、
4 文件回 1.00×、北极星门 229/229、出口条款 3 被蕴含而非重定、
`snr_story_main` 那 2 行玩家可见文本自动进入结构化文本。**「彻底排除
fallback 输出」——partner 标记为可能非常重要的那条——就是这条路的直接产物。**

### 4.6 这个建议不许诺什么

`main_7`（2182 指令）能否在可接受的功夫内拼出，是**假设**；本文只演示了
8 指令的实例并论证了机制族的可解性。若 `main_7` 最终拼不出，通道仍然清掉
其余 7 叶 + 全部连带（snr_mainmenu 单文件残留），届时再谈止损的范围比现在
小得多。

---

## §5 建议二：B1 悬置为「proposer 的弹药库」

B1 三次 implemented-and-reverted-green，每次的发现都是「作用域/打印顺序的
粒度在另一层」——这是在为一个全语料 sound 的变换付费，而其全部收益人只有
5 个 proto，且最大的 `main_7` 即使成功也拿不到字节精确（§4.2 只对 proposer
溶解此僵局，对 B1 自动路线不溶解）。建议：

- **悬置 B1 的进树目标**（不是否定其分析——iteration 2 的「materialize 批
  与 print 批分离」是真发现）；
- 把 iteration 1–3 攒下的机器（逐 pc 活性 oracle、env-tree 判别器、
  `captured_regs` 卫兵）转用为**机械 proposal 生成器**：生成器不必 sound，
  8 回归的 B2 作为生成器同样无害——法官在后面。三轮迭代的沉没成本变成
  §4 的首付。

---

## §6 建议三：验证工作的收官形态

- 北极星门达成后，L2 差分执行、taint、`probe_enum` 对**我方产物**只剩历史
  价值（字节同一使语义等价 trivially 全量）。在那之前，给 4 个残差文件扩
  L2/枚举 reach 是给即将拆除的桥加固——**不建议投入**。
- 这些仪器的余热应转向**迁移期**：下游 Zndnovel 现坐在带 6 个已确认缺陷的
  前作 stage3 产物上；「旧产物 → corpus/final 切换前后的行为差异清单」
  （拿 L1.75/keyseq 探针对双方跑）本身就是迁移指南应有的一章，且现在就能做。

---

## §7 建议四：可读性 / 下游对接的排序与两个小项

### 7.1 排序

1. **task 8（text-unit 清单）先于 task 7（命名）**：清单定义下游锚定格式，
   是 Zndnovel 侧一切工装的输入契约；命名只是清单名字列的美化。
2. 命名 pass 对认证**免费**：语料 strip 过，局部名不进字节码——「改名后
   重认证照跑、台账字节不变」应作为命名 pass 的验收断言（「呈现层变更 =
   台账字节不变」的既有定义直接适用）。
3. 迁移指南可先行的部分不依赖残差收口：225 文件字节同一清单（§2）、
   6 个前作缺陷在新产物中的修复对照、`l<depth>_<reg>` 命名约定、
   text-unit 锚定格式。

### 7.2 两个小项

- **本机 shell env 里 `PYLUADEC_CORPUS_DIR=/Users/fotile96/corpora/script_to_decompile`
  是死路径**（目录不存在；`.zshrc`/`.zshenv`/`.zprofile` 均未设置它，来源
  应是会话启动环境）。真实语料在
  `/Users/fotile96/pyluadec/others/script_to_decompile`。带着 stale 值裸跑
  任何门都会静默 skip 全部语料用例——CLAUDE.md 记载过这个坑的机制，这里是
  它的一个活体实例，值得修。
- 若 §4 不落地而需重定出口条款 3：按 §1.4 的测量，比例口径与堆风险不对齐，
  建议改为**绝对字节预算**（真实风险背景是双语实验的全语料性膨胀导致
  存读档堆耗尽；单文件 +46 KB 是否触险，值得在 PSP 侧实测而非估计）。

---

## §8 附录：全部复现命令

树：`phase8-m8-zero-doubt-handoff` @ `0e9755e`，clean。
`CD=/Users/fotile96/pyluadec/others/script_to_decompile`。

### 8.1 台账计数（§1.1/1.3）

```python
import json
rows=[json.loads(l) for l in open('corpus/ledger.jsonl') if l.strip()]
occ=[(r,o) for r in rows for o in r['occurrences']]
# 1478 rows / 1944 occ; L3 rows 1463; 非L3 occ 15; shipped=='fallback' occ 15
```

叶子尺寸表（§1.2）：`pyluadec.ingest.load_file` 后按 `_i` 路径走 `subprotos`，
读 `len(p.code)` / `p.maxstacksize` / `len(p.constants)`。

### 8.2 文件级字节同一（§2）

```python
# 对每个 corpus/final/*.lua：
#   ./build/luac_sz4 -s -o /tmp/rt.bin <f>
#   与 $CD/<f> 比：len 不等 → residue；否则 normalize 后比。
import struct
def normalize(data: bytes) -> bytes:
    buf = bytearray(data); pos = 12
    def rd_int():
        nonlocal pos
        v = struct.unpack_from('<i', buf, pos)[0]; pos += 4; return v
    def skip(n):
        nonlocal pos; pos += n
    def rd_string():
        skip(rd_int())          # size_t==4 (sz4)
    def func():
        nonlocal pos
        rd_string()                                   # source
        struct.pack_into('<i', buf, pos, 0); pos += 4 # linedefined -> 0
        struct.pack_into('<i', buf, pos, 0); pos += 4 # lastlinedefined -> 0
        skip(4)                                       # nups/numparams/vararg/maxstack
        skip(4 * rd_int())                            # code
        for _ in range(rd_int()):                     # constants
            t = buf[pos]; pos += 1
            if t == 0: pass
            elif t == 1: skip(1)
            elif t == 3: skip(8)
            elif t == 4: rd_string()
            else: raise ValueError(t)
        for _ in range(rd_int()): func()              # protos
        skip(4 * rd_int())                            # lineinfo
        for _ in range(rd_int()): rd_string(); skip(8)  # locvars
        for _ in range(rd_int()): rd_string()         # upvalues
    func()
    assert pos == len(buf), (pos, len(buf))
    return bytes(buf)
```

实测输出：`byte-identical modulo linedefined/lastlinedefined: 225/229`；
residue = 4 个 fallback 载体（size 不等：snr_common 143881/124517、
snr_graphic 23292/11939、snr_mainmenu 64230/18043、snr_story_main
16929/9984）。raw `cmp` 下唯一逐字节相同者：`config.lua`。

### 8.3 hint 拼法实验（§3.1）

两个单行/三行 Lua 文件各经 `luac_sz4 -s` 编译后 `-l` 反列：
内联三字段 → `NEWTABLE 0 0 3`；一内联两后置 → `NEWTABLE 0 0 1`（与原始一致）。

### 8.4 `main_24` 手写认证（§3.2）

```python
from pyluadec.ingest import load_file, load_bytes
from pyluadec.verify.normalize import compare_protos, NORMALIZATIONS
from pyluadec import oracle
root = load_file(f"{CD}/snr_common.lua")
orig = <walk 到 main_24>
compiled = oracle.compile_source(candidate_bytes, strip=True)  # §3.2 候选全文
cand = load_bytes(compiled).subprotos[0]
# rung 0: linedefined/lastlinedefined 失配（预期）
# rung 1 (strip-lineinfo): compare_protos 空失配 → PASS
```

### 8.5 盒模型文本清点（§1.5）

`grep -n '__pld_R\[[0-9]*\] = "' corpus/final/{snr_common,snr_story_main}.lua`
过滤非 ASCII 行：snr_common 947/981/983（调试串），snr_story_main 377/382
（玩家公告）。
