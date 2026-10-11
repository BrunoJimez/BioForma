# BioForma Studio

[Português (Brasil)](README.pt-BR.md) · English

**Version 0.3.0 — bilingual desktop workbench for Windows and Linux.**

Edit DNA, view an idealized helix, inspect existing PDB coordinates and program an educational
gene-expression model in JSON. The application runs locally and requires no accounts, paid APIs,
telemetry. Bundled references and analysis work offline; optional NCBI retrieval requires internet. Its scientific scope is educational and computational:
it does not predict a complete organism or phenotype from a genome.

## Install and run

Requires Python 3.10+ with Tkinter; Python 3.12 is recommended.

**Windows 10/11:** extract the entire package, run `INSTALAR_WINDOWS.cmd`, then use the desktop
shortcut. The per-user installer copies version 0.3 to `%LOCALAPPDATA%\BioFormaStudio\app-0.3.0`.
It coexists with previous installations and updates the BioForma shortcut. Python must remain installed.
For a portable source launch, run `ABRIR_SEM_INSTALAR.cmd` or `py -3 main.py`.

**Linux desktop:** install Python/Tkinter using the distribution’s package manager. On
Ubuntu, Linux Mint and Debian, the graphical dependency is `python3-tk`.
Run `bash INSTALAR_LINUX.sh`. The installer creates a user-owned application folder, a
launcher under `~/.local/bin`, and a `.desktop` entry in the applications menu.
For a source launch, run `bash ABRIR_LINUX.sh` or `python3 main.py`.
Linux requires an X11/Wayland desktop with Tk support; headless operation needs a virtual display.

You can check Tkinter with `python -m tkinter` (Windows) or `python3 -m tkinter` (Linux).
No elevated privileges are required by either application installer. Distro package installation
may require the ordinary system administrator permission.

This package contains source and installation scripts, not precompiled Windows/Linux binaries.
Native executables can be built on each target OS using the build scripts or the prepared Actions workflow.

## Language selection

Choose **Português (Brasil)** or **English** in the top bar. Labels, help, application messages,
graphs and object details update immediately. Existing editor drafts, undo history, cursor,
project data and numerical results remain unchanged. The preference persists for the next launch.

Command-line override: `python main.py --language en` or `--language pt`.
Sequence data, JSON keys, user-defined project names and CSV identifiers are not translated.
CSV columns are `time_au`, `mrna_au`, and `protein_au`, regardless of UI language.
Native OS dialogs and low-level OS error details may follow the operating system language.

Preferences: `%LOCALAPPDATA%\BioFormaStudio\settings.json` on Windows;
`$XDG_CONFIG_HOME/bioforma-studio/settings.json` (default `~/.config/...`) on Linux.
Logs use the same Windows folder or `$XDG_STATE_HOME/bioforma-studio/logs` (default `~/.local/state/...`).

## Features and scope

| Area | Implemented | Interpretation |
|---|---|---|
| DNA | IUPAC validation, GC%, reverse complement, positional comparison | No gene discovery or evolutionary alignment |
| Translation | Standard code, frames +1/+2/+3, stop/ambiguity markers | No inference of expression, splicing, function or folding |
| Import | Single/multi-record FASTA; GenBank ORIGIN sequence | FEATURES are not interpreted; reference-file provenance is retained separately |
| DNA viewport | Rotation, zoom, pan, selection, SVG | Idealized bases; no atomic deformation prediction |
| PDB viewport | First-model atom cloud/Cα trace; A/blank conformers | Existing coordinates; no folding or assembly reconstruction |
| Circuits | Constant-input two-stage production/degradation; AND/OR/NOT_A/XOR | Uncalibrated deterministic educational model |
| Projects | JSON save/reopen; previous 0.1 format supported | One selected DNA record; camera state is not stored |
| Reproducibility | Self-contained input/results JSON with SHA-256 | Does not certify tests or biological validity |

Limits: 100,000 bases per DNA sequence; 12 MB per input file/project; 160 bases per helix window;
50,000 parsed PDB atoms and 1,800 displayed points. Truncation is reported. Editor syntax coloring
is limited to the first 6,000 text positions. RNA with U and gapped alignments are unsupported.
The viewport uses CPU/Tkinter and does not require CUDA. There is no autosave.

## Educational examples

