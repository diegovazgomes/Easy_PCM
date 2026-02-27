@echo off
echo Encerrando servidores...

REM Mata processos uvicorn
taskkill /F /IM uvicorn.exe >nul 2>&1

REM Mata processos python que estejam rodando uvicorn
taskkill /F /IM python.exe >nul 2>&1

REM Mata ngrok
taskkill /F /IM ngrok.exe >nul 2>&1

echo Servidores encerrados.
pause