# UVS TTS Card Updater Guidelines

## UI Layout

- Any card image shown anywhere in the updater must use the shared stable
  `.image-frame` sizing pattern from the Preview tab.
- Conflict resolution should show same-name/different-image choices side by side
  so the final table DB image can be chosen visually.
- Keep conflict cards compact and comparable; card art should scale inside its
  frame and must not stretch the page vertically.
- Keep the menu/settings frame on the left side and preserve the dark theme.
- Make the updater itself the first screen; do not replace the tool with a
  landing page or explanatory splash screen.

## Scraping

- Use UVS Ultra's numeric `extension[]` filter when possible.
- The image URL folder code such as `sf62x` is useful for verification, but the
  fastest scan path is the page's own numeric extension value, such as `137`.
- Unreleased preview sets may appear under `legacy` before they become
  `standard` legal.
- After scraping the filtered set, compare against the target local card DB:
  skip same-name/same-image rows, list new rows for preview, and route
  same-name/different-image rows to conflict resolution.
- Do not require a new scan when existing scan data is already available in
  history and the user only needs to revise prior decisions.

## Local Running

- Avoid Windows Service wrappers and launcher scripts for this project because
  antivirus tools can flag service installation or wrapper-launch behavior as
  suspicious.
- Prefer a visible manual command:

```powershell
cd "C:\Users\tanne\Downloads\TTS UVS\uvs_tts_card_updater"
python -u .\cardDB_ui_server.py
```

- Stop the updater with `Ctrl+C` in the terminal running it.
- If the browser page fails to load, check for a stale listener on port `8787`
  before changing application code.

## Publishing

- After applying scrape choices to the JSON/Lua generator outputs, the next step
  is publishing `cardDB_fresh.json` into the selected TTS save's embedded
  notecard script.
- The normal table update process is to create a new TTS save for the new
  version before making changes, then publish into that new save.
- Provide a TTS save selector; do not assume the active target is always
  `TS_Save_20.json`.
- Publishing should only replace generated `cardDbImages` and `cardDbMeta`
  sections; preserve card backs, errata, helper functions, and runtime code.
- Always write a backup before publishing to either a `.lua` export or a TTS
  save JSON.
- When testing publish logic, use a copied save or a deliberately selected test
  target so the user's active TTS save is not changed accidentally.

## History

- Record applied choices and publish actions in a local structured history file
  so past updates can be reviewed from the UI.
- History entries for applied choices should include the scan analysis and
  conflict choices so old decisions can be loaded, changed, and applied again
  without running a new scan.
- Publish history should show the target file/save, backup path, card totals,
  and timestamp.

## Documentation

- Keep repeatable process lessons in this file.
- Put one-off handoffs, status notes, and longer Markdown summaries in the
  `docs` folder.
- When a lesson from a handoff should affect future implementation choices,
  copy the general rule into `guidelines.md` instead of leaving it only in the
  handoff.

## Repository Backup

- The active Downloads workspace may not itself be a Git working tree.
- The Git-backed backup/repo root is
  `C:\Users\tanne\OneDrive\Documents\git\uvs-tts-assets`.
- Check Git status from the repo root, not from
  `C:\Users\tanne\Downloads\TTS UVS`, before assuming there is no repo backup.
