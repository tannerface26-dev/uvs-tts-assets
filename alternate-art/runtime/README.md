# Alternate-Art Runtime Catalog

`manifest.json` is the reviewed input for consumers such as the UVS Ultra
Chrome extension and the TTS importer. Its qualifiers are stable identifiers:

```text
repo/{uvsUltraCardId}-{officialGalleryId}
```

The image remains in `../official-gallery/images/`; `sourcePath` is relative to
this directory. Consumers should construct URLs only from their own trusted,
HTTPS repository base URL and these allowlisted paths.

`previewPath` and `microPath` point to generated JPEG derivatives matching UVS
Ultra's native `358x500` preview and `20x20` deck-row thumbnail dimensions.

`unresolved.json` is a review queue, not runtime input. Records enter the
runtime catalog automatically only when the official gallery name has one
exact normalized match in CardDB. Name normalization changes case, whitespace,
and typographic quotation marks only. It does not use fuzzy matching.

Each runtime card includes its canonical UVS Ultra `original` image identity.
`exclusions.json` removes reviewed false positives, such as gallery records
whose images are not distinct alternate art.

Transforming cards with reviewed art on both faces store the paired back face
under `transformBack`. The transformed face is not emitted as a separate
runtime card. Consumers must keep both URLs associated with the front-face
qualifier for preview and gameplay.

Regenerate the files with:

```powershell
python build-runtime-manifest.py --card-db C:\path\to\card_db.664c59.lua
./build-image-variants.ps1
```

Review both generated files before committing. Manually confirmed mappings can
be added in a future override file rather than weakening the matching rules.
