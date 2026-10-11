@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 main.py
goto finish
:try_python
python main.py
:finish
if errorlevel 1 pause
