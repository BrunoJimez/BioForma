"""Install under XDG user folders with a launcher and .desktop entry."""
import os
from pathlib import Path
import shlex
import shutil
import sys


def desktop_quote(value):
    # Desktop Entry Exec quoting is not shell quoting. % must be escaped as %%.
    value=str(value).replace('%','%%')
    for char in ('\\','"','`','$'):
        value=value.replace(char,'\\'+char)
    return '"'+value+'"'


def install():
    if not sys.platform.startswith('linux'):
        raise RuntimeError('Use INSTALAR_WINDOWS.cmd on Windows / Use no Windows.')
    if sys.version_info < (3,10):
        raise RuntimeError('Python 3.10+ is required / Python 3.10+ é necessário.')
    try:
        import tkinter
    except ImportError as exc:
        raise RuntimeError('Install Tkinter / Instale Tkinter. Ubuntu/Mint/Debian: sudo apt install python3-tk') from exc
    source=Path(__file__).resolve().parent
    data_root=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share'))).expanduser()
    destination=data_root/'bioforma-studio'/'app-0.3.0'
    destination.mkdir(parents=True,exist_ok=True)
    if source != destination.resolve():
        for name in ('main.py','README.md','README.pt-BR.md','VALIDACAO.md'):
            shutil.copy2(source/name,destination/name)
        for name in ('bioforma','exemplos','docs','referencias'):
            shutil.copytree(source/name,destination/name,dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    bin_dir=Path(os.environ.get('BIOFORMA_BIN_DIR',str(Path.home()/'.local/bin'))).expanduser()
    bin_dir.mkdir(parents=True,exist_ok=True)
    launcher=bin_dir/'bioforma-studio'
    launcher.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+
                        shlex.quote(str(destination/'main.py'))+' "$@"\n',encoding='utf-8')
    launcher.chmod(0o755)
    apps=data_root/'applications'
    apps.mkdir(parents=True,exist_ok=True)
    desktop=apps/'bioforma-studio.desktop'
    desktop.write_text('[Desktop Entry]\nVersion=1.0\nType=Application\nName=BioForma Studio\n'
                       'Comment=Educational DNA and molecular modeling workbench\n'
                       'Comment[pt_BR]=Bancada didática de DNA e modelos moleculares\n'
                       'Exec='+desktop_quote(launcher)+'\nTerminal=false\n'
                       'Icon=applications-science\nCategories=Education;Science;\n',encoding='utf-8')
    print('Installed / Instalado:',destination)
    print('Open from the applications menu / Abra pelo menu de aplicativos: BioForma Studio')
    print('Direct launch / Abertura direta:',shlex.quote(str(launcher)))
    print('Uninstall by removing these paths / Para desinstalar, remova estes caminhos:')
    for path in (destination,launcher,desktop):print(path)
    return destination,launcher,desktop


if __name__=='__main__':
    try:
        install()
    except (OSError,RuntimeError) as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(1)
