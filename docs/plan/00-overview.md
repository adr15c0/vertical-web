# 00 — Overview

**Project:** Church Website Consolidation & Modernization
**Approach:** Divi-native (stay on WordPress + Divi 4 / Classic Editor). **Status:** planning complete.

Merge two separately maintained WordPress installs — English `goverticalchurch.com` and Spanish
`iglesiavertical.com` (both on one orphaned, Ploi-managed DigitalOcean droplet) — into a **single
Divi site**, rebuilt on **Azure**, with a shared skeleton, a programmatic Divi asset pipeline, an
internal non-developer console, and AI-assisted (human-reviewed) translation.

## Section index (maps to the planning prompt)

| # | Section | Notes |
|---|---------|-------|
| [01](01-content-model.md) | Content model | CPTs/taxonomies via versioned mu-plugin |
| [02](02-multilingual.md) | Multilingual layer | Polylang Pro; Spanish at `/es/` |
| [03](03-theme-architecture.md) | Theme architecture | **Rewritten Divi-native** (no block theme/`theme.json`) |
| [04](04-vertical-db-integration.md) | Vertical DB integration | Research spike; Postgres/Azure ← Planning Center |
| [05](05-local-environment.md) | Local environment & data pull | DDEV; extract from orphaned host via browser |
| [06](06-migration-merge.md) | Migration & merge | Divi-aware merge; English canonical |
| [07](07-deployment-pipeline.md) | Deployment pipeline | Monorepo, CI, promotion to Azure |
| [08](08-sequencing.md) | Sequencing | Phases 0–4 + governance Step 0 |
| [09](09-open-questions-costs.md) | Open questions & costs | Verify pricing independently |
| — | [Backlog](backlog.md) | Milestones → epics → issues for GitHub |

## Key decisions

- **Stay on Divi 4 + Classic Editor.** No Gutenberg/block-theme re-platform. Divi 5 is a separate,
  later evaluation — do **not** enable it on production.
- **Asset pipeline outputs Divi-native artifacts** (Theme Builder templates, Library layout JSON,
  module presets, Global Colors, shortcode content). **Material UI is a design reference only** and is
  never installed on the site.
- **Non-developers edit content/data in the console; layout/design stays in the Divi Visual Builder.**
- **Multilingual:** Polylang (Pro); Spanish at `/es/`; **English is canonical**.
- **AI translation:** Azure OpenAI **drafts**, a **bilingual human reviews**; intentional EN/ES
  divergence is preserved per-field (never blind machine translation).
- **Tooling DB:** separate **Postgres on Azure** (asset registry, translation drafts/review, inventory
  + audit log) — distinct from WordPress MySQL and from Vertical DB.
- **Automation auth:** WordPress **REST (Application Passwords)** + **WP-CLI**.

## Infrastructure reality (important)

The legacy droplet is **orphaned** — no server/DigitalOcean/Ploi/ManageWP credentials could be
recovered. It is therefore a **read-only data source**: everything is extractable through the browser
(wp-admin + UpdraftPlus full backup + WXR export + REST). The consolidated site is **rebuilt on
Azure** (subscription owned by the maintainer), which also fixes the legacy 2 MB upload limit and the
missing object cache. **DNS for both domains is controlled via GoDaddy**, so the Azure cutover is
unblocked. Divi's license is **active and current**.

## Confirmed environment

- **English:** WP 7.0.4, Divi 4.27.7 (licensed, current, Theme Builder in use — 3 templates),
  ~44 pages / 5 posts, 12 active plugins incl. Supreme Modules Lite, UpdraftPlus, Filester.
- **Spanish:** WP 7.0.4, Divi **4.27.4** (behind), ~42 pages / 0 posts. **Parity gaps:** no
  UpdraftPlus/Filester/Supreme Modules; **adds ASE** (Admin & Site Enhancements); Divi Carousel behind.
- Both: PHP 8.2 / nginx 1.24 / MySQL 8.0, Classic Editor + Divi Builder, 2 MB upload limit, no object cache.
