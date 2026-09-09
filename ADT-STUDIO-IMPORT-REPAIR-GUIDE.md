# ADT Studio import error: reusable repair guide

## How to use this file next time

Attach this Markdown file, the ZIP that fails to import, and a screenshot or the exact error. Include the original PDF and project database if available. Then send this message:

> Please use the attached guide to diagnose and fix my ADT Studio import error. Inspect the actual files and my Studio version first. Make a short plan, carry out the applicable repair, and test the resulting ZIP with Studio's importer. Preserve my original files. Give me the repaired ZIP and explain any recovery limitations. If essential files are missing, tell me exactly what you need.

This guide supplies a repair method. It does not contain the textbook, PDF, database, or repair scripts. Attach those separately or provide accessible file paths. A Markdown file alone cannot restore missing project data.

## The error this guide addresses

> This isn't a valid ADT Studio project. The archive must contain a project database and its PDF. Re-export it from ADT Studio.

There are two different ZIP exports:

| Archive | Typical contents | Purpose |
| --- | --- | --- |
| Web textbook | HTML pages, assets, images, text and audio catalogs | Reading in a browser |
| Studio project | Project database, original PDF, project resources | Importing and editing in ADT Studio |

A working browser textbook can still lack the data needed for project import. Renaming a web ZIP does not convert it to a Studio project.

## Repair plan

1. Inspect the ZIP and confirm the exact failure.
2. Check the import requirements in the user's installed Studio version or matching source code.
3. Look for the matching original project database and PDF in relevant project folders.
4. Choose the applicable repair below.
5. Create a separate repaired ZIP, preserving the inputs.
6. Test database integrity, Studio import, page rendering, and available audio.
7. Deliver the ZIP, validation results, and recovery limitations.

## Choose the applicable repair

### A. The database and PDF exist but are inside an extra folder

Check that they belong to the same book and that the database is compatible with Studio. Package the project directory's contents directly at the ZIP root. Exclude macOS metadata such as `__MACOSX` and `.DS_Store`.

Use this example layout as a starting point, then confirm it against the applicable Studio version:

```text
book-project.zip
├── book.db
├── book.pdf
├── config.yaml
├── images/
├── audio/
└── adt/                 # preserved reader, when available
```

Use the same filesystem-safe basename for the database and PDF. Preserve other project resources needed by that Studio version. Confirm current requirements before assuming this layout is sufficient.

### B. The ZIP contains only a web textbook

First try to obtain a Project export from its creator or locate the original project folder. That preserves more information than reconstruction.

If the original database is unavailable but the web textbook and matching original PDF are available, a reconstructed project may be possible. Follow the reconstruction procedure below. Do not create an empty database merely to pass the file check.

### C. Essential source files are missing

Identify which files are missing. If only a PDF is available, creating a new Studio project requires processing it again; that does not restore existing edits. If the PDF is missing, request it before attempting the reconstruction described here.

### D. The database exists but fails validation

Inspect it on a copy. Check SQLite integrity and Studio's schema compatibility. A valid SQLite file is not necessarily a valid Studio database. Use supported migrations where available; changing a schema version number alone is not a migration.

## Reconstruction procedure for a developer or coding assistant

