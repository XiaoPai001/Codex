# DHS XDbg 适配及快照格式

实际服务为 `mcp__DHS_XDbg_MCP`，不是 `mcp__x64dbg` 或 `x64dbg_automate`。不要求安装其他调试插件。

| 操作 | 实际工具/参数 |
|---|---|
| 是否存在调试目标 | `IsDebugging({})` → structuredContent.result；false 需结合真实响应区分无目标和连接失败 |
| 是否正在运行 | `IsDebugActive({})` → result；只有存在目标时 false 才有暂停含义 |
| 状态证据 | `GetModuleList({})`、`GetThreadList({})`、`GetRegisterDump({})`、`GetMemoryMap({})`（按需） |
| 只读范围 | `MemoryRead({addr:"0x...",size:"0x100"})`，两参数均为字符串，size 用明确十六进制；读取后校验实际字节数 |
| 指令/解释 | `DisasmGetInstructionRange({addr,count})`，count ≤100；`MiscParseExpression({expression})` 仅用于明确无副作用的表达式 |
| 授权实验才用 | `DebugPause`、`DebugRun`、`DebugStepIn/Over`、`DebugSetBreakpoint`、`SetHardwareBreakpoint` 等；绝不因采集自动调用 |

`ExecCommand` 可以执行任意调试命令，不作为默认状态查询或读取兜底，不能把未知命令当只读。工具异常必须保留原响应和错误；未加载目标不能虚报成功。

本机实测：HTTP 8888 不可达时，`IsDebugging` / `IsDebugActive` 可能仍返回 false，`GetModuleList` 则返回带 `Request failed` 的 error/raw；甚至 `isError:false` 也不代表请求成功。检查文本及结构化 error，不把错误字符串作为 hex，不据 false 自动断言服务在线。此时报告连接不可用，不自动改配置、重启服务或安装 x64dbg_automate。

## xp-debug-snapshot-v1

由 agent 将 MCP 结果转换为以下结构；原响应另存，不直接把 MCP 包装文本当成 hex。

```json
{
  "format": "xp-debug-snapshot-v1",
  "session_id": "本次调试进程生命周期内的唯一观察ID",
  "target_id": "实际目标文件身份或哈希；未知需明确记录",
  "process_id": null,
  "pointer_size": 8,
  "thread_id": "1234",
  "consistency": "paused",
  "captured_at": "带时区的时间",
  "registers": {"cip":"0x140001000","cax":"0x1"},
  "regions": [
    {"id":"player", "address":"0x200000", "size":4, "read_ok":true, "hex":"01 00 00 00"}
  ]
}
```

`pointer_size` 只能来自目标架构，不能凭 MCP 服务/操作系统位数推断。`size` 为十进制整数，hex 解码后长度必须一致。失败读取用 `read_ok:false,error:"实际错误",hex:null`；分块部分失败时应拆为成功与失败范围，不能补零。每段 ID 唯一、地址不得越过目标位宽；同一快照中的范围不能重叠，以免重复计数。

`session_id`、`target_id`、`captured_at` 必填且非空；时间须为带时区的 ISO 8601，时间相同或倒序时报告时序不确定，不能推导操作因果。只有已核实同一目标才可在 after 复用 ID。`consistency` 可为 `paused` / `unverified`；脚本拒绝后者。目标状态证明、模块/RVA、原始工具文件引用和操作说明可作为额外元数据保留。数字寄存器统一为整数或 `0x` 字符串，保留未知寄存器的原值，不依据 `cax` 一词推断架构。
