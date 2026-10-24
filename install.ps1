[CmdletBinding()]
param(
    [string]$Model,
    [string]$Effort,
    [string]$Destination,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $repoRoot "skill\review-flow"
$configPath = Join-Path $source "references\config.json"

if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md") -PathType Leaf)) {
    throw "Skill source not found at $source"
}

$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Model) { $config.reviewer_model = $Model }
if ($Effort) { $config.reviewer_reasoning_effort = $Effort }

if (-not $Destination) {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    $Destination = Join-Path $homeDir ".agents\skills\review-flow"
} else {
    if (-not [System.IO.Path]::IsPathRooted($Destination)) {
        $Destination = Join-Path (Get-Location) $Destination
    }
}

$Destination = [System.IO.Path]::GetFullPath($Destination)
if ((Split-Path -Leaf $Destination) -ne 'review-flow') {
    throw "Refusing to install to a directory not named review-flow: $Destination"
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

Write-Host "Installed review-flow to $Destination"
Write-Host "reviewer_model            = $($check.reviewer_model)"
Write-Host "reviewer_reasoning_effort = $($check.reviewer_reasoning_effort)"
Write-Host "Restart Codex or start a new chat if the skill does not appear."
