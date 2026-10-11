# Proposed computational validation study

Status: **prospective protocol**, prepared on 2026-10-10. It is not a record of a completed study.
Scope: BioForma Studio as an educational desktop sequence/coordinate/model workbench.

## Research questions

1. Do supported sequence operations agree with independently maintained reference implementations?
2. Does the parser retain the intended first-model PDB coordinates and the specified conformer policy?
3. Does the analytical circuit solver agree with independent numerical integration under declared inputs?
4. Do project persistence and language switching preserve inputs and numerical results?
5. Do intended educational users correctly distinguish schematics, coordinates and model predictions?

## Freeze the artifact before measuring

Choose and tag an actual release commit; archive its source, dependencies, test fixtures and hashes.
Record Python, Tk, OS, architecture, display scale and machine specifications.
Use identical input files in both languages and OSes. Fix the input-selection and exclusion rules
before inspecting results. Document every protocol deviation with date and reason.
No result should be reclassified as a priori after its outcome is known.

## Dataset and eligibility

- Sequence fixtures: curated canonical DNA, all 64 codons, lengths around frame boundaries,
  declared IUPAC ambiguities, multi-record FASTA, GenBank ORIGIN and explicitly unsupported cases.
- Structure fixtures: public legacy PDB files with accessible provenance and file-use terms;
  include multiple models, chains, altlocs, TER boundaries, missing coordinates and no-Cα entries.
- Educational examples remain identified as artificial and never stand in for measured structures.
- Build a held-out group of fixtures not used while implementing the importers.
- Determine corpus size from coverage goals and a documented sampling plan before measurement.
  Do not invent a participant count or claim statistical power without a justified calculation.

## Independent comparisons

Sequence import/translation: choose and pin Biopython, with an explicitly matched genetic-code,
reading-frame and ambiguous-codon policy. BioForma returns X for every ambiguous codon; reference
tools may resolve some ambiguous codons, so evaluate that difference under the declared policy.
GenBank eligibility is limited to ORIGIN sequence extraction; annotations are not assessed as preserved.

Coordinate import: compare with a pinned Biopython or Gemmi parser after applying the same first-model,
blank/A conformer and residue identity policies. Inspect cases of disagreement, rather than assuming
different parser defaults are software errors. Compare coordinates before viewport truncation.

Circuit: compare the closed-form solution against an independent implementation of solve_ivp or RK4.
Use declared tolerances, covering equal/near-equal degradation, zero production, Boolean boundaries,
intermediate inputs, and the allowed rate/duration boundaries. Record reference solver tolerances.

## Suggested primary endpoints, to freeze before execution

| Endpoint | Proposed acceptance rule |
|---|---|
| Supported canonical sequence import/translation | Exact sequence/result equality |
| Input validation | Supported cases accepted; unsupported or malformed cases explicitly rejected |
| PDB coordinate extraction | Same selected atom identities; coordinate error ≤ 0.001 Å |
| Analytical circuit vs independent solver | Absolute error ≤ 1e-7 + 1e-6 × absolute reference value, with adequately converged reference |
| Save/reopen | Exact canonical project data equality |
| PT/EN numerical invariance | Exact result and input/result-hash equality for the same project |

These are proposed criteria, not demonstrated outcomes. Amend and freeze them before collecting
the validation dataset. The PDB rule reflects the precision of the legacy input coordinates; it
does not assert biological accuracy. Include absolute and relative errors, not only pass/fail counts.

## Secondary endpoints

Report startup/import/analysis latency and peak memory on documented machines, using a declared
warm-up strategy and repeated measurements. Treat runs on a single machine as repeated observations,
not independent biological samples. Describe the corpus strata and report individual failures.
For small deterministic correctness datasets, exact counts often carry more meaning than p-values.

For educational usability, define learning/interpretation tasks and a scored rubric before testing.
Record whether users misread an illustrative helix or circuit as a validated organism prediction.
If recruiting participants, determine the applicable institutional ethics/consent requirements first.
Do not claim educational efficacy based solely on developer demonstrations.

## Evidence and limitations

Distinguish developer unit tests, independent computational validation, platform compatibility,
usability evaluation and biological calibration. Only claim stages actually completed.
Current software contains no genotype-to-phenotype organism model, protein-folding predictor,
experimentally calibrated circuit or wet-lab protocol. A journal submission should state this scope
in its title, abstract and methods. Do not describe the program as a validated digital organism.

## Release and manuscript materials

Include repository/tag/commit, archived source, actual DOI if later assigned, fixtures and licenses,
complete protocol, independent comparator versions, results CSV/JSON, failure inventory and environment
records. Exported BioForma records support reproduction but do not certify a successful experiment.
Report AI-assisted development transparently according to the eventual journal’s current policy.
Publication venue, author list, claims and analysis plan should be chosen based on the evidence obtained.

## Primary technical references

- https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
- https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html
- https://biopython.org/wiki/SeqIO
- https://docs.python.org/3/library/tkinter.html
- https://docs.github.com/en/actions/tutorials/build-and-test-code/python
