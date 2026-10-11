# Contributing / Contribuições

Issues and contributions can be written in English or Portuguese.
Run `python -m unittest discover -s tests -v` and `python verificar_interface.py` with a display.
For an interface change, verify both languages and ensure unsaved drafts survive language switching.
Do not translate DNA, JSON schema fields, user-defined names or machine-readable result identifiers.

Add catalog entries in `bioforma/translations.py`; preserve all format placeholders.
Use standard-library runtime dependencies where practical. Update both README files and the change log
when behavior changes. Declare the interpretation of any new molecular model and supply independent
verification for numerical changes; distinguish artificial examples from measured data.

Report the environment, input fixture/provenance, expected behavior, actual result and reproduction steps.
Avoid committing private project data or credentials. Scientific claims must match validation evidence.
