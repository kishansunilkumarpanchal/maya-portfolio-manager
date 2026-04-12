@echo off
echo ======================================
echo Checking dependencies...
echo ======================================
python -m pip install -r requirements.txt

echo.
echo ======================================
echo Starting Maya Portfolio Manager (PostgreSQL)...
echo ======================================
python app_v2.py
pause
