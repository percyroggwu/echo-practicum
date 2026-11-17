# discovery_v1 generator

Builds the synthetic data pack `files_discovery_v1/` and its database `data/echo_discovery_v1.db`
(plan v10, section 5). Standard library only; no model or API calls; seed 20261115.

The pack (308 MB) and the database (437 MB) are not in git: GitHub limits files to 100 MB. Rebuild
them instead. The result is byte-identical (checked 2026-11-17: database SHA-256
`b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4`, same 27 CSVs and answer key).

## Inputs (all in git)

- `files_update/` and `data_extensions/`: the legacy tables and goals/self-review extensions.
- `files_discovery_v1/QA_manifest.csv`, `QA_data_dictionary.csv`, `README.md`: the pack's schema.
- `files_discovery_v1_private/QA_discovery_v1_story_rows.csv` and `QA_discovery_v1_story_worksheet.csv`:
  the frozen hand-built stories (P1-P6, D1-D8).
- `files_discovery_v1_private/QA_discovery_v1_answer_key.csv`: its header is read, then the file is
  rewritten with the answer key.

The answer key is for tests and evaluation only. It must never be loaded into a runtime database or
a model prompt.

## Rebuild

From `Agent_Echo`:

```
python -m data_discovery.generate_discovery_v1
python import_data.py --profile discovery_v1
```

The generator overwrites the pack CSVs and the answer key. `python -m data_discovery.build_discovery_v1`
runs both steps and then the QA checks, writing `files_discovery_v1/QA_build_report.md` and a private
report.
