<#
.SYNOPSIS
安装本仓库的 XP 技能：代码审阅、逆向分析、笔记整理、上下文交接、进度说明与子智能体接续。
.PARAMETER Skill
技能标识；默认 xp-review-flow。仓库分类不影响本地安装目录名。
.PARAMETER Model
审阅模型 ID，仅用于 xp-review-flow。
.PARAMETER Effort
审阅推理强度，例如 xhigh（极高），仅用于 xp-review-flow。
.PARAMETER Destination
安装目录，末级目录名必须等于技能标识。
.PARAMETER Force
替换已有技能安装目录及其中的本地配置。
#>
[CmdletBinding()]
param(
    [ValidateSet('xp-review-flow', 'xp-re-notes', 'xp-context-handoff', 'xp-status', 'xp-delegate', 'xp-ida-struct', 'xp-debug-diff', 'xp-save-analysis')]
    [string]$Skill = 'xp-review-flow',
    [string]$Model,
    [string]$Effort,
    [string]$Destination,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
# 开发类 / 逆向分析类 / 工作流类：分类路径不影响本地安装目录名。
$categories = @{
    'xp-review-flow' = 'development'
    'xp-re-notes' = 'reverse-engineering'
    'xp-context-handoff' = 'workflow'
    'xp-status' = 'workflow'
    'xp-delegate' = 'workflow'
    'xp-ida-struct' = 'reverse-engineering'
    'xp-debug-diff' = 'reverse-engineering'
    'xp-save-analysis' = 'reverse-engineering'
}
$category = $categories[$Skill]
$source = Join-Path $repoRoot "skills\$category\$Skill"
$configPath = Join-Path $source "references\config.json"

if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md") -PathType Leaf)) {
    throw "Skill source not found at $source"
}

$config = $null
if ($Skill -eq 'xp-review-flow') {
    $config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
} elseif ($Model -or $Effort) {
    throw '-Model and -Effort apply only to xp-review-flow'
}
if ($Model) { $config.reviewer_model = $Model }
if ($Effort) { $config.reviewer_reasoning_effort = $Effort }
if ($null -ne $config -and (-not $config.reviewer_model -or -not $config.reviewer_reasoning_effort)) {
    throw "Reviewer configuration is incomplete: $configPath"
}

if (-not $Destination) {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    $Destination = Join-Path $homeDir ".agents\skills\$Skill"
} else {
    if (-not [System.IO.Path]::IsPathRooted($Destination)) {
        $Destination = Join-Path (Get-Location) $Destination
    }
}

$Destination = [System.IO.Path]::GetFullPath($Destination)
if ((Split-Path -Leaf $Destination) -ne $Skill) {
    throw "Refusing to install to a directory not named ${Skill}: $Destination"
}
# 在任何覆盖操作之前检查规范化路径，避免删除技能源目录。
$source = [System.IO.Path]::GetFullPath($source).TrimEnd('\', '/')
$Destination = $Destination.TrimEnd('\', '/')
if ($Destination -eq $source -or $Destination.StartsWith($source + '\', [System.StringComparison]::OrdinalIgnoreCase) -or $source.StartsWith($Destination + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Installation destination must not overlap skill source'
}
$skillsRoot = Split-Path -Parent $Destination
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null

if (Test-Path -LiteralPath $Destination) {
    if (-not $Force) {
        throw "$Destination already exists. Re-run with -Force to replace it."
    }
    Remove-Item -LiteralPath $Destination -Recurse -Force
}

Copy-Item -LiteralPath $source -Destination $Destination -Recurse

if ($null -ne $config) {
$installedConfig = Join-Path $Destination "references\config.json"
[System.IO.File]::WriteAllText(
    $installedConfig,
    ($config | ConvertTo-Json -Depth 3) + [Environment]::NewLine,
    (New-Object System.Text.UTF8Encoding($false))
)

$check = Get-Content -LiteralPath $installedConfig -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $check.reviewer_model -or -not $check.reviewer_reasoning_effort) {
    throw "Installed reviewer configuration is incomplete: $installedConfig"
}

Write-Host "reviewer_model            = $($check.reviewer_model)"
Write-Host "reviewer_reasoning_effort = $($check.reviewer_reasoning_effort)"
}
Write-Host "Installed $Skill to $Destination"
Write-Host "Restart Codex or start a new chat if the skill does not appear."
