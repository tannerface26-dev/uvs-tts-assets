# UVS TTS Card Updater

The updater runs as a visible local browser tool. It intentionally avoids Windows
Service and launcher-script wrappers because antivirus software can flag those
patterns as suspicious.

Start the updater:

```powershell
cd "C:\Users\tanne\Downloads\TTS UVS\uvs_tts_card_updater"
python -u .\cardDB_ui_server.py
```

Then open:

```text
http://127.0.0.1:8787/cardDB_ui.xml
```

Stop the updater by pressing `Ctrl+C` in that terminal.

After applying card choices, use `Publish to TTS` to rebuild the generated
`cardDbImages` and `cardDbMeta` sections in `.tts/bundled/card_db.664c59.lua`
from `cardDB_fresh.json`.

For normal table-version updates, create the new TTS save first, then use the
`TTS Save` selector and `Publish to Save` to update that save's embedded
`card_db` notecard script.
