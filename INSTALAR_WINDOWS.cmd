@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo BioForma Studio 0.2 - instalacao local para Windows
echo Requer Python 3.10 ou superior com Tcl/Tk. Recomendado: Python 3.12 64 bits.
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 install_windows.py
goto finish
:try_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python install_windows.py
goto finish
:no_python
echo Python nao encontrado. Instale em https://www.python.org/downloads/windows/
echo Marque a instalacao do launcher py e Tcl/Tk. Depois execute este arquivo novamente.
:finish
pause
