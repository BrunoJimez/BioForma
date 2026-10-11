"""Versioned, hash-checked reference fixtures and optional NCBI FASTA retrieval.

No scientific annotations are inferred. Network responses are bounded and never
executed. The installed application has no third-party runtime dependencies.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .i18n import tr


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def reference_dir():
    root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    return root/'referencias'


def catalog():
    return json.loads((reference_dir()/'manifest.json').read_text(encoding='utf-8'))['records']


def validate_source(source):
    if source is None:
        return None
    if not isinstance(source, dict) or len(source) > 12:
        raise ValueError(tr('Metadados de origem inválidos.'))
    allowed = {'kind','label','accession','provider','record_url','download_url',
               'retrieved_utc','file_sha256','sequence_sha256','text_sha256','molecule_note'}
    if set(source)-allowed or not all(isinstance(v,str) and len(v)<=2000 for v in source.values()):
        raise ValueError(tr('Metadados de origem inválidos.'))
    if source.get('kind') not in ('local_file','ncbi_reference','rcsb_reference'):
        raise ValueError(tr('Metadados de origem inválidos.'))
    for field in ('file_sha256','sequence_sha256','text_sha256'):
        if field in source and not re.fullmatch('[0-9a-f]{64}',source[field]):
            raise ValueError(tr('Metadados de origem inválidos.'))
    if 'file_sha256' not in source:
        raise ValueError(tr('Metadados de origem inválidos.'))
    return dict(source)


def local_source(raw, label, sequence=None, text=None):
    result={'kind':'local_file','label':Path(label).name,'file_sha256':sha256(raw)}
    if sequence is not None:
        result['sequence_sha256']=sha256(sequence.encode('ascii'))
    if text is not None:
        result['text_sha256']=sha256(text.encode('utf-8'))
    return result


def load_reference(index):
    from .core import parse_fasta,parse_pdb,MAX_FILE_BYTES
    record=catalog()[index]
    fmt='fasta' if 'fasta' in record['files'] else 'pdb'
    info=record['files'][fmt]
    name=info['path']
    if Path(name).name!=name:
        raise ValueError(tr('Caminho de referência inválido.'))
    path=reference_dir()/name
    if path.stat().st_size>MAX_FILE_BYTES:
        raise ValueError(tr('Arquivo maior que o limite de 12 MB desta versão.'))
    raw=path.read_bytes()
    if sha256(raw)!=info['sha256']:
        raise ValueError(tr('A referência foi alterada: SHA-256 não confere.'))
    text=raw.decode('utf-8')
    source={'kind':'ncbi_reference' if fmt=='fasta' else 'rcsb_reference',
            'label':record['accession'],'accession':record['accession'],
            'provider':record['provider'],'record_url':record['record_url'],
            'download_url':info['download_url'],'retrieved_utc':record['retrieved_utc'],
            'file_sha256':info['sha256'],'molecule_note':record.get('molecule_note','')}
    if fmt=='fasta':
        records=parse_fasta(text)
        if len(records)!=1 or records[0][0].split()[0]!=record['accession']:
            raise ValueError(tr('Identificador da sequência não confere com a referência.'))
        name,seq=records[0]
        source['sequence_sha256']=sha256(seq.encode('ascii'))
        return {'format':fmt,'name':name,'sequence':seq,'text':text,'source':source}
    parse_pdb(text)
    source['text_sha256']=sha256(text.encode('utf-8'))
    return {'format':fmt,'name':record['accession'],'text':text,'source':source}


def fetch_ncbi(accession, opener=None):
    """One versioned nucleotide accession. Timeout 20 s; response <=12 MB.

    Consumers call this on a worker thread. No Tk or local-file writes occur here.
    Versioned accessions identify sequence versions; raw-file hashes additionally
    identify the fetched representation, whose annotations may change over time.
    """
    from .core import parse_fasta,MAX_FILE_BYTES
    accession=accession.strip().upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9_]{2,24}\.\d{1,4}',accession):
        raise ValueError(tr('Use um acesso com versão, por exemplo NR_027552.1.'))
    query=urlencode({'db':'nuccore','id':accession,'rettype':'fasta','retmode':'text','tool':'BioFormaStudio'})
    url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+query
    request=Request(url,headers={'User-Agent':'BioFormaStudio/0.3.0'})
    with (opener or urlopen)(request,timeout=20) as response:
        raw=response.read(MAX_FILE_BYTES+1)
    if len(raw)>MAX_FILE_BYTES:
        raise ValueError(tr('Arquivo maior que o limite de 12 MB desta versão.'))
    text=raw.decode('utf-8-sig')
    if not text.startswith('>'):
        raise ValueError(tr('O NCBI não retornou um registro FASTA válido.'))
    records=parse_fasta(text)
    if len(records)!=1 or records[0][0].split()[0]!=accession:
        raise ValueError(tr('Identificador da sequência não confere com a referência.'))
    name,seq=records[0]
    source={'kind':'ncbi_reference','label':accession,'accession':accession,
            'provider':'NCBI Nucleotide','record_url':'https://www.ncbi.nlm.nih.gov/nuccore/'+accession,
            'download_url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
            'file_sha256':sha256(raw),'sequence_sha256':sha256(seq.encode('ascii'))}
    return {'format':'fasta','name':name,'sequence':seq,'text':text,'source':source}
