# Backlog — milestones, epics & issues

Milestones map to phases. Each issue carries a `phase:*`, `area:*`, and `type:*` label, and its
**acceptance criteria = Definition of Done**. This file is the source of truth for the GitHub issues
created via `scripts/bootstrap-github.sh`.

Dependencies: **Phase 2** depends on Phase 1; **Phase 3** depends on Phases 1 + 2; **Phase 4** depends
on Phase 3. Production is only touched in Phase 4.

---

## Milestone: Phase 0.5 — Repo Governance
- **#gov-1** chore(governance): finalize branch protection on `main` — required review + status checks, linear history, no direct pushes.
- **#gov-2** chore(governance): create GitHub Project board and wire milestones/labels.
- **#gov-3** ci(governance): expand CI (PHPCS, console lint/test, Divi Library JSON schema) as code lands.

## Milestone: Phase 0 — POC & Foundations
- **#p0-1** feat(infra): stand up DDEV WordPress locally, seeded from the English export.
- **#p0-2** chore(divi): install Divi + pinned third-party add-ons locally; **catalog module dependencies**.
- **#p0-3** feat(infra): stand up Postgres tooling DB (schema v0: `divi_assets`, `asset_versions`, `translation_drafts`, `inventory_snapshots`, `job_log`).
- **#p0-4** feat(pipeline): inventory + backup job (pages/posts/media/menus/plugins + Divi Library, Theme Builder templates, Global Colors).
- **#p0-5** feat(pipeline): **Divi asset pipeline POC** — generate a Library layout JSON + module preset + Global Colors (MUI as reference), push via WP-CLI, confirm editable in the Divi Visual Builder.
- **#p0-6** feat(pipeline): REST ↔ WP-CLI round-trip test with Divi builder meta intact; log to `job_log`.
- **#p0-7** spike(infra): verify full WP-CLI capability checklist.

## Milestone: Phase 1 — Scaffolding, Content Model & Divi Design System
- **#p1-1** feat(mu-plugins): register CPTs + taxonomies (events, sermons, ministries, staff, campuses, locations); mark translatable-vs-shared fields.
- **#p1-2** feat(divi): Divi Theme Builder skeleton (global header/footer + CPT archive/single templates).
- **#p1-3** feat(divi): centralize design tokens (Global Colors + module presets).
- **#p1-4** feat(theme): initialize the Divi child theme (`child-theme/`).
- **#p1-5** chore(infra): Composer-managed third-party plugins (wpackagist) where possible.

## Milestone: Phase 2 — Internal Admin Console
- **#p2-1** feat(console): scaffold React console on the WP REST API (Application Passwords auth).
- **#p2-2** feat(console): content/data editing + media swap for non-dev staff, with preview-before-publish + audit log.
- **#p2-3** feat(console): Divi asset library browser (from the tooling DB).
- **#p2-4** feat(console): translation review queue (Phase 3 hook).

## Milestone: Phase 3 — Consolidation & AI Translation
- **#p3-1** chore(i18n): install UpdraftPlus on the ES site; full backups of both sites.
- **#p3-2** chore(divi): standardize Divi (4.27.4→4.27.7) + Divi Carousel (3.0.6→3.2.1) across envs; inventory ASE settings.
- **#p3-3** feat(i18n): install + configure Polylang Pro; establish EN↔ES translation pairs.
- **#p3-4** feat(i18n): merge ES into English — WXR import + **Divi-aware globals reconcile** (Global Colors, presets, Theme Builder, `et_pb_layout`).
- **#p3-5** feat(i18n): `/es/` URL structure + `hreflang` + 301 redirect map (`iglesiavertical.com` → `/es/`).
- **#p3-6** spike(i18n): validate Divi Theme Builder × Polylang (template translation/assignment).
- **#p3-7** feat(i18n): Azure OpenAI translation-draft service with **field-level guard** + human review.
- **#p3-8** feat(i18n): merge validation pass-criteria script (counts, media/links, pairs, menus, hreflang).

## Milestone: Phase 4 — Azure Host, Migrate & Cutover
- **#p4-1** spike(infra): choose Azure WordPress hosting (App Service for Containers vs VM).
- **#p4-2** feat(infra): provision Azure WordPress + Redis object cache + raised PHP upload limit.
- **#p4-3** feat(infra): staging environment mirror + local→staging→prod promotion pipeline.
- **#p4-4** feat(infra): production cutover runbook (DNS via GoDaddy) + rehearsed rollback.
