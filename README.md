# Codex 技能合集

按用途分类维护的 Codex 技能。仓库中的分类目录用于浏览，安装后每个技能仍是独立文件夹。

个人技能统一使用 `xp-` 前缀，界面显示为 `XP · 中文名称`。在技能选择器中输入 `xp-` 可集中查找本仓库的技能。

## 技能目录

| 分类 | 技能 | 功能 |
|---|---|---|
| 开发 | [xp-review-flow：独立代码审阅](skills/development/xp-review-flow/SKILL.md) | 启动独立审阅子智能体，检查缺陷、回归风险和测试缺口，提供结论与整改方案 |
| 逆向分析 | [xp-re-notes：逆向分析笔记整理](skills/reverse-engineering/xp-re-notes/SKILL.md) | 总结本地 MD、整理数据结构、生成交接摘要，保留来源与不确定项，另存结果 |
| 逆向分析 | [xp-ida-struct：IDA 结构恢复](skills/reverse-engineering/xp-ida-struct/SKILL.md) | 从真实指令、反编译与交叉引用恢复字段候选，保留证据和冲突，默认不改 IDB |
| 逆向分析 | [xp-debug-diff：调试状态对比](skills/reverse-engineering/xp-debug-diff/SKILL.md) | 适配 DHS XDbg MCP，采集指定范围快照，离线对比寄存器与内存变化 |
| 逆向分析 | [xp-save-analysis：存档格式分析](skills/reverse-engineering/xp-save-analysis/SKILL.md) | 对比存档样本、分析格式与数值线索，按需联动 IDA/调试器，保留不确定项 |
| 工作流 | [xp-context-handoff：上下文交接](skills/workflow/xp-context-handoff/SKILL.md) | 切换模型或聊天前保存任务背景、决定、进展和下一步计划，读取交接文档接续工作 |
| 工作流 | [xp-status：大白话进度](skills/workflow/xp-status/SKILL.md) | 在聊天中简短解释当前在做什么、做到哪了、还差什么和下一步，默认不保存文件 |
| 工作流 | [xp-delegate：子智能体接续](skills/workflow/xp-delegate/SKILL.md) | 将当前任务交给一个子智能体继续，默认沿用主模型，也可配置/指定模型，完成后由主聊天汇报 |

## 安装

克隆本仓库后在仓库根目录执行。Python 安装器需要 Python 3；Windows 的 PowerShell 安装器可独立使用。

```sh
python scripts/install.py --skill xp-review-flow
python scripts/install.py --skill xp-re-notes
python scripts/install.py --skill xp-context-handoff
python scripts/install.py --skill xp-status
python scripts/install.py --skill xp-delegate
python scripts/install.py --skill xp-ida-struct
python scripts/install.py --skill xp-debug-diff
python scripts/install.py --skill xp-save-analysis
```

```powershell
./scripts/install.ps1 -Skill xp-review-flow
./scripts/install.ps1 -Skill xp-re-notes
./scripts/install.ps1 -Skill xp-context-handoff
./scripts/install.ps1 -Skill xp-status
./scripts/install.ps1 -Skill xp-delegate
./scripts/install.ps1 -Skill xp-ida-struct
./scripts/install.ps1 -Skill xp-debug-diff
./scripts/install.ps1 -Skill xp-save-analysis
```

不指定技能时默认安装 `xp-review-flow`。默认安装位置是 `~/.agents/skills/<技能名>`，跨仓库使用。安装后在下一轮对话调用；若列表未刷新，可新开聊天。

指定安装位置时，目标目录名必须与技能名一致。例如安装到 `$CODEX_HOME/skills` 下或项目的 `.agents/skills` 下：

```sh
python scripts/install.py --skill xp-re-notes --dest .agents/skills/xp-re-notes
```

```powershell
./scripts/install.ps1 -Skill xp-re-notes -Destination .agents/skills/xp-re-notes
```

已有目标默认拒绝覆盖。确需替换安装时加 `--force` / `-Force`，这会删除并替换对应技能目录，包括本地配置；请先保留需要的修改。

也可请 Codex 的 skill-installer 从本仓库安装，提供相应路径：

- `skills/development/xp-review-flow`
- `skills/reverse-engineering/xp-re-notes`
- `skills/workflow/xp-context-handoff`
- `skills/workflow/xp-status`
- `skills/workflow/xp-delegate`
- `skills/reverse-engineering/xp-ida-struct`
- `skills/reverse-engineering/xp-debug-diff`
- `skills/reverse-engineering/xp-save-analysis`

## 独立代码审阅

```text
$xp-review-flow 审阅刚写的上传流程，检查失败重试和并发写入，不要改代码。
```

支持指定文件、模块、提交、分支对比或业务流程；未指定范围时审阅当前未提交改动。返回 `BLOCK`、`APPROVE_WITH_COMMENTS` 或 `APPROVE`，问题包含严重程度、文件行号、触发条件和最小修法。