1. **Confirm the source match.** Compare PDF page count and representative pages with the reader. Do not assume reader navigation count equals PDF page count: covers, quizzes, and split sections can add entries.
2. **Inspect Studio's implementation.** Locate import validation, database schema and migrations, content types, preview routes, and packaging code. The reference repository is <https://github.com/unicef/adt-studio>. Use the version applicable to the user's installation.
3. **Create a separate working directory.** Copy the PDF and preserve the complete reader under `adt/`. Keep the original inputs unchanged.
4. **Build a real database.** Use the compatible schema. Populate source pages and extracted PDF text. Generate PDF page previews and register images with valid paths, dimensions, and IDs.
5. **Recover content.** Map the reading manifest and HTML into page sectioning and rendering records. Preserve stable text IDs, section order, inline text, styling, images, extra covers, and any activity behavior that can be recovered. Check image URLs against Studio's preview and export conventions.
6. **Recover catalogs.** Import text, glossary, table of contents, audio mappings, and audio files. Follow the version's speech catalog requirements. Record unknown voice/model/provider-text provenance honestly. Do not claim that recovered text is a verified transcription of an audio file.
7. **Keep processing status honest.** Mark only steps with recovered output complete. Do not invent AI decisions, prompts, generation logs, caches, or editing history. Unrecoverable stages must remain identified as incomplete or unavailable.
8. **Finalize SQLite compatibility.** Close connections and checkpoint any WAL transactions. If the target SQLite runtime cannot read a WAL-mode database, finalize a copy with `PRAGMA journal_mode=DELETE` after checkpointing, then retest it. Verify with the actual runtime rather than assuming Python's integrity check proves compatibility.
9. **Package the project.** Put the database and matching PDF at the ZIP root. Include required project resources and the preserved reader. Do not include temporary database sidecars after the database has been finalized.
10. **Test before delivery.** Apply the checklist below. Describe the result as a reconstructed project, not the recovered original database.

## Validation checklist

- ZIP opens and contains the required database and PDF at the expected level.
- SQLite integrity check returns `ok`.
- Studio's database layer can open the database.
- Recovered records pass that version's content schemas.
- Studio's import preview reports no validation error and the correct page count.
- A full import into a separate test folder completes successfully. Await asynchronous import calls before checking the result.
- The imported book does not report a database rebuild requirement.
- Representative pages render correctly through Studio's preview, including text, styles, and images.
- Navigation order and added covers/sections are checked.
- Audio mappings resolve and representative audio files load.
- Missing or partially recovered features are documented; successful import alone does not prove every feature is fully restored.

Keep validation output with the repaired ZIP. Avoid rerunning content generation until reconstructed semantics and any activities have been reviewed. Re-exporting from Studio may differ from the preserved reader.

## Deliverables for any book

Save repair outputs in a separate directory, such as `output/import-repair/`. Replace `<book-name>` below with a filesystem-safe name for the book being repaired; do not use the angle brackets literally.

- `<book-name>-recovered-project.zip` — repaired import archive.
- `<book-name>-recovered-project-validation.json` — actual validation results, including any failures or untested checks.
- `rebuild_project.py` — reconstruction script, if one was needed.
- `validate_project.mts` — importer and schema validation script, if one was used.
- `README.md` — import instructions, recovered content, and limitations.

These are naming examples, not files supplied by this guide. Use `recovered` for a reconstructed project; for a packaging-only repair, use `repaired` instead.

## Record the outcome of each repair

Create a fresh report for the current book. Record:

- Input filenames and the diagnosed cause of the import error.
- Studio version and database schema version actually tested.
- Whether the original database was repackaged, migrated, or reconstructed.
- Actual PDF page count, reader section count, text entries, images, and audio mappings recovered.
- Missing source files, missing assets, and content that could not be recovered.
- Import preview and full import results, including validation errors or rebuild requirements.
- Schema checks and representative pages, navigation, and audio tested.
- Any checks not performed and any remaining limitations.

Do not copy counts, success claims, or schema versions from a previous repair. Mark the repair successful only after the applicable checks pass.

Any scripts created during a repair should take input paths, output paths, and book identifiers as parameters where practical. Inspect their assumptions and dependencies before reusing them with another book or Studio version. Never assume a previous book's page count, language, section structure, or local filesystem paths apply.

## Import the repaired file

1. Open ADT Studio and choose **Import a Project**.
2. Select the repaired `-project.zip` file itself. Do not extract and re-zip it.
3. Check the preview title and page count, then import.
4. Open representative pages and try read-aloud.
5. If an error remains, provide the exact error, Studio version, and the ZIP used so the next repair starts from evidence.
