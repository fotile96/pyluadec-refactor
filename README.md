# pyluadec-refactor

面向 Lua 5.1 字节码的反编译工具链：读取字节码、重建结构化 Lua、重编译认证；无法认证的部分保留 fallback 状态机。

**首次使用请读 [通用 Lua 反编译 Starter Guide](docs/runbooks/general-lua-starter-guide.md)**：无需原游戏、本地化仓库或历史语料，包含完整示例、认证边界和 agent 修复交接模板。

- [构建与跨平台排查](docs/runbooks/64bit-migration.md)
- [管线与 fallback 说明](docs/runbooks/decompile-pipeline.md)
- [结构化管线与验证细节](docs/runbooks/structured-pipeline.md)
- [维护说明与历史决策](CLAUDE.md)

当前支持 little-endian、官方格式的 Lua 5.1 字节码，序列化 `size_t` 为 4 或 8 字节；不支持 Lua 5.2+、LuaJIT 或自定义指令集。项目的 L3 是重编译后的 proto 比对认证，不是证明助手验证的完整 Lua 语义证明。
