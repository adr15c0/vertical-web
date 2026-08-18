# vertical-web

Monorepo for the **Vertical Church** website consolidation and modernization: merging two
separately maintained WordPress installs (English `goverticalchurch.com` and Spanish
`iglesiavertical.com`) into a **single Divi-based WordPress site** with a shared skeleton,
a programmatic Divi asset pipeline, an internal admin console, and AI-assisted (human-reviewed)
translation.

> **Status:** planning complete, execution starting. See [`docs/plan/00-overview.md`](docs/plan/00-overview.md).

## What this is

- **Public site:** stays on **WordPress + Divi 4** (Classic Editor / Divi Builder). No block theme,
  no `theme.json`, no Gutenberg re-platform.
- **Asset pipeline:** generates **Divi-native** assets — Theme Builder templates, Divi Library
  layouts (`et_pb_layout` JSON), module presets, Global Colors, and page content (Divi shortcodes) —
  pushed via WP-CLI/REST. Material UI is used only as a *design reference*, never installed on the site.
- **Internal console:** a React app on the WP REST API for non-developer staff to edit **content/data**
  (layout/design stays in the Divi Visual Builder).
- **Multilingual:** Polylang (Pro), Spanish at `/es/`, with **Azure OpenAI** drafting translations that
  a **bilingual human reviews** — intentional EN/ES divergence is preserved.
- **Tooling DB:** a separate **Postgres on Azure** store for the Divi asset registry, translation
  drafts/review state, and inventory/audit logs (distinct from WordPress MySQL and from Vertical DB).

## Repository layout

| Path | Purpose |
|------|---------|
| `docs/plan/` | The full plan (numbered by section) + the GitHub backlog. |
| `child-theme/` | Divi child theme — the only place custom theme code lives. |
| `mu-plugins/` | Versioned must-use plugins (custom post types, taxonomies, integrations). |
| `asset-pipeline/` | Divi asset generator (Library layouts / presets / Global Colors) + WP push (REST + WP-CLI). |
| `console/` | React internal admin console (content/data editing on the WP REST API). |
| `.github/` | CI, issue/PR templates, CODEOWNERS, governance. |

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. In short: trunk-based flow, short-lived
`feat/…` · `fix/…` · `chore/…` branches, **Conventional Commits**, PRs into a protected `main`
with green CI and review, and squash-merge. Every PR links its issue (`Closes #123`).

## Infrastructure note

The original DigitalOcean droplet (Ploi-managed) is **orphaned** — no server credentials could be
recovered — so it is treated as a **read-only data source**. The consolidated site will be
**rebuilt on Azure** (subscription owned by the maintainer), which also aligns with Vertical DB
already running on Azure.

## License

Proprietary — see [`LICENSE`](LICENSE). © 2026 Vertical Church. All rights reserved.
