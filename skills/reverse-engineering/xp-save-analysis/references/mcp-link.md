# 存档读写链的现有 MCP 联动

不是安装器；无需新增 MCP。工具清单和 schema 以本次实际发现为准。缺少目标时继续已有离线证据或报告缺口，不能伪造运行观察。

## IDA：mcp__hex_rays_ida

- `list_databases({})` 确认目标，`reference({query: ...})` 查 strings、imports、xrefs、decompile、operands 的实际 ida-domain API，然后 `execute_python({code,instance_id})` 只读取。
- 从样本路径/扩展名/序列化错误文本及文件读取 API 的调用点寻找真正的读写函数；仅命中字符串不等于已找到处理链。区分游戏代码和通用压缩/序列化库。
- 记录磁盘缓冲区长度、解码后长度、调用参数和实际字段读写；不要凭函数名猜加密算法。反编译失败退回指令级证据。
- 无库而用户指定原始二进制时，先复制到新分析目录再 `open_database`，不改原二进制或覆盖活动 IDB；不自行关闭用户 GUI、不调用 save 或 patch 工具。

## 调试：mcp__DHS_XDbg_MCP

- 先检查 `GetModuleList` 等实际响应中的 error/raw，再结合 `IsDebugging({})` 和 `IsDebugActive({})` 区分目标状态；`GetThreadList`、`GetRegisterDump` 取得上下文。底层连接失败可能仍返回 false 且 `isError:false`，不能单凭布尔值声称连接正常。
- 已暂停且用户指定相关缓冲区时用 `MemoryRead({addr:"0x...",size:"0x..."})` 分块读取，默认每次最多 4 KiB，校验返回长度并保留错误。只读实际指定范围，不默认全进程 dump。
- 记录模块基址及 RVA、线程、采集时间、输入输出缓冲区和长度；进程重启后重新核对对象身份，不自动复用旧地址。
- 控制执行、文件 API 断点、内存写断点或跟踪必须属于用户明确要求的动态实验；只要求文件分析不授权暂停、步进、启动或改内存。任何实验不得替换原存档，需由用户选择测试副本/槽位。

此 skill 独立可用；若同机有 `xp-ida-struct` 或 `xp-debug-diff`，可复用其证据格式，但不依赖它们安装成功或其模型配置。
