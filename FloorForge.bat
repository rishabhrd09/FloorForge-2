@echo off
cd /d "%~dp0"
call start.bat %*
if errorlevel 1 pause
