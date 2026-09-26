$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if ($env:OS -ne "Windows_NT") { throw "Run this recipe on Windows." }
& .\setup.bat
if ($LASTEXITCODE -ne 0) { throw "Python setup failed" }
& .\.venv\Scripts\python.exe -m pip install -r requirements-packaging.txt
if ($LASTEXITCODE -ne 0) { throw "Packaging dependency installation failed" }
& .\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm packaging\FloorForge.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
$compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($compiler) {
  & $compiler.Source packaging\FloorForge.iss
  if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }
} else {
  Write-Host "Portable build is in dist\FloorForge. Install Inno Setup and compile packaging\FloorForge.iss for a wizard installer."
}
Write-Host "Unsigned output only. Authenticode signing and clean-machine testing remain release gates."
