import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from install_linux import desktop_quote,install


class LinuxInstallTests(unittest.TestCase):
    def test_desktop_exec_quotes_special_characters(self):
        quoted=desktop_quote('/path with spaces/$cash%"quote')
        self.assertTrue(quoted.startswith('"') and quoted.endswith('"'))
        self.assertIn('\\$cash%%',quoted)
        self.assertIn('\\"quote',quoted)

    @unittest.skipUnless(sys.platform.startswith('linux'),'Linux installer target only')
    def test_install_in_user_owned_xdg_paths(self):
        with tempfile.TemporaryDirectory(prefix='bioforma path ') as folder:
            data=Path(folder)/'data'
            binary=Path(folder)/'bin'
            with patch.dict(os.environ,{'XDG_DATA_HOME':str(data),'BIOFORMA_BIN_DIR':str(binary)}):
                destination,launcher,desktop=install()
            self.assertTrue((destination/'main.py').is_file())
            self.assertTrue((destination/'bioforma/translations.py').is_file())
            self.assertTrue(os.access(launcher,os.X_OK))
            self.assertIn(str(destination/'main.py'),launcher.read_text())
            self.assertIn('Exec="',desktop.read_text())
            self.assertIn('Name=BioForma Studio',desktop.read_text())
            launched=subprocess.run([str(launcher),'--version'],capture_output=True,text=True,check=True)
            self.assertEqual(launched.stdout.strip(),'0.3.0')


if __name__=='__main__':unittest.main()
