# Session Updater

Use this checklist when starting a development session for the UVS TTS card DB
importer/updater.

1. Read `guidelines.md` and `HANDOFF.md` before changing code or running a
   test cycle.
2. Confirm the intended workflow for the session: scan, apply choices, publish
   to a selected TTS save, or improve the updater UI/server.
3. Start the updater with the direct Python command:

```powershell
cd "C:\Users\tanne\Downloads\TTS UVS\uvs_tts_card_updater"
python -u .\cardDB_ui_server.py
```

4. Open `http://127.0.0.1:8787/cardDB_ui.xml`.
5. If the page returns `ERR_EMPTY_RESPONSE`, check for duplicate
   `cardDB_ui_server.py` processes or a stale listener on port `8787` before
   changing application code.
6. For browser inspection, use Chrome remote debugging on port `9222`.
7. Keep the normal publish path focused on `Publish to Save`; the selected TTS
   save's embedded `card_db` script is the source Tabletop Simulator will load.
8. After changes, run:

```powershell
python -m py_compile .\cardDB_ui_server.py .\cardDB_generator.py
```

9. Update `guidelines.md` when the session teaches a reusable lesson, and update
   `HANDOFF.md` when the next session needs current state or status.
