"""Scientific data operations. Pure Python, no network and no executable input."""
from __future__ import annotations
from .i18n import tr

from dataclasses import dataclass
from collections import Counter
import json
import math
import re
from pathlib import Path

MAX_BASES = 100_000
MAX_FILE_BYTES = 12_000_000
IUPAC = frozenset('ACGTRYSWKMBDHVN')
COMPLEMENT = str.maketrans('ACGTRYSWKMBDHVN', 'TGCAYRSWMKVHDBN')
BASE_COLORS = {'A': '#53dfb0', 'T': '#f4b860', 'C': '#65b5ff', 'G': '#bd99ff'}
ELEMENT_COLORS = {'C': '#91a6b9', 'N': '#609fff', 'O': '#ff748c',
                  'S': '#f5d76e', 'P': '#ffb165', 'H': '#e6edf5', 'FE': '#d89b67'}
DEMO_DNA = 'ATGGCTTCTGGTAAAGACTACGAACTGACCGGTGCTTCCAAAGGTGACTTCTACGGTGCTTAA'
DEFAULT_CIRCUIT = {'operator': 'AND', 'input_a': 0.8, 'input_b': 0.6,
                   'transcription': 2.0, 'translation': 1.2,
                   'decay_m': 0.4, 'decay_p': 0.2, 'duration': 40.0}

# NCBI standard genetic code, codons ordered T,C,A,G in each position.
_BASE_ORDER = 'TCAG'
_AMINO = ('FFLLSSSSYY**CC*W' 'LLLLPPPPHHQQRRRR'
          'IIIMTTTTNNKKSSRR' 'VVVVAAAADDEEGGGG')
CODONS = dict(zip((a+b+c for a in _BASE_ORDER for b in _BASE_ORDER
                  for c in _BASE_ORDER), _AMINO))


def normalize_dna(text: str) -> str:
    """Whitespace is permitted. Other invalid symbols are never silently removed."""
    seq = ''.join(text.split()).upper()
    if not seq:
        raise ValueError(tr('A sequência está vazia.'))
    if len(seq) > MAX_BASES:
        raise ValueError(tr('Esta versão aceita até {0:,} bases por sequência.').format(MAX_BASES))
    invalid = sorted(set(seq) - IUPAC)
    if invalid:
        raise ValueError(tr('Símbolos inválidos para DNA: ') + ', '.join(invalid) +
                         tr('. Use A, C, G, T ou códigos de ambiguidade IUPAC.'))
    return seq


def reverse_complement(seq: str) -> str:
    return normalize_dna(seq).translate(COMPLEMENT)[::-1]


def parse_fasta(text: str) -> list[tuple[str, str]]:
    records, title, chunks = [], None, []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('>'):
            if title is not None:
                records.append((title, normalize_dna(''.join(chunks))))
            elif chunks:
                raise ValueError(tr('Há sequência antes do primeiro cabeçalho FASTA.'))
            title, chunks = line[1:].strip() or tr('Sem nome'), []
        else:
            chunks.append(line)
    if title is None:
        return [(tr('Sequência'), normalize_dna(''.join(chunks)))]
    records.append((title, normalize_dna(''.join(chunks))))
    return records


def parse_genbank(text: str) -> list[tuple[str, str]]:
    """Import ORIGIN sequences only; deliberately does not interpret FEATURES."""
    records = []
    for block in text.split('//'):
        if not block.strip():
            continue
        lines = block.splitlines()
        locus = next((line.split()[1] for line in lines
                      if line.startswith('LOCUS ') and len(line.split()) > 1), None)
        if locus is None:
            raise ValueError(tr('Registro GenBank sem linha LOCUS válida.'))
        origin = next((i for i, line in enumerate(lines) if line.strip() == 'ORIGIN'), None)
        if origin is None:
            raise ValueError(tr('GenBank sem sequência ORIGIN; registros CONTIG não são suportados.'))
        seq_lines = []
        for line in lines[origin+1:]:
            if not line.strip():
                continue
            if not re.fullmatch(r'\s*\d+\s+[A-Za-z\s]+', line):
                raise ValueError(tr('Linha inválida na seção ORIGIN do GenBank.'))
            seq_lines.append(re.sub(r'[\d\s]', '', line))
        records.append((locus, normalize_dna(''.join(seq_lines))))
    if not records:
        raise ValueError(tr('Nenhum registro GenBank encontrado.'))
    return records


