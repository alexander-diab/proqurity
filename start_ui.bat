@echo off
REM Startet die Befund-Weboberflaeche. Doppelklick genuegt.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if not exist ".venv\Scripts\python.exe" (
  echo Kein venv gefunden. Zuerst:
  echo   py -3.11 -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
echo Starte Befund UI ...
start "" http://127.0.0.1:8000
.venv\Scripts\python.exe -m app.web.server
pause
