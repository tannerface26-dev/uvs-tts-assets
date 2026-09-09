# UVS TTS Card Updater Handoff

## Project Location

`C:\Users\tanne\Downloads\TTS UVS\uvs_tts_card_updater`

This updater is intentionally separate from the main TTS table files, but it reads
and writes the card DB files in the parent workspace.

Git-backed backup/repo root:

`C:\Users\tanne\OneDrive\Documents\git\uvs-tts-assets`

The Downloads workspace did not report as a Git working tree when checked
directly, so check Git status from the repo root above.

## Run Command

Use the direct Python server command. Avoid service wrappers or launcher scripts
because Norton flagged those patterns as `IDP.Generic`.

```powershell
cd "C:\Users\tanne\Downloads\TTS UVS\uvs_tts_card_updater"
python -u .\cardDB_ui_server.py
```

Open:

`http://127.0.0.1:8787/cardDB_ui.xml`

Stop with `Ctrl+C` in the terminal.

## Important Files

- `cardDB_ui_server.py`: local HTTP API, scraper coordination, apply/publish logic.
- `cardDB_ui.html`: browser UI.
- `cardDB_generator.py`: moved generator script used by the UI/server.
- `cardDB_ui_decisions.json`: latest decision log written by Apply Choices.
- `history.json`: generated after apply/publish actions; stores update history.
- `guidelines.md`: lessons learned and project rules.

Parent workspace outputs:

- `..\cardDB_fresh.json`
- `..\cardDB_fresh.lua`
- `..\.tts\bundled\card_db.664c59.lua`

TTS save folder:

`C:\Users\tanne\OneDrive\Documents\My Games\Tabletop Simulator\Saves`

## Current Workflow

1. Create a new Tabletop Simulator save for the new table version.
2. Start the updater server.
3. In the UI, select the target TTS save from the left menu.
4. Enter the UVS Ultra extension number.
5. Use `legacy` for unreleased preview sets unless the set is officially
   standard legal.
6. Click `Scan Set`.
7. Review Preview and Conflicts.
8. For same-name/different-image conflicts, visually choose the desired card.
9. Click `Apply Choices` to update `cardDB_fresh.json` and `cardDB_fresh.lua`.
10. Click `Publish to Save` to update the selected TTS save's embedded `card_db`
    notecard script.

## Scraping Notes

- The scraper should use UVS Ultra's numeric `extension[]` filter.
- For the SF6 2026 Challenger set, the extension number used was `137`.
- The image URL folder code was `sf62x`, but the UI should favor the site filter
  number, not image-folder matching.
- Unreleased previews may show under `legacy`; this is expected.

## Conflict Resolution Notes

- All card previews must use the shared `.image-frame` sizing pattern.
- Conflict choices should stay compact and side by side.
- If a loaded old decision is wrong, use the History tab, load the old applied
  choices, change the selected cards, then Apply Choices again.

## Publishing Notes

- Publishing to `..\.tts\bundled\card_db.664c59.lua` alone does not update an
  already-created TTS save.
- Existing TTS saves embed the `LuaScript` for the `card_db` object.
- `Publish to Save` finds object GUID `664c59` or Nickname `card_db` and replaces
  only the generated `cardDbImages` and `cardDbMeta` sections.
- A backup is written before publishing to a save or Lua file.

## History Feature

The History tab now records:

- applied choice runs
- TTS Lua publishes
- selected-save publishes

Applied choice history includes the scan analysis and choices so it can be
loaded later without running a new scan. Publishing history records target path,
backup path, card totals, and timestamp.

History starts filling from actions performed after the history feature was
added.

## Verification Done

The latest code was checked with:

```powershell
python -m py_compile .\cardDB_ui_server.py .\cardDB_generator.py
```

Smoke-tested endpoints on port `8788`:

- `/api/history`
- `/api/defaults`

The temporary `8788` server was stopped afterward.

## Next Likely Work

- Test the History tab through a real apply/publish cycle.
- Confirm `Publish to Save` updates the newly created TTS save that the user
  selects.
- Consider adding a visible "last published save" indicator near the save
  selector.
- Consider adding a `Refresh Saves` button if TTS creates a new save while the UI
  is already open.
