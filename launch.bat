@echo off
REM Double-click to start the website at http://localhost:8000 (keep this window open)
cd /d "%~dp0"
if not exist logs mkdir logs
echo %date% %time% launcher started in %cd% > logs\launcher.log
if not exist .venv\Scripts\python.exe goto needsetup
echo %time% checking installed packages... >> logs\launcher.log
.venv\Scripts\python.exe -c "import uvicorn, fastapi, langchain_groq" >nul 2>&1
if errorlevel 1 goto needsetup
goto run

:needsetup
echo %time% packages missing, calling install.bat >> logs\launcher.log
echo Packages are not installed yet - running setup first (5-10 minutes, do not click inside this window)...
call "%~dp0install.bat"
echo %time% install.bat returned >> logs\launcher.log

:run
echo %time% starting server >> logs\launcher.log
echo Starting the website... it will open in your browser in about 10 seconds.
start "" cmd /c "timeout /t 10 >nul & start http://localhost:8000"
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload --reload-dir app --reload-dir knowledge --reload-include "*.md" >> logs\server.log 2>&1
echo %time% server stopped >> logs\launcher.log
echo The website stopped. See logs\server.log
pause
