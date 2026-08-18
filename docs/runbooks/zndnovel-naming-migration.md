# Zndnovel 侧迁移指南：换用我方反编译基座（M8 命名对齐之后）

**读者**：维护 `/Users/fotile96/Zndnovel`（`lua_scripts/`、`tools/`、
`data/ledger*.jsonl`）的人。**方式**：partner 已定——我方整体控制修改面，
出具本指南供 Zndnovel 侧自行调整；本指南只描述事实与给出需要的改动
形状，不改 Zndnovel 一个字节。

**前置事实（全部实测，2026-08-18）**：我方反编译产物
（`pyluadec-refactor/corpus/final/`，229 文件）已完成与旧
`post_process/stage1_output/` 的命名对齐——

| 命名类 | 对齐情况 |
|---|---|
| 顶层函数名（`scene_*`、`card_*`、dispatch/shared/helper 变体，846 个，161 文件） | **与旧产物逐名相同**（translation_ir 的 817 个名称键单元 100% 同名可再锚定） |
| `scene_id` / `scene_title` 参数（908 个） | **与旧产物逐名相同** |
| 残余局部与参数 | **我方方案 `l<depth>_<reg>`**，与旧 `v\d+`/`p\d+` 无机械对应（partner 裁定 2026-08-18：不做旧兼容模式） |
| 字节码语义 | 每文件与游戏原始字节码 strip 后逐字节同一（mod 行号字段），229/229 |

## 1. 文本形状差异（正则锚定的工具必读）

我方产物的顶层函数声明形状（229 文件实测计数）：

```
890 ×  local NAME = function(...)          ← 顶层具名局部函数
317 ×  NAME = function(...)                ← 全局赋值（main 等）
  0 ×  local function NAME(...)            ← 本语料不出现
```

旧产物是「顶部一个大 `local A, B, C, ...` 语句 + 后续 `NAME = function`
赋值」。**受影响点（按 `tools/build_ledger.py` 逐行核对）**：

- `FUNC_RE = ^\s*([A-Za-z_][\w.]*)\s*=\s*function` 只匹配 317 个全局形式，
  890 个 `local NAME = function` 全部漏匹配 → 函数栈为空 → `func` 归属
  丢失。且栈的配对缩进取的是**名字列号**（`m.start(1)`），我方 `end`
  对齐在**声明行缩进**（`local ` 前缀把名字推后 6 列，`end` 却在行首
  缩进处）——只放宽正则不改编进，函数永远不入栈也不出栈。两处一起改：

  ```python
  FUNC_RE = re.compile(r'^(\s*)(?:local\s+)?([A-Za-z_][\w.]*)\s*=\s*function')
  # 入栈用 (name, 声明行缩进)，END_RE 的配对比较不变：
  #   stack.append((m.group(2), len(m.group(1))))
  ```

  （我方 `end` 与声明行同缩进是打印器的固定性质：闭包体 indent+1、
  `end` 回到语句缩进。）

- `BARE_VN_RE = ^v\d+$`（`_owner_func` 跳过裸名找真实归属者）：我方残余
  名是 `l<depth>_<reg>` 形（例 `l1_2`）。跳过逻辑需要把该形也视为裸名：

  ```python
  BARE_LOCAL_RE = re.compile(r'^(?:v\d+|l\d+_\d+|u\d+)$')
  ```

  只影响归属跳过；`scene_*`/`card_*` 等语义名不受影响。
- `VMS_RE` 消息行形状不变（`vms(id, "VOICE", "…")`）；
  `TR_LINE_RE` 标记形状不变。

## 2. 行号不是稳定锚（tr_line / ledger.line）

我方产物的行号与 stage1 不同（打印结构不同：嵌套内联 vs 顶部集中声明）。
Zndnovel 自有代码已经承认这点（`build_ledger.py` 的 F7 注释：`(file,
line)` 是执行序的载体）。换基座后：

- `-- tr_line:N` 标记与 `ledger.line` **必须从新基座整体重生成**，不能
  从旧值搬移；
- 跨版本需要稳定的锚是 **`(file, 函数名)`**——这正是本次对齐保证同名
  的层面。`tools/build_ledger.py` 的 `func` 字段、translation_ir 的单元
  目录名，都以函数名为键，换基座后语义连续。

## 3. 单元再锚定工件

`pyluadec-refactor/corpus/naming/unit_map.jsonl`（1003 行，生成器
`build_unit_map.py`，固定点纪律同台账）：每个旧翻译单元一行
`old_id == new_id`，附我方坐标 `file` / `path`（proto 路径，`main_N`
形）/ `reg`（局部函数的寄存器号；`file__main` 单元为 null）。用法：

- 名称键单元：`new_id` 即我方产物中的函数名，直接 `(file, name)` 锚定；
- `file__main` 单元：定位到 `(file, "main_<idx>")` proto——`main` 是
  全局赋值，从指令流（SETGLOBAL "main" 的 CLOSURE 来源）解析，映射表
  已代劳。

## 4. 缺陷区（单独成节，P4）

M6 在旧链路确认 6 个真缺陷 proto（`snr_music:main_3`、
`snr_common:main_75` 与 `main_76_2`、`snr_mainmenu:main_7`、
`snr_graphic:main_4`、`snr_memory:main_4`）+ 1 个路径级有意编辑
（`snr_common:main_83`）。**旧翻译资产若锚定在这些 proto 上，等于锚在
错误代码上；回填前必须人工核对。**实测现状（2026-08-18）：这 5 个
文件在 translation_ir 里**一个单元都没有**（缺陷全在库文件，翻译单元
全在剧本/卡片文件），所以当下无需搬迁任何资产——但任何未来给库文件
补翻译的动作，都要先过 `unit_map.jsonl` 的 `defect-zone` flag（映射器
带同一 zone 判定，演进自动生效；当前 flag 计数为 0 是实测事实，不是
断言缺失）。

另两个下游补丁文件（换基座后需在新基座上重放）：

- `snr_common.lua`：Zndnovel 侧字体替换（`fontLoad` 中文字体）；
- `snr_s4_10_s.lua`：Zndnovel 侧已手工修复的选择地图代码（我方基座
  **已含等价修复**——该 proto 走认证重建，不需要重放旧补丁，但请以
  运行验证为准）。

## 5. 验收建议（Zndnovel 侧自查）

1. 换基座后 `tools/build_ledger.py` 重跑：行数与旧账本按 `(file, id)`
   对账——vms 消息集合应当完全一致（字节码同一 ⇒ 常量同一）；
   `func` 归属按同名函数对账。
2. 抽查 `lua_scripts/snr_crd_103.lua`：`card_103_s6s_150_sel_step11`
   族函数名与旧文件同名、跨函数引用（如 `card_103_s6s_150_sel_resolve()`
   出现在 step11 体内）形状如常。
3. 任何以 `v\d+` 局部名为键的历史工件（若存在）不可直接搬移——
   `l<depth>_<reg>` 与 `v\d+` 无对应关系（这是 partner 裁定的取舍：
   残余局部本就没有语义）。