模型配置：[references/config.json](skills/development/xp-review-flow/references/config.json)，默认 `gpt-6.1-sol`、`xhigh`。模型 ID 与推理档位需由使用者的环境支持；不可用时停止并报错，不静默回退。

安装时可覆盖配置（仅适用于 xp-review-flow）：

```sh
python scripts/install.py --skill xp-review-flow --model gpt-6.1-sol --effort xhigh
```

```powershell
./scripts/install.ps1 -Skill xp-review-flow -Model gpt-6.1-sol -Effort xhigh
```

此技能需要支持指定子智能体模型和推理强度的客户端。只读审阅是指令约束；子智能体继承父会话的 provider 和权限。审阅结论不等于 CI 强制门禁。

## 逆向分析笔记整理

```text
$xp-re-notes 总结 D:/analysis/game-notes 里的 MD，列出进度和待验证清单。
$xp-re-notes 整理 D:/analysis/save.md 中的存档数据结构，保留字段来源和未知项。
$xp-re-notes 给 D:/analysis/game-notes 生成交接摘要，方便下次继续分析。
```

保留来源文件、行号或章节、游戏版本和地址基准；区分有验证记录、推测、待验证与冲突。不同版本和磁盘/内存布局分别整理，不自行补造字段。不覆盖原始笔记或已有报告，新报告遵循当前工作区的输出目录约定。此技能整理已有资料，不代替实际逆向实验。

## IDA 结构恢复、调试对比与存档分析

```text
$xp-ida-struct 只读分析指定函数的对象布局，列出字段读写证据、候选类型和未知项，不改 IDB。
$xp-debug-diff 对比指定两份快照，说明变化范围，不把字节变化直接当成字段含义。
$xp-save-analysis 对比同版本存档，分析候选偏移与格式线索，另存报告，不覆盖原文件。
```

三个技能均由当前主模型执行，不固定模型或推理强度。报告使用中文，保留样本身份、地址/偏移基准、原始片段和证据来源；区分观察、推测、待验证与冲突。所有报告新建，默认不改目标内存、原二进制、IDB 或存档。

- **IDA 结构恢复**适配 Hex-Rays `reference` / `execute_python` 接口。先查实际 API，再读取指定数据库；默认仅输出结构候选和证据表，不自动写回类型或重命名。
- **调试状态对比**适配 `DHS_XDbg_MCP`，不依赖 `x64dbg_automate`。现场采集需要服务在线、有明确目标与范围；离线脚本读取 `xp-debug-snapshot-v1`，校验会话和目标身份，保留短读/失败范围，不自动做全进程转储。
- **存档格式分析**的离线脚本只依赖 Python 标准库，分析文件哈希、长度、熵、签名候选、固定偏移差异和数值窗口；不自动解压、解密或写回。高熵和单次差异不能证明加密算法或字段语义。

### 验证范围与连接要求

本地合成样本的 **42 项行为检查通过**，包括精确差异计数、身份/位宽校验、错误保留、预算限制、时间顺序提示及不覆盖输入。离线检查不代表真实游戏兼容性或 MCP 端到端成功。

本次开发环境中，IDA 文档接口可调用，但开库因无法加载 `idalib.dll` 失败；DHS 调试接口的 HTTP 8888 连接被拒绝。适配规则已记录这些错误识别方式：状态查询返回 false、甚至 `isError:false`，均不能独自证明服务在线。实时结构恢复和前后快照采集仍需在配置正确、目标可用的环境补测。安装技能不会自动安装或修复 IDA、调试器或其 MCP。

脚本格式及接口说明见各技能目录中的 `references/`；运行离线脚本时应使用实际安装路径，并提供新的输出目录。

## 上下文交接

切换模型、新开聊天或准备压缩上下文前，显式调用：

```text
$xp-context-handoff 保存当前任务到 D:/project/handoff，包含背景、关键决定、完成情况、证据来源和下一步计划。
```

保存位置遵循当前工作区的输出限制；未指定时使用工作区约定的输出目录。每次生成新的 UTF-8 Markdown 文档，不覆盖已有文件。报告保留目标与验收标准、用户约束、关键决定、文件/提交/测试证据、未决问题、下一步计划及可复制的恢复提示词，不复制密钥和令牌。

切换后指定实际文件路径继续：

```text
$xp-context-handoff 读取 D:/project/handoff/实际交接文件.md，核对当前工作区状态后继续下一步。
```

仅要求查看文档时不会执行计划。恢复时先核对现状，不将旧计划视为新的操作授权。它只能总结当前可见或可核实的信息，不能找回已丢失的上下文，也不提供切换模型前自动保存的保证。

## 大白话进度

