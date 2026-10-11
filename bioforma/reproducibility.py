"""Self-contained records for computational reproducibility, not biological validation."""
import hashlib
import json
import platform
from datetime import datetime, timezone
from . import __version__
from .core import validate_project, sequence_stats, simulate_circuit, parse_pdb


def canonical_hash(data):
    serialized=json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def make_record(project,language='pt'):
    data=validate_project(project)
    from .references import sha256
    results={'sequence':sequence_stats(data['sequence'],data.get('frame',0)),
             'circuit':simulate_circuit(data['circuit'])}
    source=data.get('sequence_source')
    if source and 'sequence_sha256' in source:
        results['sequence_source_match']=sha256(data['sequence'].encode('ascii'))==source['sequence_sha256']
    if data.get('pdb_source'):
        results['pdb_source_match']=sha256(data['pdb_text'].encode('utf-8'))==data['pdb_source'].get('text_sha256',data['pdb_source']['file_sha256'])
    if data['pdb_text']:
        _,info=parse_pdb(data['pdb_text'])
        results['pdb']=info
    return {
        'record_format':'bioforma-reproducibility', 'record_version':1,
        'generated_utc':datetime.now(timezone.utc).isoformat(),
        'software':{'name':'BioForma Studio','version':__version__,
                    'python':platform.python_version(),'platform':platform.platform(),
                    'ui_language':language},
        'algorithm':{'translation':'NCBI standard genetic code; ambiguous codons=X',
                     'gc':'G+C divided by A+C+G+T; None when denominator is zero',
                     'circuit':'two_stage_linear_constant_input_analytic_expm1_v2',
                     'pdb':'legacy PDB; first model; A/blank altloc; TER-aware trace'},
        'units':'arbitrary compatible units for time, expression and circuit rates',
        'scientific_status':{
            'computational_tests':'see VALIDACAO.md; test execution is not certified by this record',
            'biological_validation':'not performed',
            'structure_origin':'artificial_geometry' if 'BIOFORMA GEOMETRIC DEMO' in data['pdb_text']
                              else 'not_verified' if data['pdb_text'] else 'none',
            'organism_prediction':'not implemented'},
        'project':data,
        'results':results,
        'sha256':{'project':canonical_hash(data),'results':canonical_hash(results)},
    }
