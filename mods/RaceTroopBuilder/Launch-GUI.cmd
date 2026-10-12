@echo off
if not exist "%~dp0dist\RaceTroopBuilder-v0.3.0-win-x64\app\gui\RaceTroopBuilder.exe" (
  echo Please build first: powershell -File "%~dp0tools\build.ps1"
  pause
  exit /b 1
)
start "" "%~dp0dist\RaceTroopBuilder-v0.3.0-win-x64\app\gui\RaceTroopBuilder.exe" %*
