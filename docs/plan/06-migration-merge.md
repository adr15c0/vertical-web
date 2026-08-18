# 06 — Migration & merge

**Canonical install: English** (`goverticalchurch.com`) — it has the posts/blog history and analytics
baseline; Spanish is pages-only (0 posts), simpler to import. We merge Spanish **into** English.

## Divi-aware merge (not just WXR posts)

Divi stores layouts as **shortcodes in `post_content`** and keeps global assets in options and the
`et_pb_layout` CPT. A correct merge reconciles **more than posts**:

1. **Prep**
   - Install UpdraftPlus on ES; take full backups of **both** sites (immediately before merge).
   - **Standardize versions** across environments first: Divi `4.27.4 → 4.27.7`, Divi Carousel
     `3.0.6 → 3.2.1`, so layouts render identically.
   - The merged install carries the **union of add-ons**: Divi Carousel Free + Supreme Modules Lite;
     **inventory ASE** (ES-only) settings and decide keep/drop.
2. **Import ES content** via **WXR**; reconcile media attachments, map users/authors, rebuild ES menus.
3. **Reconcile Divi globals:** Global Colors, module presets, **Theme Builder templates**, and the
   `et_pb_layout` **Library** across both sites; verify shortcode content renders post-import.
4. **Establish translation pairs** in Polylang (EN ↔ ES); set language, `/es/` structure, `hreflang`.
5. **Redirect map:** `iglesiavertical.com/*` → canonical `/es/*` (301). Redirects go live **at cutover**.

## Validation (pass criteria)

- Page/post counts match expectations; no broken media or internal links.
- All Polylang pairs linked; menus and Theme Builder assignments correct per language.
- `hreflang` validates; sample Divi pages render pixel-correct in both languages.

## Backups & rollback

- Exact pre-merge backup captured via UpdraftPlus (both sites) and stored off the orphaned host.
- Merge happens on **staging first**; production cutover only after staging passes.
- Rollback: keep the legacy droplet serving until DNS to Azure is verified; revert DNS if needed.
