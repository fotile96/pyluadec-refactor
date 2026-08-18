# corpus/proposals -- propose-and-certify 的暂存 proposal（2026-08-18）

八份手写源码 proposal，每份对应 `corpus/ledger.jsonl` 里一个非 `L3` 叶子
proto，全部经**未改动的**认证阶梯在 rung 1（strip-lineinfo）通过——见
`verify_proposals.py`（判定驱动，同目录，先例是 `corpus/pred_repairs/` 的
同目录驱动约定）与 `docs/reports/m8-strategy-survey-fable5.md` §9（战役
记录与逐 proto 的编辑说明）。

- 文件格式：`certify_proto` 对非根 proto 用的 wrapper 原样
  （`local u0, ...` 声明 + `return function(<params>) <body> end`）。
- **已接入管线（2026-08-18，通道实现任务落盘）。** 消费点：
  `emit_certified_chunk` 的 proposal tier（`structure/structured.py`），
  打印臂在 `emit/lua.py::closure_parts`（reconstructor 臂之后、fallback
  之前）；台账 `shipped` 增值 `"proposal"`（ratchet 序
  structured > proposal > fallback，`structured -> proposal` 是
  `proposal-mask` 降级）；守卫在 `tests/test_proposal_channel.py`
  （枚举钉 = `structure/proposals.py::MANIFEST` 与本目录文件集相等）。
  本清单从 8 叶扩到 **9**：`main_25`（K1 折叠自有拒绝）在接线中入册。
- 除 `main_24`（从码流走查从零写出）外，其余七份都是「近失配打印文本 +
  定点编辑」的产物：基底文本由 `emit.lua._print_proto_body` 生成，编辑
  只动失配区域。
- 手编辑本目录任何文件后必须重跑驱动：
  `PYLUADEC_CORPUS_DIR=<corpus> uv run python corpus/proposals/verify_proposals.py`
