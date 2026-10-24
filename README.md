# Codex 技能合集

按用途分类维护的 Codex 技能。仓库中的分类目录用于浏览，安装后每个技能仍是独立文件夹。

个人技能统一使用 `xp-` 前缀，界面显示为 `XP · 中文名称`。在技能选择器中输入 `xp-` 可集中查找这三个技能。

## 技能目录

| 分类 | 技能 | 功能 |
|---|---|---|
| 开发 | [xp-review-flow：独立代码审阅](skills/development/xp-review-flow/SKILL.md) | 启动独立审阅子智能体，检查缺陷、回归风险和测试缺口，提供结论与整改方案 |
| 逆向分析 | [xp-re-notes：逆向分析笔记整理](skills/reverse-engineering/xp-re-notes/SKILL.md) | 总结本地 MD、整理数据结构、生成交接摘要，保留来源与不确定项，另存结果 |
| 工作流 | [xp-context-handoff：上下文交接](skills/workflow/xp-context-handoff/SKILL.md) | 切换模型或聊天前保存任务背景、决定、进展和下一步计划，读取交接文档接续工作 |

## 安装

克隆本仓库后在仓库根目录执行。Python 安装器需要 Python 3；Windows 的 PowerShell 安装器可独立使用。

```sh
python scripts/install.py --skill xp-review-flow
python scripts/install.py --skill xp-re-notes
python scripts/install.py --skill xp-context-handoff
```

```powershell
./scripts/install.ps1 -Skill xp-review-flow
./scripts/install.ps1 -Skill xp-re-notes
./scripts/install.ps1 -Skill xp-context-handoff
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
│  │  └─ xp-re-notes/
│  │     ├─ SKILL.md
│  │     └─ agents/openai.yaml
│  └─ workflow/
│     └─ xp-context-handoff/
│        ├─ SKILL.md
│        └─ agents/openai.yaml
└─ scripts/
   ├─ install.py
   └─ install.ps1
```

旧版 `review-flow`、`re-notes`、`context-handoff` 现已分别更名为 `xp-review-flow`、`xp-re-notes`、`xp-context-handoff`。旧调用名不再作为独立技能保留。升级时先保留旧技能目录中的自定义配置，再安装新名称的技能，确认后移走旧目录，避免选择器同时出现新旧两份。

原来的 `skill/review-flow` 已迁移到 `skills/development/xp-review-flow`，根目录安装脚本已迁移至 `scripts/`，请使用本文的新路径。历史交接文档保留生成时的原始名称与路径，继续使用时请对照以上更名映射。
