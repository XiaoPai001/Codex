# review-flow

`review-flow` 是一个 Codex skill。它让一个独立的强推理子智能体审阅刚完成
的代码或业务流程，检查缺陷、边界情况、回归风险和测试缺口，返回审批结论
与修改方案。

它不会修改代码。它的模型和推理强度独立于当前负责写代码的模型。

## 安装

要求：支持自定义子智能体的 Codex 客户端。安装器需要 Python 3；
Windows 也可以直接用 PowerShell 安装脚本。

### 任意平台（推荐）

克隆仓库后，在仓库根目录运行：

```sh
python3 install.py
```

Windows 上通常是 `python install.py`。

### Windows PowerShell

```powershell
./install.ps1
```

两个安装器行为一致。

默认安装到用户级目录 `~/.agents/skills/review-flow`，对任何仓库都生效。
Codex 同时会扫描 `$CODEX_HOME/skills`（默认 `~/.codex/skills`）。想让审阅能力
跨仓库生效，装到这两处之一即可；想只给某个仓库用，就装到该仓库的
`.agents/skills`。
也可以安装到某个仓库的 `.agents/skills/review-flow`，让团队随仓库共享：

```powershell
./install.ps1 -Destination .agents/skills/review-flow
```

```sh
python3 install.py --dest .agents/skills/review-flow
```

如果目标已存在，需要显式加 `-Force` 或 `--force`。两个安装器都只接受
名为 `review-flow` 的目标目录，不会替换其他目录。

## 修改模型 ID

模型配置唯一存放在：

```text
skill/review-flow/references/config.json
```

也可以在安装时覆盖：

```powershell
./install.ps1 -Model "cn:mimo-v2.6-pro" -Effort "high"
```

```sh
python3 install.py --model "cn:mimo-v2.6-pro" --effort "high"
```

仓库里的默认值是 `ccs-qoder-2/qmodel_38max`，它来自维护这台机器时的模型目录。
换到另一台电脑时先确认该 ID 在本机可用，不可用就按上面的方式改成本机的
强模型 ID。

安装后修改已安装副本的 `references/config.json` 即可，不需要重启 Codex。
模型 ID 必须与当前环境的模型目录中的 `slug` 完全一致；推理强度必须是该
模型实际支持的档位。模型不可用时，skill 会停止并报错，不会静默降级成
父智能体的模型。

## 使用

在 Codex 中显式调用：

```text
$review-flow 审阅刚写的上传流程，重点检查失败重试和并发写入。不要改代码。
```

审阅范围可以是未提交改动、指定文件或模块、某个提交、分支对比，或整条
业务流程。没有指定范围时，默认审阅当前未提交的改动。

返回格式：

- `BLOCK`：存在必须先修的问题
- `APPROVE_WITH_COMMENTS`：修复建议不阻塞，但建议处理
- `APPROVE`：未发现可执行缺陷

每条问题包含严重级别、`文件:行号`、出错原因、触发场景和最小修法。

## 它与内置 Review Agent 的区别

Codex 自带的 `review-agent` 会在当前会话里直接审阅，使用的是当前会话模型。
`review-flow` 会启动单独的审阅子智能体，并使用配置中的模型，因此适合
“弱模型干活、强模型审批”的流程。

## 边界

- 审阅是技术结论，不是不可绕过的安全门禁。需要强制拦截时，再把测试或
  审阅接入 CI / Git hook。
- 子智能体继承父会话的 provider、沙箱、审批策略、MCP 和权限。这里切换
  的是模型与推理强度，不能单独切换到另一套 provider。
- “不修改文件”是指令约束。需要严格只读时，应在父会话使用只读权限。
- 自定义子智能体需要当前 Codex 版本支持；技能框架本身不等于多智能体能力。

各平台的 skill 路径与子智能体行为以 OpenAI 官方文档为准：

- [Build skills](https://developers.openai.com/codex/skills/)
- [Subagents](https://developers.openai.com/codex/subagents/)

## 仓库结构

```text
.
|-- README.md
|-- install.py
|-- install.ps1
`-- skill/
    `-- review-flow/
        |-- SKILL.md
        |-- agents/
        |   `-- openai.yaml
        `-- references/
            `-- config.json
```
