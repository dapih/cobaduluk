# One-command install for Cursor, Codex, Kilo, OpenCode, Antigravity, OpenClaw, etc.
# Usage (from your project root):
#   irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
# Or:
#   .\install.ps1 [-Dest excel-to-json] [-NonInteractive]

param(
    [string]$Dest = "excel-to-json",
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/dapih/cobaduluk.git"

if (-not (Test-Path "$Dest/skills/excel-to-json/scripts/bootstrap.py")) {
    Write-Host "-> clone $Repo -> $Dest"
    git clone --depth 1 $Repo $Dest
}

$bootstrapArgs = @()
if (-not $NonInteractive) {
    $bootstrapArgs += "--interactive"
}

python "$Dest/skills/excel-to-json/scripts/bootstrap.py" @bootstrapArgs
