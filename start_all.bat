@echo off
cd /d "%~dp0"

REM libera execução só para esta chamada (sem mexer no Windows todo)
powershell -ExecutionPolicy Bypass -File ".\start_all.ps1"

pause
