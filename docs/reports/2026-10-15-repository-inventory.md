# 仓库清点与通用入口交付（2026-10-15）

## Git 状态

清点起点为 `9ac37e2`（`master` / `origin/master`）。执行 `git fetch origin --prune` 后：

- 工作区没有已跟踪文件修改，也没有未忽略的新文件；stash 为空。
- 本地分支只有 `master`，远端分支只有 `origin/master`（另有符号引用 `origin/HEAD`）。
- `git branch -a --no-merged master` 无输出；没有需要合并的功能分支，因此没有创建空提交或人为 merge。
- 6 条旧 detached worktree 记录指向已不存在的临时目录；其 HEAD 为 `72cb6a8` 或 `3669950`，均已验证是 `master` 的祖先。用 `git worktree prune` 清除失效记录后，只剩当前工作区。
- 忽略项包括原生构建产物、`.venv`、缓存、`luac.out`、本地 agent 工作目录及 `corpus/discrepancies.json`；未将它们作为源码提交，也未删除这些文件。

本轮提交到本地 `master`，不包含远端 push。

## 项目资产与通用使用边界

项目是 Python ≥ 3.12 + pybind11 + vendored Lua 5.1.5 的工具链，采用 uv 管理 Python 环境、CMake 构建原生工具。

| 位置 | 作用 |
| --- | --- |
| `src/pyluadec/ingest`、`native/`、`vendor/` | sz4/sz8 字节码读取、原生桥与 Lua 工具 |
| `lift/`、`cfg/`、`express/`、`sir/`、`emit/`、`structure/` | 指令分析、结构化重建、proposal 与 fallback 发射 |
| `verify/`、`oracle.py` | 重编译、proto 比较、认证阶梯及台账工具 |
| `tests/` | 合成回归与由外部语料门控的历史验收 |
| `corpus/`、`scripts/` | 大量历史项目的固定资产、探针和验收脚本；不等同通用 CLI |
| `CLAUDE.md`、`docs/`、`CHANGELOG.md` | 设计决策、历史结果、runbook 与交接记录 |

本轮增加根目录 README 和通用 starter guide，建立不依赖游戏资产的使用入口。指南特别说明：

- 通用任务用 `load_file` + `decompile_chunk`，避免 `decompile_file` 按文件名加载历史 proposal/naming。
- 最终写盘源码需独立做整树认证，逐 proto `levels` 与最终 shipped 来源不是同一概念。
- 当前最高阶梯是 L3.0 / L3.1；这是重编译产物比对，不能冒充证明助手级形式化证明。
- handoff 包含输入/输出哈希、环境、失配、覆盖边界与验收约束；无需启动任何外部 agent。

## 发现并修复的问题

裸跑 `uv run pytest -q` 初始结果为 **1092 passed、139 skipped、2 errors**。两个 error 来自 `tests/test_invariant_panel.py::panel_scan` 直接读取缺失的 `PYLUADEC_CORPUS_DIR`。

修复改用已有 session fixture `corpus_dir` 和 `pred_corpus_dir`，使缺少任一历史语料时按仓库约定 skip，存在语料时仍执行相同 `scan_all` 和原断言。已单独提交为 `1fdf681`。

## 验证记录

- `uv run pytest -q`：**1092 passed、141 skipped**，10.63 秒。未配置外部原始/前作语料，不能据此声称历史语料全量验收通过。
- `uv sync --locked`：成功；`./scripts/build_native.sh`：成功（当前 macOS 环境）。
- 直接提取并执行 starter guide 中全部示例操作块：生成输入、反编译、重编译、整树认证、执行对比及 listing 均成功。
- 示例得到 **L3.0**、零 mismatch、无 fallback；原件与重编译结果 SHA-256 相同。原件与候选执行均输出 `15`。
- `git diff --check`：通过。

示例产物位于 gitignored `build/starter-demo/`，可由指南重建；正式交接应另行归档。上述测试数字仅是本次环境快照，不是新语料的质量承诺。
