@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 verificar_interface.py
goto finish
:try_python
python verificar_interface.py
:finish
pause
