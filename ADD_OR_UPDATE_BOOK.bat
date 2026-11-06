@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 BOOK_UPDATE.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python BOOK_UPDATE.py
  ) else (
    echo Python 3 is required. Please install Python 3 from python.org.
    pause
  )
)
if errorlevel 1 pause
