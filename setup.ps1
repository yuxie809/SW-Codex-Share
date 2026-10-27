param([string]$Python = '', [switch]$Mcp)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
function CheckExit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed (exit $LASTEXITCODE)" }
}
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    if ($Python) { & $Python -m venv .venv }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { & python -m venv .venv }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv .venv }
    else { throw 'Install 64-bit Python 3.10+ and rerun setup.ps1.' }
    CheckExit 'Create virtual environment'
}
$VenvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $VenvPython -c "import sys,struct; assert sys.version_info >= (3,10) and struct.calcsize('P') == 8, 'Use 64-bit Python 3.10+'"
CheckExit 'Python compatibility'
& $VenvPython -m pip install -r requirements.txt
CheckExit 'Install dependencies'
& $VenvPython -m pip check
CheckExit 'Dependency consistency'
if ($Mcp) {
    $ConfigDir = Join-Path $PSScriptRoot '.codex'
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    $ConfigFile = Join-Path $ConfigDir 'config.toml'
    if (Test-Path -LiteralPath $ConfigFile) { throw 'Project config already exists. See README; it was not overwritten.' }
    $ServerPath = (Join-Path $PSScriptRoot 'mcp_server.py').Replace('\','/')
    $CommandPath = $VenvPython.Replace('\','/')
    # TOML literal strings preserve Windows paths. Single quotes in a folder
    # name require manual setup, rather than writing an invalid config.
    if ($ServerPath.Contains("'") -or $CommandPath.Contains("'")) { throw 'Use a folder without single quotes for MCP setup.' }
    @"
[mcp_servers.sw_codex_share]
command = '$CommandPath'
args = ['-X', 'utf8', '$ServerPath']
startup_timeout_sec = 60
tool_timeout_sec = 180
"@ | Set-Content -LiteralPath $ConfigFile -Encoding utf8
}
Write-Host 'Setup complete. Run: .\.venv\Scripts\python.exe -X utf8 test_connection.py'
