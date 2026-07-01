# install.ps1 — install shopify-theme-builder as a Claude Code / Claude apps skill (Windows).
# For other agents (Codex, Cursor, Windsurf) you don't need this: keep the repo
# in your project — they read AGENTS.md / .cursor/ / .windsurf/ directly.
#
# Usage:
#   ./install.ps1            # install to %USERPROFILE%\.claude\skills (all projects)
#   ./install.ps1 -Project   # install to .\.claude\skills (current project)
param([switch]$Project)

$ErrorActionPreference = 'Stop'
$SrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillName = 'shopify-theme-builder'

if ($Project) {
  $DestRoot = Join-Path (Get-Location) '.claude\skills'
} else {
  $DestRoot = Join-Path $env:USERPROFILE '.claude\skills'
}

$Dest = Join-Path $DestRoot $SkillName
New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
Copy-Item -Recurse -Force $SrcDir $Dest

foreach ($x in @('.git', '.cursor', '.windsurf', 'node_modules')) {
  $p = Join-Path $Dest $x
  if (Test-Path $p) { Remove-Item -Recurse -Force $p }
}

Write-Host "Installed '$SkillName' -> $Dest"
Write-Host 'Restart Claude Code (or start a new session), then ask: "build a Shopify theme".'