def translate(seq: str, frame: int = 0) -> str:
    if frame not in (0, 1, 2):
        raise ValueError(tr('Quadro de leitura deve ser 0, 1 ou 2.'))
    seq = normalize_dna(seq)
    return ''.join(CODONS.get(seq[i:i+3], 'X') for i in range(frame, len(seq)-2, 3))


def sequence_stats(seq: str, frame: int = 0) -> dict:
    seq = normalize_dna(seq)
    counts = Counter(seq)
    canonical = sum(counts[b] for b in 'ACGT')
    protein = translate(seq, frame)
    return {'length': len(seq), 'canonical': canonical,
            'ambiguous': len(seq)-canonical,
            'gc_percent': 100*(counts['G']+counts['C'])/canonical if canonical else None,
            'protein': protein, 'stops': protein.count('*'),
            'trailing_bases': max(0, len(seq)-frame) % 3}


def positional_difference(original: str, current: str) -> dict:
    """A positional comparison, explicitly not an evolutionary alignment."""
    return {'mismatches': sum(a != b for a, b in zip(original, current)),
            'length_delta': len(current)-len(original)}


def fasta_text(name: str, seq: str) -> str:
    seq = normalize_dna(seq)
    title = ' '.join(name.split()).replace('>', '') or 'BioForma'
    return '>'+title+'\n'+'\n'.join(seq[i:i+80] for i in range(0, len(seq), 80))+'\n'


@dataclass(frozen=True)
class Atom:
    x: float
    y: float
    z: float
    element: str
    name: str
    chain: str
    residue: str
    resname: str
    segment: int = 0


def parse_pdb(text: str) -> tuple[list[Atom], dict]:
    """First coordinate model, one conformer (blank/A) per atom identity."""
    atoms, seen, skipped, model_seen = [], set(), 0, False
    segment = 0
    for line in text.splitlines():
        record = line[:6].strip()
        if record == 'MODEL':
            if model_seen or atoms:
                break
            model_seen = True
        if record == 'ENDMDL':
            break
        if record == 'TER':
            segment += 1
        if record not in ('ATOM', 'HETATM'):
            continue
        if len(line) < 54:
            raise ValueError(tr('Linha de coordenadas PDB incompleta.'))
        if line[16] not in (' ', 'A'):
            skipped += 1
            continue
        atom_field = line[12:16]
        name = atom_field.strip()
        chain, residue, resname = line[21], line[22:27].strip(), line[17:20].strip()
        key = (record, chain, residue, resname, name, segment)
        if key in seen:
            skipped += 1
            continue
        try:
            x, y, z = (float(line[a:b]) for a,b in ((30,38),(38,46),(46,54)))
        except ValueError as exc:
            raise ValueError(tr('Coordenadas PDB inválidas.')) from exc
        if not all(math.isfinite(v) for v in (x,y,z)):
            raise ValueError(tr('O PDB contém coordenadas não finitas.'))
        if any(abs(v) > 1_000_000 for v in (x,y,z)):
            raise ValueError(tr('Coordenadas fora do intervalo aceito pelo visor PDB.'))
        element = line[76:78].strip().upper() if len(line) >= 78 else ''
        if not element:
            letters = re.sub('[^A-Za-z]', '', atom_field)
            element = (letters[:1] if atom_field.startswith(' ') or atom_field[0].isdigit()
                       else letters[:2]).upper() or 'C'
        atoms.append(Atom(x,y,z,element,name,chain,residue,resname,segment))
        seen.add(key)
        if len(atoms) > 50_000:
            raise ValueError(tr('Esta versão aceita PDB com até 50.000 átomos no primeiro modelo.'))
    if not atoms:
        raise ValueError(tr('Nenhum átomo compatível encontrado no primeiro modelo PDB.'))
    return atoms, {'atoms': len(atoms), 'alternate_skipped': skipped,
                   'chains': len({a.chain for a in atoms})}


