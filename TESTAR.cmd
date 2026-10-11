@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -m unittest discover -s tests -v
goto finish
:try_python
python -m unittest discover -s tests -v
:finish
pause
