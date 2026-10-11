import json
from pathlib import Path
from string import Formatter
import tempfile
import unittest
from bioforma.core import DEFAULT_CIRCUIT, DEMO_DNA, normalize_dna, simulate_circuit, sequence_stats
from bioforma.example import demo_pdb
from bioforma.guides import get_help
from bioforma.i18n import set_language,tr,translate_existing
from bioforma.paths import load_language,save_language
from bioforma.reproducibility import make_record
from bioforma.translations import EN


class LanguageTests(unittest.TestCase):
    def tearDown(self):
        set_language('pt')

    def test_catalog_format_arguments_are_preserved(self):
        def fields(text):
            return sorted((field,spec,conversion or '') for _,field,spec,conversion in Formatter().parse(text) if field is not None)
        for key,value in EN.items():
            with self.subTest(key=key):self.assertEqual(fields(key),fields(value))

    def test_bidirectional_labels_and_help(self):
        set_language('en')
        self.assertEqual(tr('Salvar projeto'),'Save project')
        self.assertIn('QUICK GUIDE',get_help())
        self.assertEqual(translate_existing('Save project','en','pt'),'Salvar projeto')
        set_language('pt')
        self.assertIn('GUIA RÁPIDO',get_help())

    def test_errors_follow_selected_language(self):
        set_language('en')
        with self.assertRaisesRegex(ValueError,'empty'):normalize_dna('')
        set_language('pt')
        with self.assertRaisesRegex(ValueError,'vazia'):normalize_dna('')

    def test_engine_results_are_language_invariant(self):
        set_language('pt')
        pt=(sequence_stats(DEMO_DNA),simulate_circuit(DEFAULT_CIRCUIT))
        set_language('en')
        self.assertEqual(pt,(sequence_stats(DEMO_DNA),simulate_circuit(DEFAULT_CIRCUIT)))

    def test_preferences_roundtrip_and_bad_file_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'nested/settings.json'
            self.assertEqual(load_language(path),'pt')
            save_language('en',path)
            self.assertEqual(load_language(path),'en')
            path.write_text('{bad')
            self.assertEqual(load_language(path),'pt')
            path.write_text('["en"]')
            self.assertEqual(load_language(path),'pt')

    def test_record_is_reproducible_across_language(self):
        project={'format':'bioforma','version':1,'name':'Unchanged data name','sequence':DEMO_DNA,
                 'baseline':DEMO_DNA,'frame':0,'pdb_text':demo_pdb(),'circuit':DEFAULT_CIRCUIT}
        set_language('pt');a=make_record(project,'pt')
        set_language('en');b=make_record(project,'en')
        self.assertEqual(a['sha256'],b['sha256'])
        self.assertEqual(a['results'],b['results'])
        self.assertEqual(a['project'],b['project'])
        self.assertEqual(a['scientific_status']['biological_validation'],'not performed')
        self.assertEqual(a['scientific_status']['structure_origin'],'artificial_geometry')


if __name__=='__main__':unittest.main()
