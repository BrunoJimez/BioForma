import json
import math
from pathlib import Path
import tempfile
import unittest

from bioforma.core import *
from bioforma.example import demo_pdb
from bioforma.viewer import dna_geometry, pdb_geometry


class SequenceTests(unittest.TestCase):
    def test_translation_known_and_ambiguous(self):
        self.assertEqual(translate('ATGGCTTGGTAA'), 'MAW*')
        self.assertEqual(translate('ATGNNNTGA'), 'MX*')
        self.assertEqual(translate('AATGGCT',1), 'MA')
        self.assertEqual(translate('AA',2),'')
        self.assertEqual(len(CODONS),64)
        self.assertEqual({c for c,a in CODONS.items() if a=='*'}, {'TAA','TAG','TGA'})

    def test_fasta_multiple_and_roundtrip(self):
        records=parse_fasta('>first\natg c\n>second\nTTAN\n')
        self.assertEqual(records,[('first','ATGC'),('second','TTAN')])
        for name,seq in records:
            self.assertEqual(parse_fasta(fasta_text(name,seq)),[(name,seq)])

    def test_reject_malformed_dna(self):
        for bad in ('','ATGU','ATG123','ACT-','ACT!'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                normalize_dna(bad)
        for bad in ('>empty\n','ACT\n>name\nACGT'):
            with self.assertRaises(ValueError): parse_fasta(bad)

    def test_reverse_complement_iupac(self):
        seq='ACGTRYSWKMBDHVN'
        self.assertEqual(reverse_complement(reverse_complement(seq)),seq)
        self.assertEqual(reverse_complement('ATGC'),'GCAT')

    def test_gc_excludes_ambiguity(self):
        self.assertEqual(sequence_stats('GCNN')['gc_percent'],100)
        self.assertIsNone(sequence_stats('NNN')['gc_percent'])
        self.assertEqual(sequence_stats('ATGG')['trailing_bases'],1)

    def test_genbank_sequence_only(self):
        gb='LOCUS       TOY 6 bp DNA\nFEATURES             Location/Qualifiers\nORIGIN\n        1 atgtaa\n//\n'
        self.assertEqual(parse_genbank(gb),[('TOY','ATGTAA')])
        with self.assertRaises(ValueError): parse_genbank('LOCUS X\nCONTIG elsewhere\n//')

    def test_geometry_complement_and_range(self):
        points,links=dna_geometry('ATGC',1,10,'ATGC')
        self.assertEqual(len(points),6)
        self.assertEqual(points[0].label,'T')
        self.assertEqual(points[1].label,'A')
        self.assertAlmostEqual(math.dist(points[0].xyz,points[1].xyz),20)


class StructureTests(unittest.TestCase):
    def test_pdb_geometry_and_carbon_alpha(self):
        atoms,info=parse_pdb(demo_pdb())
        self.assertEqual(info['atoms'],32)
        self.assertEqual(atoms[0].element,'C')
        points,links,total=pdb_geometry(atoms,'trace')
        self.assertEqual((len(points),len(links),total),(32,31,32))

    def test_first_model_and_altloc(self):
        atom=demo_pdb().splitlines()[2]
        alt=atom[:16]+'B'+atom[17:]
        pdb='MODEL        1\n'+atom+'\n'+alt+'\nENDMDL\nMODEL        2\n'+atom+'\nENDMDL'
        atoms,info=parse_pdb(pdb)
        self.assertEqual(len(atoms),1)
        self.assertEqual(info['alternate_skipped'],1)

    def test_reject_nonfinite_coordinate(self):
        atom=demo_pdb().splitlines()[2]
        with self.assertRaises(ValueError):
            parse_pdb(atom[:30]+f'{"nan":>8}'+atom[38:])

    def test_chain_break_not_connected(self):
        atoms,_=parse_pdb(demo_pdb())
        a=atoms[1]
        atoms[1]=Atom(a.x,a.y,a.z,a.element,a.name,'B',a.residue,a.resname)
        _,links,_=pdb_geometry(atoms,'trace')
        self.assertFalse(any((x,y)==(0,1) for x,y,*_ in links))

    def test_ter_break_not_connected(self):
        rows=demo_pdb().splitlines()
        atoms,_=parse_pdb('\n'.join(rows[:3]+['TER']+rows[3:]))
        _,links,_=pdb_geometry(atoms,'trace')
        self.assertEqual(len(links),30)

    def test_reject_overflowing_geometry(self):
        atom=demo_pdb().splitlines()[2]
        with self.assertRaises(ValueError):
            parse_pdb(atom[:30]+f'{"1e200":>8}'+atom[38:])


class CircuitTests(unittest.TestCase):
    def test_boolean_limits(self):
        for operator,expected in [('AND',[0,0,0,1]),('OR',[0,1,1,1]),('XOR',[0,1,1,0]),('NOT_A',[1,1,0,0])]:
            for (a,b),y in zip([(0,0),(0,1),(1,0),(1,1)],expected):
                result=simulate_circuit(dict(DEFAULT_CIRCUIT,operator=operator,input_a=a,input_b=b))
                self.assertEqual(result['input'],y)

    def test_initial_and_equilibrium(self):
        r=simulate_circuit(dict(DEFAULT_CIRCUIT,duration=300))
        self.assertEqual(r['points'][0],(0,0,0))
        self.assertAlmostEqual(r['points'][-1][1],r['m_equilibrium'],places=8)
        self.assertAlmostEqual(r['points'][-1][2],r['p_equilibrium'],places=8)
        self.assertTrue(all(m>=0 and p>=0 for _,m,p in r['points']))

    def test_equal_degradation_closed_form(self):
        data=dict(DEFAULT_CIRCUIT,decay_m=.3,decay_p=.3)
        r=simulate_circuit(data)
        t,m,p=r['points'][-1]
        expected=r['p_equilibrium']*(1-math.exp(-.3*t)*(1+.3*t))
        self.assertAlmostEqual(p,expected,places=10)

    def test_analytical_against_independent_rk4(self):
        # Independent numerical integration of the ODE, including two decay orderings.
        for dm,dp in ((.4,.2),(.2,.4),(.3,.3)):
            data=dict(DEFAULT_CIRCUIT,decay_m=dm,decay_p=dp,duration=5)
            r=simulate_circuit(data)
            m=p=0.
            dt=.001
            def f(m,p):
                return data['transcription']*.8*.6-dm*m,data['translation']*m-dp*p
            for _ in range(5000):
                a,b=f(m,p)
                c,d=f(m+dt*a/2,p+dt*b/2)
                e,g=f(m+dt*c/2,p+dt*d/2)
                h,j=f(m+dt*e,p+dt*g)
                m+=dt*(a+2*c+2*e+h)/6
                p+=dt*(b+2*d+2*g+j)/6
            self.assertAlmostEqual(r['points'][-1][1],m,places=8)
            self.assertAlmostEqual(r['points'][-1][2],p,places=8)

    def test_parameter_validation(self):
        for key,value in [('input_a',2),('decay_m',0),('duration',float('nan')),('translation',True),('operator','exec')]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                simulate_circuit(dict(DEFAULT_CIRCUIT,**{key:value}))


class ProjectTests(unittest.TestCase):
    def test_project_persists_all_data(self):
        p={'format':'bioforma','version':1,'name':'Projeto ç','sequence':DEMO_DNA,
           'baseline':DEMO_DNA,'frame':2,'pdb_text':demo_pdb(),'circuit':DEFAULT_CIRCUIT}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'projeto.json'
            atomic_write(path,json.dumps(p,ensure_ascii=False))
            self.assertEqual(validate_project(json.loads(read_small(path))),p)
            p['sequence']='ATG'
            atomic_write(path,json.dumps(p))
            self.assertEqual(json.loads(read_small(path))['sequence'],'ATG')

    def test_invalid_project(self):
        with self.assertRaises(ValueError): validate_project({'format':'other'})


if __name__=='__main__':
    unittest.main()
