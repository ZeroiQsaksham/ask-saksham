@echo off
REM Double-click to publish the current project to https://github.com/ZeroiQsaksham/ask-saksham
REM Uses your own Git login on this computer. Report: logs\publish.log
cd /d "%~dp0"
if not exist logs mkdir logs
set LOG=logs\publish.log
echo %date% %time% publish started > %LOG%
git --version >> %LOG% 2>&1
if errorlevel 1 (
  echo Git is not installed. >> %LOG%
  echo Git is not installed - see logs\publish.log
  pause
  exit /b 1
)
if not exist .git (
  git init -b main >> %LOG% 2>&1
  git remote add origin https://github.com/ZeroiQsaksham/ask-saksham.git >> %LOG% 2>&1
)
git config user.name "Saksham Pandey"
git config user.email "ZeroiQsaksham@users.noreply.github.com"
git config core.autocrlf false
echo Fetching the current version from GitHub...
git fetch origin main >> %LOG% 2>&1
if errorlevel 1 (
  echo FETCH FAILED >> %LOG%
  echo Could not reach GitHub - see logs\publish.log
  pause
  exit /b 1
)
git reset origin/main >> %LOG% 2>&1
git add -A >> %LOG% 2>&1
echo ---- changes ---- >> %LOG%
git status --short >> %LOG% 2>&1
git diff --cached --quiet && (
  echo Nothing new to publish. >> %LOG%
  echo Nothing new to publish.
  pause
  exit /b 0
)
if not exist logs\commit_message.txt echo Update project> logs\commit_message.txt
git commit -F logs\commit_message.txt >> %LOG% 2>&1
echo Uploading to GitHub (a GitHub sign-in window may appear the first time - sign in there)...
git push origin HEAD:main >> %LOG% 2>&1
if errorlevel 1 (
  echo PUSH FAILED >> %LOG%
  echo Upload failed - see logs\publish.log
  pause
  exit /b 1
)
echo PUBLISHED OK >> %LOG%
REM Reset the message so the next publish does not reuse it
echo Update knowledge base> logs\commit_message.txt
echo Published! https://github.com/ZeroiQsaksham/ask-saksham
pause
