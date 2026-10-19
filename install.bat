@echo off
REM Double-click to install everything and run the self-tests. Report: logs\setup.log
cd /d "%~dp0"
if not exist logs mkdir logs
echo %time% install.bat started >> logs\launcher.log
if not exist .env copy .env.example .env >nul

set "BASEPY="
if exist "%USERPROFILE%\anaconda3\python.exe" set "BASEPY=%USERPROFILE%\anaconda3\python.exe"
if not defined BASEPY set "BASEPY=python"
echo %time% base python: %BASEPY% >> logs\launcher.log

if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment with %BASEPY% - takes about a minute, please wait...
  "%BASEPY%" -m venv .venv > logs\venv.log 2>&1
)
if not exist .venv\Scripts\python.exe (
  echo Could not create .venv - see logs\venv.log
  echo %time% VENV FAILED >> logs\launcher.log
  pause
  exit /b 1
)

echo %time% running scripts\setup.py >> logs\launcher.log
echo Installing packages and running tests. This can take 5-10 minutes the first time. Please do not click inside this window...
.venv\Scripts\python.exe scripts\setup.py
echo %time% setup.py exited with code %errorlevel% >> logs\launcher.log
echo.
echo Setup finished.
