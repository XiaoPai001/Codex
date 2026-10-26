# Codex：会话内子智能体适配

以实际暴露的 `multi_agent_v1` 工具 schema 为准。不要把此工作流实现成 `create_thread` / `fork_thread`，也不依赖 `send_message_to_thread`，因为那些会创建或操作用户的其他聊天。

- 使用 `spawn_agent` 的 `fork_context:true` 继承当前可见历史。**完整历史 fork 时必须省略 `agent_type`**；本机实际接口会拒绝同时传 `agent_type`，因为 fork 继承父类型。先按入口解析本次覆盖和 config.json：最终 model/effort 为 `inherit` 才分别省略 `model` / `reasoning_effort`，当前工具说明此时继承父设置；不要把字符串 `inherit` 原样传入工具。
- 不选固定模型/档位的 `reviewer`。若父类型本身固定了模型而与用户指定值冲突，不能用 fork 偷偷继承错误模型；改用 `fork_context:false,agent_type:"default"` 和完整执行简报，但仍须校验指定值可以表达，并向用户说明此时继承的是关键摘要，不是完整历史。
- 最终解析出具体值（来源为本次指令或用户配置）时，校验当前工具列出的模型及档位后传入。不要硬编码安装这天的模型清单；提供商/账号限制不能由技能绕过。
- `message` 放完整执行简报；若工具支持结构化 `items`，可以按需引用文件/技能。两种消息输入方式按 schema 二选一。
- 保存 `agent_id`，使用 `wait_agent({targets:[id],timeout_ms:...})` 等待结果。按当前交互环境限制设置有界等待并及时向用户说明实质进展，不不断重复短等待。`timed_out:true` 不表示任务已失败。
- 需要传达用户新修正时使用同一 agent 的 `send_input`，只有确实要打断旧方向才 `interrupt:true`。完成并检查产物后 `close_agent`；不得把 close 的成功回执当成任务成功。
- `fork_context` 只解决上下文传递，不代表已建立 Git worktree 或文件写入隔离。根据实际环境核对目录与变更；执行者不能回滚/覆盖其他人的修改。

默认请求形态示意（发送前替换简报，不机械复制占位文本）：

```json
{
  "fork_context": true,
  "message": "实际执行简报"
}
```

可用时从该 agent 的 runtime/turn_context 核对有效模型与 effort；仅读取必要元数据，不泄露完整日志。仅有 `spawn_agent` 参数时说“按这些参数启动并返回”，不声称服务端独立证明。