def validate_circuit(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) != set(DEFAULT_CIRCUIT):
        raise ValueError(tr('Use exatamente os campos do exemplo de circuito.'))
    if data['operator'] not in ('AND', 'OR', 'NOT_A', 'XOR'):
        raise ValueError(tr('Operador permitido: AND, OR, NOT_A ou XOR.'))
    result = {'operator': data['operator']}
    limits = {'input_a': (0,1), 'input_b': (0,1), 'transcription': (0,10),
              'translation': (0,10), 'decay_m': (.01,5),
              'decay_p': (.01,5), 'duration': (1,300)}
    for key,(low,high) in limits.items():
        v = data[key]
        if isinstance(v, bool) or not isinstance(v, (float,int)) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(tr('{0}: informe um número entre {1} e {2}.').format(key, low, high))
        result[key] = float(v)
    return result


def simulate_circuit(data: dict) -> dict:
    """Analytic solution of a two-stage, constant-input expression toy model."""
    c = validate_circuit(data)
    a,b = c['input_a'], c['input_b']
    u = {'AND': a*b, 'OR': a+b-a*b, 'NOT_A': 1-a, 'XOR': a*(1-b)+b*(1-a)}[c['operator']]
    km, kp, dm, dp = (c[k] for k in ('transcription','translation','decay_m','decay_p'))
    m_inf = km*u/dm
    p_inf = kp*m_inf/dp
    points = []
    for i in range(501):
        # Preserve exact final endpoint (multiply after the normalized fraction).
        t = c['duration']*(i/500)
        m = m_inf*(-math.expm1(-dm*t))
        # Stable divided difference; no subtraction of nearly equal exponentials.
        delta = abs(dp-dm)
        integral = (t*math.exp(-dp*t) if delta == 0
                    else math.exp(-min(dm,dp)*t)*(-math.expm1(-delta*t))/delta)
        p = max(0., kp*m_inf*((-math.expm1(-dp*t))/dp-integral))
        points.append((t,m,p))
    return {'input':u, 'points':points, 'm_equilibrium':m_inf, 'p_equilibrium':p_inf}


def read_small(path: str | Path) -> str:
    path = Path(path)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(tr('Arquivo maior que o limite de 12 MB desta versão.'))
    return path.read_text(encoding='utf-8-sig')


def validate_project(data: dict) -> dict:
    if not isinstance(data, dict) or data.get('format') != 'bioforma' or data.get('version') != 1:
        raise ValueError(tr('Formato/versão de projeto não reconhecido.'))
    for key in ('name','sequence','baseline','pdb_text'):
        if not isinstance(data.get(key), str):
            raise ValueError(tr('Campo de projeto inválido: {0}.').format(key))
    if len(data['name']) > 500:
        raise ValueError(tr('Nome de projeto longo demais.'))
    result = dict(data)
    from .references import validate_source
    for field in ('sequence_source','pdb_source'):
        if field in data:
            result[field]=validate_source(data[field])
    result['sequence'] = normalize_dna(data['sequence'])
    result['baseline'] = normalize_dna(data['baseline'])
    result['circuit'] = validate_circuit(data.get('circuit'))
    if type(data.get('frame',0)) is not int or data.get('frame',0) not in (0,1,2):
        raise ValueError(tr('Quadro de leitura inválido.'))
    if data['pdb_text']:
        parse_pdb(data['pdb_text'])
    return result


def atomic_write(path: str | Path, text: str) -> None:
    import os
    import tempfile
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.bioforma-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
