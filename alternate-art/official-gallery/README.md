# Official Gallery Alternate-Art Archive

This directory contains the 459 cards returned by the UVS Games official
gallery's alternate-art classifications during the September 2026 FEAT-021
research pass.

- `images/` stores one image per official gallery card ID.
- `manifest.json` maps each local file to its official card ID, displayed name,
  rarity classification, set/number metadata when available, and source URL.

These files are research inputs. Inclusion here does not mean that a matching
UVS Ultra image URL or canonical Ultra card identity has been confirmed. Use the
confirmed TTS importer registry for runtime alternate-art mappings.

The archive can be refreshed with
`TTS UVS/session/download-official-alt-art.ps1`. The downloader is resumable,
validates image responses, spaces requests, and stops on rate-limit or server
errors.
