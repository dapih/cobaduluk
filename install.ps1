# One-command install for Cursor, Codex, Kilo, OpenCode, Antigravity, OpenClaw, etc.
# Usage (from your project root):
#   irm https://raw.githubusercontent.com/dapih/cobaduluk/main/install.ps1 | iex
# Or:
#   .\install.ps1 [-Dest excel-to-json]

param(
    [string]$Dest = "excel-to-json"
)

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/dapih/cobaduluk.git"

if (-not (Test-Path "$Dest/scripts/bootstrap.py")) {
    Write-Host "-> clone $Repo -> $Dest"
    git clone --depth 1 $Repo $Dest
}

python "$Dest/scripts/bootstrap.py"
