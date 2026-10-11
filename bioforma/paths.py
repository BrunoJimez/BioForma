"""User-owned platform paths. No admin privileges required."""
import os
import sys
from pathlib import Path

UI_FONT = 'Segoe UI' if sys.platform == 'win32' else 'DejaVu Sans'
MONO_FONT = 'Consolas' if sys.platform == 'win32' else 'DejaVu Sans Mono'


def config_dir():
    override = os.environ.get('BIOFORMA_CONFIG_DIR')
    if override:
        return Path(override).expanduser()
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home())))/'BioFormaStudio'
    return Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'bioforma-studio'


def log_dir():
    if os.environ.get('BIOFORMA_CONFIG_DIR') or sys.platform == 'win32':
        return config_dir()/'logs'
    return Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state')))/'bioforma-studio'/'logs'


def preferences_path():
    return config_dir()/'settings.json'


def load_language(path=None):
    import json
    try:
        p = Path(path) if path is not None else preferences_path()
        if p.stat().st_size > 4096:
            return 'pt'
        data = json.loads(p.read_text(encoding='utf-8'))
        language = data.get('language') if isinstance(data,dict) else None
        return language if language in ('pt','en') else 'pt'
    except (OSError,ValueError,UnicodeError):
        return 'pt'


def save_language(language, path=None):
    import json
    from .core import atomic_write
    if language not in ('pt','en'):
        raise ValueError('Language must be pt or en.')
    p = Path(path) if path is not None else preferences_path()
    p.parent.mkdir(parents=True,exist_ok=True)
    atomic_write(p,json.dumps({'language':language},indent=2)+'\n')
