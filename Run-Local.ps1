$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$workspacePython = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\work\.venv\Scripts\python.exe'))
if (Test-Path -LiteralPath $localPython) {
    $appPython = $localPython
} elseif (Test-Path -LiteralPath $workspacePython) {
    $appPython = $workspacePython
} else {
    Write-Host 'Install Python 3.12, then run the setup commands from README.md.'
    exit 1
}
$env:KIVY_HOME = Join-Path $PSScriptRoot '.local\kivy'
& $appPython main.py
exit $LASTEXITCODE
