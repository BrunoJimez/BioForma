import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bioforma.core import DEFAULT_CIRCUIT,validate_project
from bioforma.references import catalog,load_reference,fetch_ncbi,validate_source,sha256,local_source
from bioforma.reproducibility import make_record


class ReferenceTests(unittest.TestCase):
    def test_reference_identity_and_provenance_roundtrip(self):
        reference=load_reference(0)
        seq=reference['sequence']
        project={'format':'bioforma','version':1,'name':reference['name'],
                 'sequence':seq,'baseline':seq,'pdb_text':'','circuit':DEFAULT_CIRCUIT,
                 'frame':0,'sequence_source':reference['source']}
        loaded=validate_project(json.loads(json.dumps(project)))
        self.assertEqual(project,loaded)
        self.assertTrue(make_record(loaded)['results']['sequence_source_match'])
        loaded['sequence']='A'+seq[1:]
        if loaded['sequence']==seq:loaded['sequence']='T'+seq[1:]
        self.assertFalse(make_record(loaded)['results']['sequence_source_match'])
        self.assertEqual(loaded['sequence_source'],reference['source'])

    def test_all_offline_references_have_validated_sources(self):
        for i in range(len(catalog())):
            record=load_reference(i)
            self.assertEqual(validate_source(record['source']),record['source'])

    def test_pdb_raw_hash_and_stored_text_hash_distinguish_line_endings(self):
        record=load_reference(2)
        text=record['text']
        raw=text.replace('\n','\r\n').encode('utf-8')
        source=local_source(raw,'windows.pdb',text=text)
        self.assertNotEqual(source['file_sha256'],source['text_sha256'])
        project={'format':'bioforma','version':1,'name':'crambin','sequence':'ATG',
                 'baseline':'ATG','pdb_text':text,'circuit':DEFAULT_CIRCUIT,'pdb_source':source}
        self.assertTrue(make_record(project)['results']['pdb_source_match'])
        project['pdb_text']+='REMARK  edited\n'
        self.assertFalse(make_record(project)['results']['pdb_source_match'])

    def test_tampered_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'manifest.json').write_text(json.dumps({'records':[{'files':{'fasta':{
                'path':'example.fasta','sha256':'0'*64}}}]}))
            (root/'example.fasta').write_text('>example\nATG\n')
            with patch('bioforma.references.reference_dir',return_value=root):
                with self.assertRaises(ValueError):load_reference(0)

    def test_network_response_version_and_size_checked(self):
        raw=b'>NR_027552.1 example\nACGT\n'
        calls=[]
        def opener(request,timeout):
            calls.append((request.full_url,timeout))
            return io.BytesIO(raw)
        result=fetch_ncbi(' nr_027552.1 ',opener=opener)
        self.assertEqual(result['sequence'],'ACGT')
        self.assertEqual(result['source']['file_sha256'],sha256(raw))
        self.assertEqual(calls[0][1],20)
        self.assertTrue(calls[0][0].startswith('https://eutils.ncbi.nlm.nih.gov/'))
        for data in (b'<html>error</html>',b'>NR_027552.2 wrong version\nACGT\n',
                     b'>NR_027552.1\nACGT\n>OTHER.1\nACGT\n',b'>NR_027552.1\nACGU\n'):
            with self.subTest(data=data),self.assertRaises(ValueError):
                fetch_ncbi('NR_027552.1',opener=lambda *a,**kw:io.BytesIO(data))
        with patch('bioforma.core.MAX_FILE_BYTES',5),self.assertRaises(ValueError):
            fetch_ncbi('NR_027552.1',opener=opener)

    def test_invalid_accession_never_contacts_server(self):
        for accession in ('NR_027552','https://example.com','NR_027552.1&secret=1',''):
            with self.subTest(accession=accession),patch('bioforma.references.urlopen') as network:
                with self.assertRaises(ValueError):fetch_ncbi(accession)
                network.assert_not_called()

    def test_provenance_metadata_has_bounded_schema(self):
        for source in ({'kind':'local_file'}, {'kind':'other','file_sha256':'0'*64},
                       {'kind':'local_file','file_sha256':'wrong'},
                       {'kind':'local_file','file_sha256':'0'*64,'unknown':1}):
            with self.subTest(source=source),self.assertRaises(ValueError):validate_source(source)


if __name__=='__main__':unittest.main()
