@echo off
cd /d "%~dp0"
if not exist node_modules call npm install --no-audit --no-fund
if errorlevel 1 goto end
if not exist .env (
  copy .env.example .env
  echo Edit .env to enter your MySQL password, then start again.
  goto end
)
call npm start
:end
pause
