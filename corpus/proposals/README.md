# corpus/proposals -- propose-and-certify 的暂存 proposal（2026-08-18）

八份手写源码 proposal，每份对应 `corpus/ledger.jsonl` 里一个非 `L3` 叶子
proto，全部经**未改动的**认证阶梯在 rung 1（strip-lineinfo）通过——见
`verify_proposals.py`（判定驱动，同目录，先例是 `corpus/pred_repairs/` 的
同目录驱动约定）与 `docs/reports/m8-strategy-survey-fable5.md` §9（战役
记录与逐 proto 的编辑说明）。

- 文件格式：`certify_proto` 对非根 proto 用的 wrapper 原样
  （`local u0, ...` 声明 + `return function(<params>) <body> end`）。
- **这些文件尚未被管线消费。** 通道接线（`emit_certified_chunk` 在
  CLOSURE 站点查 proposal、台账 provenance、ratchet kind、warranty
  `t_grade` 分档）是通道实现任务的活；届时布局/命名以那个任务为准，
  本目录是它的输入。
- 除 `main_24`（从码流走查从零写出）外，其余七份都是「近失配打印文本 +
  定点编辑」的产物：基底文本由 `emit.lua._print_proto_body` 生成，编辑
  只动失配区域。
- 手编辑本目录任何文件后必须重跑驱动：
  `PYLUADEC_CORPUS_DIR=<corpus> uv run python corpus/proposals/verify_proposals.py`