Open `exemplos/demo.bioforma.json` for an initial project. The included DNA fragment is invented,
with no validated function. `geometria_artificial.pdb` contains explicitly artificial coordinates
for viewer testing, not an experimental or predicted protein.
For existing scientific structures, obtain a legacy PDB from a source such as the
[RCSB PDB](https://www.rcsb.org/) and verify its provenance there.

## Reproducibility and publication

Use **Export reproducibility record** in the guide tab. The JSON includes the full project,
parameters, calculated sequence/circuit/PDB summaries, application and Python versions,
platform, UI language, algorithm identifiers, UTC timestamp and input/result hashes.
For the same project, UI language does not change the numerical results or their hashes.
Exported records contain project data; review them before sharing.

See [VALIDACAO.md](VALIDACAO.md) for evidence actually obtained and
[the proposed validation protocol](docs/VALIDATION_PLAN.en.md) for a future study.
The plan is not an experiment already performed. Unit and interface checks are computational
verification; biological calibration and validation have not been performed.
The user confirmed that 0.2 worked on Windows. Local 0.3 tests and GUI flows passed in Linux.
See VALIDACAO.md for independently measured results and remote/target-OS status.

## Public references in version 0.3

Open **04 Public references** and select an offline example:

| Reference | Data | Scientific interpretation |
|---|---|---|
| NR_027552.1 | Bacillus subtilis partial 16S rRNA locus, 1,517 bases | A bacterial reference locus, not a whole bacterial genome |
| NC_001422.1 | PhiX174 bacteriophage genome, 5,386 bases | Single-stranded DNA; the displayed duplex is idealized |
| 1CRN | Crambin coordinates from RCSB PDB, 327 atoms | Existing X-ray coordinates, independent of the open DNA |

The bundled FASTA/GenBank/PDB bytes are frozen under `referencias/`. A manifest records
accession/version, provider URLs, retrieval time and SHA-256. Opening a bundled example verifies
its hash. Project JSON and reproducibility records preserve source metadata and report whether
the current DNA still matches the imported sequence. Positional baseline changes do not erase
the source history. Hashes establish byte identity, not biological correctness or authenticity
of a user-edited project.

Optional **Retrieve FASTA from NCBI** accepts a versioned nucleotide accession and runs in the
background. Only the entered accession is sent to NCBI; no project data are uploaded. No account
or key is required. Timeout: 20 seconds; response limit: 12 MB; sequence limit: 100,000 bases.
Errors preserve the current project. Large bacterial genomes require segments or a future
genome-scale interface. This version does not analyze annotated CDS/genes or other genetic codes.
Translation of rRNA or a whole genome in an arbitrary frame must not be interpreted as real
protein expression.

Independent validation uses Biopython 1.86, SciPy 1.17.0 and NumPy 2.3.5, installed only for tests:

```sh
python -m pip install -r requirements-validation.txt
python scripts/validate_independent.py --output local-results/independent.json
```

See `validacao/PROTOCOL.md` and the frozen `validacao/results_v0.3.0.json`. All 64 canonical
codons matched Biopython. Exhaustive IUPAC testing disclosed 127 intentional differences
among 3,375 codons: BioForma conservatively uses X for every ambiguous codon, while Biopython
resolves some possibilities. These are disclosed policy differences, not full agreement.
The model passed 113 ODE cases (56,613 sampled times) with tolerance
`1e-7 + 1e-6*abs(reference)`. This is computational evidence on a small corpus, not biological
validation or a claim of general accuracy.

## Research publication

The public development repository is [BrunoJimez/BioForma](https://github.com/BrunoJimez/BioForma).
Code/data availability, limitations and future study stages are described in
[RESEARCH_ROADMAP.md](docs/RESEARCH_ROADMAP.md). A scientific paper and archival DOI remain
future deliverables after a defined study. No paper submission, acceptance or DOI is claimed.

## Tests and builds

Core/catalog tests: `python -m unittest discover -s tests -v`.
Native UI flow: `python verificar_interface.py` with a graphical display.
Windows launchers: `TESTAR.cmd`, `TESTAR_INTERFACE.cmd`.
Linux test launcher: `bash TESTAR_LINUX.sh`; CI uses Xvfb for the GUI flow.

To build native binaries, use `GERAR_EXE.cmd` on Windows or `bash GERAR_BINARIO_LINUX.sh`.
This stage requires internet to obtain the pinned PyInstaller dependency. Both scripts call
`build_executable.py`, which produces a complete portable runtime folder and an OS-specific archive.
Distribute the whole runtime folder, not only its main executable. Linux binaries depend on their
build distribution’s ABI; broad Linux distro compatibility is not claimed.

The prepared GitHub workflows test source on Windows/Linux with Python 3.10 and 3.12, and provide
a manual native build on Windows/Linux. They have not run remotely until the repository is published.
Build artifacts are uploaded to Actions; the workflow does not automatically create a public release.

## GitHub preparation

This package includes `LICENSE`, `CITATION.cff`, change log, contribution guide, issue template,
ignore rules, bilingual documentation and CI/build workflows. See [GITHUB.md](GITHUB.md).
No repository URL, DOI, ORCID, journal acceptance or remote CI pass is invented.

## References

- [NCBI genetic codes](https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi)
- [wwPDB coordinate format](https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html)
- [Python/Tkinter documentation](https://docs.python.org/3/library/tkinter.html)
- [GitHub Python CI documentation](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [PyInstaller platform/build documentation](https://pyinstaller.org/en/stable/)

## License and citation

MIT; see [LICENSE](LICENSE). Citation metadata is in [CITATION.cff](CITATION.cff).
The project currently credits Bruno Jimez. Add any actual collaborators to the metadata before
a scholarly release. No DOI has been assigned.
