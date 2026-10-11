"""Per-user installation. No elevation, package downloads, or PATH changes."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Este instalador é destinado ao Windows. Em Linux, execute main.py.')
    if sys.version_info < (3,10):
        raise RuntimeError('Instale Python 3.12 (64 bits) com Tcl/Tk em https://www.python.org/downloads/windows/')
    import tkinter
    root=tkinter.Tk()
    root.withdraw()
    root.destroy()
    source=Path(__file__).resolve().parent
    destination=Path(os.environ['LOCALAPPDATA'])/'BioFormaStudio'/'app-0.3.0'
    destination.mkdir(parents=True,exist_ok=True)
    if destination.resolve() != source.resolve():
        for filename in ('main.py','README.md','README.pt-BR.md','VALIDACAO.md'):
            shutil.copy2(source/filename,destination/filename)
        for folder in ('bioforma','exemplos','docs','referencias'):
            shutil.copytree(source/folder,destination/folder,dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    pythonw=Path(sys.executable).with_name('pythonw.exe')
    if not pythonw.exists():
        pythonw=Path(sys.executable)
    command='''$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'BioForma Studio.lnk'))
$shortcut.TargetPath = $env:BIOFORMA_PYTHON
$shortcut.Arguments = '"' + (Join-Path $env:BIOFORMA_FOLDER 'main.py') + '"'
$shortcut.WorkingDirectory = $env:BIOFORMA_FOLDER
$shortcut.Description = 'BioForma Studio - bancada digital de biologia'
$shortcut.Save()
'''
    env=dict(os.environ,BIOFORMA_PYTHON=str(pythonw),BIOFORMA_FOLDER=str(destination))
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],
                          env=env,capture_output=True,text=True)
    # A .cmd fallback is always available even if COM/desktop access is restricted.
    launcher=destination/'ABRIR.cmd'
    launcher.write_text('@echo off\nchcp 65001 >nul\n"'+str(Path(sys.executable))+'" "'+str(destination/'main.py')+'"\nif errorlevel 1 pause\n',encoding='utf-8')
    print('\nInstalado em:',destination)
    if result.returncode:
        print('Nao foi possivel criar o atalho. Use:',launcher)
        print(result.stderr.strip())
    else:
        print('Atalho criado na Area de Trabalho: BioForma Studio')
    print('Abra o atalho para iniciar. O aplicativo funciona offline.')
    print('Desinstalacao: apague a pasta app-0.3.0 acima e o atalho. Seus projetos nao sao removidos.')


if __name__=='__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        print('\nInstalacao nao concluida. Confira o Python, o componente Tcl/Tk e as permissoes da pasta.')
        raise SystemExit(1)
