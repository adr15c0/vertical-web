# 05 — Local environment & data pull

## Local stack: DDEV

**Chosen: DDEV** (Docker-based) over `wp-env` and Local. Rationale: closest to the nginx/PHP/MySQL
production shape, team-friendly, scriptable, and it comfortably runs Divi + WP-CLI. It also lets us run
the **Postgres tooling DB** alongside WordPress locally.

## Pulling production down (from an orphaned host — browser only)

We have **no SSH** to the legacy droplet, but wp-admin works, so data comes out through the browser:

- **English:** UpdraftPlus is installed → take a **full backup** (DB + uploads) and download it; also do
  a **WXR export** (Tools → Export).
- **Spanish:** UpdraftPlus is **not** installed → **install UpdraftPlus on the ES site** (admin) for a
  full backup, plus a WXR export.
- **Media:** included in the UpdraftPlus uploads archive (works around the 2 MB PHP limit, which only
  affects *uploading into* WordPress, not exporting out).

## Seeding local

1. Import the DB dump into the DDEV MySQL.
2. Restore `wp-content/uploads`.
3. Install **Divi** (from the licensed Elegant Themes package) + the **exact third-party add-ons** at
   pinned versions (Supreme Modules Lite, Divi Carousel Free; ASE for ES).
4. `wp search-replace 'https://goverticalchurch.com' 'https://vertical-web.ddev.site'`
   **`--all-tables --precise`** to handle serialized Divi shortcode data safely (dry-run first).
5. Verify a real Divi page opens and edits in the **Visual Builder**.

## Refreshing local later

- Re-run the export → import → `search-replace` sequence via a scripted make target so refreshes don't
  require redoing setup. Divi + add-ons persist in the DDEV config.

> Once the Azure host exists (Phase 4), the same export/import flow migrates data onto Azure; DDEV
> remains the developer inner-loop.