```text
$xp-status 用大白话说说我们现在在干什么、做到哪了。
$xp-status 别讲太多技术细节，告诉我做完了什么，还差什么。
$xp-status 只说这次存档分析的进度，哪些确定了、哪些还没验证。
```

中文显示名称为 **XP · 大白话进度**，由当前主模型执行。默认直接在聊天中简短解释目标、当前进展、未完成事项和实际下一步，不自动保存文档、重新测试或操作仓库。它会区分计划、完成、测试通过和已上传，不把离线测试通过说成真实目标已验证，也不会编造完成百分比或待办。

它与上下文交接分工如下：

| 技能 | 适用需求 | 默认输出 |
|---|---|---|
| `xp-status` | 给用户快速讲清楚现在的情况 | 聊天内的大白话说明 |
| `xp-context-handoff` | 让切换后的模型能继续工作 | 包含背景、约束、证据与计划的新 MD 文档 |

## 子智能体接续

中文显示名称为 **XP · 子智能体接续**。它把当前目标、已完成事项、最新约束、关键文件和验收条件交给一个子智能体，由它接着执行，完成后在发起调用的主聊天汇报。不会另建普通聊天，也不会要求用户切到子窗口查结果。

```text
$xp-delegate 接着当前任务做，沿用当前模型，完成后在这里汇报。
$xp-delegate 用 gpt-6.1-sol、xhigh 继续当前未完成任务，做完回主聊天汇报。
```

每次读取技能目录中的 [references/config.json](skills/workflow/xp-delegate/references/config.json)，默认值是：

```json
{
  "model": "inherit",
  "reasoning_effort": "inherit"
}
```

`inherit` 动态跟随调用时主聊天选择的模型和推理设置，不锁定安装时的模型。两个字段分别按 **本次明确指定 > 用户维护的技能配置 > inherit 所指的主设置** 解析。例如，配置为 `gpt-6.1-sol` / `xhigh` 时今后默认指定它们；某次明确说“沿用当前”又可覆盖固定配置。指定值须由宿主实际支持，不可用时报告错误，不静默换模型。只影响执行子智能体，不修改主模型或全局设置。

附带的 `scripts/resolve_request.py` 负责验证配置和解析优先级，不负责启动子智能体，也不代替模型可用性检查。安装器的 `--model` / `-Model` 与 `--effort` / `-Effort` 仍仅用于 `xp-review-flow`；`xp-delegate` 请修改自己的配置或在本次调用中指定。

包含 [Codex 适配](skills/workflow/xp-delegate/references/codex.md)与 [Claude Code 适配](skills/workflow/xp-delegate/references/claude-code.md)。Codex 已实际测试默认继承及回传，父子本地运行日志均为 `gpt-6.1-sol` / `high`，该值是当时环境的观察结果，不是固定默认值；指定其他模型的实际启动及 Claude Code 路径尚未实测。Claude Code 安装目录为 `~/.claude/skills/xp-delegate`，调用示例为 `/xp-delegate`，宿主工具及模型限制仍需核对。

需要宿主提供可用的子智能体工具；安装技能不会自动配置模型、切换提供商或增加权限。历史继承不能保证每个细节都传达，关键决定仍放入明确简报；未完成任务、启动错误和验收缺口会如实回报。

## 仓库结构

```text
Codex/
├─ README.md
├─ skills/
│  ├─ development/
│  │  └─ xp-review-flow/
│  │     ├─ SKILL.md
│  │     ├─ agents/openai.yaml
│  │     └─ references/config.json
│  ├─ reverse-engineering/
│  │  ├─ xp-re-notes/
│  │  ├─ xp-ida-struct/
│  │  ├─ xp-debug-diff/
│  │  └─ xp-save-analysis/
│  └─ workflow/
│     ├─ xp-context-handoff/
│     │  ├─ SKILL.md
│     │  └─ agents/openai.yaml
│     ├─ xp-status/
│     │  ├─ SKILL.md
│     │  └─ agents/openai.yaml
│     └─ xp-delegate/
│        ├─ SKILL.md
│        ├─ agents/openai.yaml
│        ├─ references/
│        │  ├─ config.json
│        │  ├─ codex.md
│        │  └─ claude-code.md
│        └─ scripts/resolve_request.py
└─ scripts/
   ├─ install.py
   └─ install.ps1
```

旧版 `review-flow`、`re-notes`、`context-handoff` 现已分别更名为 `xp-review-flow`、`xp-re-notes`、`xp-context-handoff`。旧调用名不再作为独立技能保留。升级时先保留旧技能目录中的自定义配置，再安装新名称的技能，确认后移走旧目录，避免选择器同时出现新旧两份。

原来的 `skill/review-flow` 已迁移到 `skills/development/xp-review-flow`，根目录安装脚本已迁移至 `scripts/`，请使用本文的新路径。历史交接文档保留生成时的原始名称与路径，继续使用时请对照以上更名映射。
