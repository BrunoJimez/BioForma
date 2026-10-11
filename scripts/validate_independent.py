"""Offline independent computational validation. Requires requirements-validation.txt.

Writes measured evidence and exits nonzero on any unmet criterion. It does not
validate biological behavior or automatically authorize a paper submission.
"""
import argparse
import hashlib
import io
import itertools
import json
from pathlib import Path
import platform
import random
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import Bio
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction
from Bio.PDB import PDBParser
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from bioforma import __version__
from bioforma.core import (parse_fasta,parse_genbank,parse_pdb,reverse_complement,
                          translate,sequence_stats,simulate_circuit,DEFAULT_CIRCUIT)
from bioforma.viewer import pdb_geometry


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    report={'schema':1,'software':'BioForma Studio','version':__version__,
            'generated_utc':datetime.now(timezone.utc).isoformat(),
            'environment':{'python':platform.python_version(),'platform':platform.platform(),
                           'biopython':Bio.__version__,'scipy':scipy.__version__,'numpy':np.__version__},
            'seed':20261010,'checks':[],'sequence_records':[],'ode_cases':[]}
    checks=report['checks']
    def check(name,ok,**details):
        checks.append({'name':name,'passed':bool(ok),**details})
    manifest=json.loads((ROOT/'referencias/manifest.json').read_text())
    for record in manifest['records']:
        for fmt,info in record['files'].items():
            path=ROOT/'referencias'/info['path']
            check('file_sha256:'+path.name,digest(path)==info['sha256'],sha256=digest(path))
        if 'fasta' not in record['files']:
            continue
        acc=record['accession']
        fa=(ROOT/'referencias'/record['files']['fasta']['path']).read_text()
        gb=(ROOT/'referencias'/record['files']['gb']['path']).read_text()
        ours_fa=parse_fasta(fa);ours_gb=parse_genbank(gb)
        ref_fa=SeqIO.read(io.StringIO(fa),'fasta')
        ref_gb=SeqIO.read(io.StringIO(gb),'genbank')
        seq=str(ref_fa.seq)
        check('FASTA_exact:'+acc,len(ours_fa)==1 and ours_fa[0][1]==seq and ref_fa.id==acc)
        check('GenBank_ORIGIN_exact:'+acc,len(ours_gb)==1 and ours_gb[0][1]==str(ref_gb.seq)==seq and ref_gb.id==acc)
        stats=sequence_stats(seq)
        expected_gc=100*gc_fraction(ref_fa.seq,ambiguous='remove')
        check('length_GC:'+acc,stats['length']==len(ref_fa.seq) and abs(stats['gc_percent']-expected_gc)<=1e-12)
        check('reverse_complement:'+acc,reverse_complement(seq)==str(ref_fa.seq.reverse_complement()))
        for frame in range(3):
            trimmed=seq[frame:frame+((len(seq)-frame)//3)*3]
            expected=str(Seq(trimmed).translate(table=1))
            check(f'translation_frame_{frame+1}:'+acc,translate(seq,frame)==expected)
        report['sequence_records'].append({'accession':acc,'length':len(seq),'gc_percent':stats['gc_percent'],
            'molecule_type':ref_gb.annotations.get('molecule_type'),
            'sequence_sha256':hashlib.sha256(seq.encode()).hexdigest()})
    codons=[''.join(c) for c in itertools.product('ACGT',repeat=3)]
    check('64_canonical_codons',all(translate(c)==str(Seq(c).translate()) for c in codons),cases=len(codons))
    alphabet='ACGTRYSWKMBDHVN'
    differences=[];policy_ok=True
    for bases in itertools.product(alphabet,repeat=3):
        codon=''.join(bases);ours=translate(codon);theirs=str(Seq(codon).translate())
        policy_ok &= ours==(theirs if set(codon)<=set('ACGT') else 'X')
        if ours!=theirs:
            differences.append({'codon':codon,'bioforma':ours,'biopython':theirs})
    check('3375_IUPAC_declared_policy',policy_ok,cases=15**3,
          comparator_differences=len(differences),interpretation='Intentional conservative X policy; not full consensus translation agreement.')
    report['iupac_differences']=differences
    pdb=(ROOT/'referencias/1CRN.pdb').read_text()
    ours,info=parse_pdb(pdb)
    ref=PDBParser(QUIET=True).get_structure('1CRN',io.StringIO(pdb))[0]
    atoms=list(ref.get_atoms())
    check('1CRN_atom_count',len(ours)==len(atoms),bioforma=len(ours),biopython=len(atoms))
    identities=[]
    for atom in atoms:
        residue=atom.get_parent();rid=residue.id
        identities.append((atom.name,atom.element,residue.get_parent().id,str(rid[1])+rid[2].strip(),residue.resname))
    check('1CRN_atom_identity',[(a.name,a.element,a.chain,a.residue,a.resname) for a in ours]==identities)
    coord_error=float(np.max(np.abs(np.array([(a.x,a.y,a.z) for a in ours])-np.array([a.coord for a in atoms])))) if len(ours)==len(atoms) else float('inf')
    check('1CRN_coordinates',coord_error<=.001,max_absolute_error_angstrom=coord_error,tolerance_angstrom=.001)
    pts,links,total=pdb_geometry(ours,'trace')
    check('1CRN_CA_trace',len(pts)==sum(a.name=='CA' for a in atoms)==46 and len(links)==45,points=len(pts),edges=len(links))
    cases=[]
    def add(label,**values):cases.append((label,dict(DEFAULT_CIRCUIT,**values)))
    for op in ('AND','OR','NOT_A','XOR'):
        add('default_'+op,operator=op)
        for a,b in ((0,0),(0,1),(1,0),(1,1)):
            add(f'endpoints_{op}_{a}_{b}',operator=op,input_a=a,input_b=b)
    add('zero_transcription',transcription=0)
    add('zero_translation',translation=0)
    for dm,dp in itertools.product((.01,5),repeat=2):
        add(f'decay_extrema_{dm}_{dp}',decay_m=dm,decay_p=dp,transcription=10,translation=10,duration=300)
    add('equal_decay',decay_m=.2,decay_p=.2)
    for delta in (1.1e-10,1e-8):
        add(f'near_equal_plus_{delta}',decay_m=.2,decay_p=.2+delta)
        add(f'near_equal_minus_{delta}',decay_m=.2+delta,decay_p=.2)
    for duration in (1,300):add(f'duration_{duration}',duration=duration)
    rng=random.Random(20261010)
    for i in range(80):
        add(f'random_{i}',operator=rng.choice(('AND','OR','NOT_A','XOR')),input_a=rng.random(),input_b=rng.random(),
            transcription=rng.uniform(0,10),translation=rng.uniform(0,10),
            decay_m=rng.uniform(.01,5),decay_p=rng.uniform(.01,5),duration=rng.uniform(1,300))
    for label,c in cases:
        a,b=c['input_a'],c['input_b']
        if c['operator']=='AND':u=a*b
        elif c['operator']=='OR':u=1-(1-a)*(1-b)
        elif c['operator']=='NOT_A':u=1-a
        else:u=a*(1-b)+(1-a)*b
        points=np.array(simulate_circuit(c)['points'])
        def rhs(t,y):
            return [c['transcription']*u-c['decay_m']*y[0],c['translation']*y[0]-c['decay_p']*y[1]]
        ref=solve_ivp(rhs,(0,c['duration']),(0,0),method='DOP853',t_eval=points[:,0],rtol=1e-11,atol=1e-13)
        error=np.abs(points[:,1:]-ref.y.T)
        tolerance=1e-7+1e-6*np.abs(ref.y.T)
        ok=ref.success and np.all(error<=tolerance)
        row={'case':label,'parameters':c,'passed':bool(ok),'max_absolute_error':float(error.max()),
             'max_tolerance_ratio':float(np.max(error/tolerance)),'timepoints':len(points)}
        report['ode_cases'].append(row)
    check('ODE_SciPy_DOP853',all(c['passed'] for c in report['ode_cases']),cases=len(cases),
          total_timepoints=len(cases)*501,atol=1e-7,rtol=1e-6,
          max_absolute_error=max(c['max_absolute_error'] for c in report['ode_cases']),
          max_tolerance_ratio=max(c['max_tolerance_ratio'] for c in report['ode_cases']))
    sources=list((ROOT/'bioforma').glob('*.py'))+[Path(__file__),ROOT/'validacao/PROTOCOL.md',ROOT/'requirements-validation.txt']
    report['source_sha256']={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}
    report['fixture_manifest_sha256']=digest(ROOT/'referencias/manifest.json')
    report['limitations']=['Developer-led small convenience sample; not peer review or a general accuracy estimate.',
        'No organism/phenotype prediction, gene annotation, folding or biological validation.',
        'PDB fixture has no altloc complexity; other PDB policies need a larger corpus.',
        'Ambiguous translation follows conservative X policy, with comparator differences disclosed.',
        'Independent library comparisons establish computational agreement for the measured cases only.']
    report['passed']=all(c['passed'] for c in checks)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT/'validacao/results_v0.3.0.json'))
    args=parser.parse_args()
    result=run()
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for check in result['checks']:
        print(('PASS' if check['passed'] else 'FAIL')+' '+check['name'])
    print('Report:',path)
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
