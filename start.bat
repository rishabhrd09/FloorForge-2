@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto setup
if not exist ".venv\.floorforge-ready" goto setup
.venv\Scripts\python.exe -c "import sys,numpy,shapely,trimesh,ezdxf,reportlab,PIL,scipy,networkx,pyparsing,typing_extensions,fontTools,charset_normalizer; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>nul
if errorlevel 1 goto setup
for /f "delims=" %%H in ('.venv\Scripts\python.exe -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('requirements.lock.txt').read_bytes()).hexdigest())"') do set "LOCK_HASH=%%H"
findstr /x /c:"requirements_sha256=%LOCK_HASH%" .venv\.floorforge-ready >nul 2>nul
if errorlevel 1 goto setup
.venv\Scripts\python.exe -m floorforge serve %*
exit /b %errorlevel%

:setup
call setup.bat
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m floorforge serve %*
exit /b %errorlevel%
