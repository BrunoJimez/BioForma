# Computational validation protocol — BioForma 0.3

Defined on 2026-10-10 before running the complete v0.3 validation suite.
This is a small, developer-led verification study, not biological or external peer validation.

## Fixed public fixtures

NCBI RefSeq NR_027552.1 (Bacillus subtilis DSM 10 partial 16S rRNA locus),
NC_001422.1 (PhiX174 genome), each as FASTA and GenBank, and RCSB PDB 1CRN
(crambin). Raw source bytes, retrieval URLs/time and SHA-256 are frozen in
`referencias/manifest.json`. Two nucleotide records and one structure are a
convenience sample; they do not establish general accuracy on all taxa/formats.

## Acceptance criteria

1. FASTA and GenBank ORIGIN nucleotide strings match Biopython SeqIO exactly.
   Reference headers/version and manifest file hashes match. GenBank FEATURES
   are NOT imported or validated by BioForma.
2. Length, canonical-base GC and reverse complement match Biopython exactly
   (GC tolerance 1e-12 percentage points). All 64 unambiguous codons and three
   forward frames of both nucleotide records match Bio.Seq.translate(table=1)
   with incomplete terminal codons excluded. No CDS inference is asserted.
3. Exhaust all 15^3 IUPAC codons. BioForma's declared conservative policy is X
   for any ambiguous codon. Record differences from Biopython's consensus
   translation rather than hiding or calling them agreement.
4. First-model PDB atom count, identifiers, elements and coordinates match
   Biopython PDBParser for the 1CRN fixture. Coordinate tolerance 0.001 Angstrom.
   This fixture has no alternate-location ambiguity; it does not validate all
   altloc/assembly policies. C-alpha count and consecutive trace edges checked.
5. Two-stage constant-input ODE compared at all 501 times to SciPy solve_ivp
   DOP853 rtol=1e-11, atol=1e-13. Required component-wise error <=
   1e-7 + 1e-6*abs(reference). Cases: all four operators with the default inputs,
   transcription/translation zero, input endpoints, both decay extrema, equal
   and nearly equal decays (both directions, delta=1.1e-10 and 1e-8), durations
   1 and 300, and 80 deterministic random cases (seed 20261010) within UI bounds.
   Independent ODE reference spells out gate equations without importing gates.
6. Project/record round trips retain source hashes; edits flag divergence from
   imported sequence. PT/EN switching preserves data, drafts and output hashes.
   Legacy projects without source metadata still open.
7. Native Linux UI smoke flow in both languages includes reference loading,
   structure loading, provenance save/open/export and mocked asynchronous NCBI
   success/error handling; no interactive scientific claims from network mocks.
   Windows 0.2 user confirmation is recorded separately from automated v0.3 checks.

## Baseline finding and corrective work

A diagnostic comparison of the v0.2 analytical circuit on 2026-10-10 revealed
cancellation when decay_m=0.2 and decay_p=0.2+1.1e-10: maximum absolute error
5.804245031493238e-6, outside the above component-wise tolerance. v0.3 replaces
the subtractive exponential quotient with an expm1-based divided difference.
The baseline diagnosis is exploratory; acceptance is the fixed full suite above.
During the full suite, floating-point multiplication/division could place the
last requested time slightly beyond the interval duration. v0.3 computes time
as duration*(i/500), preserving the exact endpoint. No tolerances were relaxed.

## Reporting and publication gate

The validation script exits nonzero for any unmet criterion and records all
comparisons, library/Python versions, hashes, case parameters, errors and limitations.
`VALIDACAO.md` must distinguish observed results, proposed future studies,
computational model verification, and unperformed biological validation.
Only after local criteria and UI/core checks pass may this validated development
version be sent to GitHub. Target-OS CI results must remain explicitly pending
until observed. A code release is not a scientific-paper publication.
