@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHON="
py -3.13 -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON=py -3.13"
if defined PYTHON goto python_found
py -3.12 -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON=py -3.12"
if defined PYTHON goto python_found
py -3.11 -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON=py -3.11"
if defined PYTHON goto python_found
python -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON=python"
if not defined PYTHON goto fail

:python_found
%PYTHON% -c "import sys; print('Using Python',sys.version.split()[0])"
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe -c "import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>nul
  if errorlevel 1 .venv\Scripts\python.exe -m venv --clear .venv
) else (
  %PYTHON% -m venv .venv
)
if errorlevel 1 goto fail
if defined FLOORFORGE_WHEELHOUSE (
  .venv\Scripts\python.exe -m pip install --disable-pip-version-check --no-index --find-links "%FLOORFORGE_WHEELHOUSE%" -r requirements.lock.txt
) else (
  .venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.lock.txt
)
if errorlevel 1 goto fail
.venv\Scripts\python.exe scripts\smoke.py
if errorlevel 1 goto fail
for /f "delims=" %%H in ('%PYTHON% -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('requirements.lock.txt').read_bytes()).hexdigest())"') do set "LOCK_HASH=%%H"
>.venv\.floorforge-ready echo python=managed
>>.venv\.floorforge-ready echo requirements_sha256=%LOCK_HASH%
echo Setup complete. Double-click FloorForge.bat to start.
exit /b 0

:fail
echo Setup failed. Check Python 3.11-3.13, network access and available disk space.
echo No global Python packages were changed. Retry after fixing the issue.
exit /b 1
