"""Windows entry point; errors are logged under the user's application data."""
import os
import sys
import traceback
from pathlib import Path


def run():
    try:
        import argparse
        from bioforma import __version__
        parser=argparse.ArgumentParser(description='BioForma Studio desktop workbench')
        parser.add_argument('--language',choices=('pt','en'),help='Interface language; otherwise use saved preference')
        parser.add_argument('--version',action='version',version=__version__)
        args=parser.parse_args()
        from bioforma.app import main
        main(language=args.language)
    except Exception:
        from bioforma.paths import log_dir
        from bioforma.i18n import tr
        folder=log_dir()
        folder.mkdir(parents=True,exist_ok=True)
        log=folder/'erro.log'
        log.write_text(traceback.format_exc(),encoding='utf-8')
        try:
            from tkinter import messagebox
            messagebox.showerror('BioForma Studio',tr('Não foi possível iniciar.\nDiagnóstico: {0}').format(log))
        except Exception:
            pass
        print(traceback.format_exc(),file=sys.stderr)
        raise SystemExit(1)


if __name__=='__main__':
    run()
