@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo Gera um executavel Windows no proprio Windows. Requer internet nesta etapa.
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -m venv .buildenv
goto build
:try_python
python -m venv .buildenv
:build
if errorlevel 1 goto fail
".buildenv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto fail
".buildenv\Scripts\python.exe" build_executable.py
if errorlevel 1 goto fail
echo.
echo Pronto: dist\BioFormaStudio\BioFormaStudio.exe
echo Para distribuir, copie a pasta inteira dist\BioFormaStudio, incluindo _internal.
echo O computador de destino nao precisa ter Python instalado.
goto finish
:fail
echo Falha na compilacao. Leia o erro acima. Nenhum executavel foi confirmado como pronto.
:finish
pause
