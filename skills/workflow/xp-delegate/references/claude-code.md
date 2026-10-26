# Claude Code：会话内子代理适配

使用当前会话实际可用的 Agent/子代理工具；旧版本的工具名或输入字段可能不同，先读 schema，不照搬 Codex 的 `spawn_agent` / `reasoning_effort` / `wait_agent`。

- 先按入口规则读取本 skill config.json，并按字段应用本次用户覆盖。最终为 `inherit` 时才沿用主设置；最终为具体值时按宿主 schema 传递。此配置不是 Claude 全局设置，也不替代 .claude/agents 中的实际定义。
- 选择可执行任务的通用子代理。继承模式优先使用实际支持的设置；若默认会受自定义 Agent 的 model/effort 配置影响，则不能把省略参数当成继承保证。检查有效配置；无法确认继承机制时先报告限制，不偷偷选 sonnet/opus。
- 具体模型值使用当前宿主支持的别名或完整 ID，并检查账号/网关是否可用。不能默认认为 Codex 的 GPT 模型 ID 在 Claude Code 中可用。具体 effort 用当前 Claude schema 的合法字段和值；inherit 模式无法保留主设置时说明。
- Claude 的普通子代理不一定收到完整主聊天历史。若实际提供当前对话 fork 功能且符合任务要求，可以使用；否则将完整的关键执行简报传入，而不是只说“继续上面的任务”。
- 不要给本 skill 固定添加 `context: fork` 或预设一个子代理 model：那可能把整个编排技能先放入子代理，妨碍主对话监督或导致二次委派。由主对话显式启动一个执行者即可。
- 优先使用会返回主对话的前台执行。若宿主实际以后台执行，则按返回的任务句柄使用对应等待/结果工具，直到取得结果再汇报；不能混用 Codex agent ID 或承诺父会话结束后一定自动通知。
- 主对话接到结果后核对实际文件和验收证据，再向用户汇报。不另起一个普通 Claude 聊天或切窗口代替会话内子代理。
- 此处不自动创建 `.claude/agents/` 配置、不改全局模型、不注册 MCP。若工具/配置缺失而确实必须增加配置，先说明缺少什么；不能把安装技能当作已配置子代理的证据。

官方参考（用于解释宿主差异，实际执行以已安装版本和工具 schema 为准）：

- https://code.claude.com/docs/zh-CN/sub-agents
- https://code.claude.com/docs/zh-CN/skills

Codex 的 `agents/openai.yaml` 是其 UI 元数据，不能替代 Claude Code 的子代理配置。Claude 调用本 skill 使用 `/xp-delegate`，并从 Claude 的技能目录安装；这不自动继承 Codex 的模型、权限或 MCP 连接。
