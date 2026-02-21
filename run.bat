@echo off
title TERM FIRE RUNNER
cd /d "%~dp0"

echo [1/3] Checking dependencies...
python -m pip install -r requirements.txt

echo [2/3] Ensuring browsers are installed...
python -m playwright install chrome

echo [3/3] Launching TERM FIRE...
python term-fire.py

pause
