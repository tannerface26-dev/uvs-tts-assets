# UVS Ultra Custom UI Backup

This directory is a source backup of the unpacked Chrome extension from:

```text
C:\Users\tanne\OneDrive\Documents\chrome_custom_extensions\uvs_ultra_custom_ui
```

Snapshot details:

```text
Extension version: 0.3.5
Assets revision: 5a000475fcd59bd31e816e85135642e817d31998
Manifest version: 3
```

The extension has no requested Chrome permissions or host permissions. Its
content scripts are restricted to `https://uvsultra.online/*`. Repository image
URLs are generated into `remote-card-art.js` and pinned to the assets revision
above.

To rebuild the generated card-art catalog after an approved assets update, run
the checked-in Python script with the runtime manifest and full commit hash.
Update the matching pinned path in `card-art.js`, validate all JavaScript, and
reload the unpacked extension before replacing this backup.
