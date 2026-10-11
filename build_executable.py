"""Build on the target OS. Application runtime itself needs no pip dependencies."""
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
from bioforma import __version__


def build():
    root=Path(__file__).resolve().parent
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed',
                    '--onedir','--name','BioFormaStudio',str(root/'main.py')],cwd=root,check=True)
    folder=root/'dist/BioFormaStudio'
    executable=folder/('BioFormaStudio.exe' if sys.platform=='win32' else 'BioFormaStudio')
    if not executable.is_file():raise RuntimeError('Expected native executable was not produced.')
    for name in ('LICENSE','README.md','README.pt-BR.md','CITATION.cff','VALIDACAO.md'):
        shutil.copy2(root/name,folder/name)
    for name in ('exemplos','docs','referencias'):
        shutil.copytree(root/name,folder/name,dirs_exist_ok=True)
    import PyInstaller
    manifest={'software_version':__version__,'python':platform.python_version(),
              'platform':platform.platform(),'pyinstaller':PyInstaller.__version__,'files':{}}
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            digest=hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
            manifest['files'][path.relative_to(folder).as_posix()]=digest.hexdigest()
    (folder/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    os_name='Windows' if sys.platform=='win32' else 'Linux'
    format_name='zip' if sys.platform=='win32' else 'gztar'
    archive=shutil.make_archive(str(root/'dist'/f'BioFormaStudio-{os_name}-{__version__}'),format_name,
                                root_dir=root/'dist',base_dir='BioFormaStudio')
    print('Built:',executable)
    print('Archive:',archive)
    print('Native compatibility depends on the build OS. A target-machine check is still required.')


if __name__=='__main__':build()
