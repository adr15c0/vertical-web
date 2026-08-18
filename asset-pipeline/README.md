# asset-pipeline

Generates **Divi-native** assets and pushes them to WordPress.

Outputs:
- Divi **Library layouts** (`et_pb_layout` JSON)
- Divi **module presets**
- Divi **Global Colors** / design defaults
- Page content (Divi **shortcodes** in `post_content` + `_et_pb_use_builder=on` meta)

Push channels:
- **WP REST API** (Application Passwords) for content/media
- **WP-CLI** for admin ops and to bypass the 2 MB upload limit on the legacy host

Material UI is used only as a **design reference** to avoid hand-building sections from scratch;
it is never installed on or pushed to the WordPress site. A creative refines the resulting Divi
Library assets in the **Divi Visual Builder**.
