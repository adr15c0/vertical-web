# 07 — Deployment pipeline

## Repository layout (monorepo)

```
vertical-web/
├─ child-theme/     # Divi child theme (custom code only)
├─ mu-plugins/      # CPTs, taxonomies, integrations (versioned)
├─ asset-pipeline/  # Divi Library/preset/Global-Color generator + WP push (REST + WP-CLI)
├─ console/         # React internal admin console (WP REST API)
├─ docs/plan/       # this plan + backlog
└─ .github/         # CI, templates, CODEOWNERS, governance
```

## Branching & PRs

- Trunk-based; protected `main`; short-lived `feat/…`·`fix/…`·`chore/…` branches.
- **Conventional Commits**, PR template, squash-merge, PRs link issues (`Closes #`).
- `main` requires: green CI + ≥1 review, linear history, no direct pushes. See
  [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).

## Environments & promotion

`local (DDEV)` → `staging (Azure)` → `production (Azure)`. The legacy droplet is **not** a deploy
target — it's a read-only data source that gets decommissioned after migration.

## What travels how

- **Theme + custom plugin code** → Git → deployed to environments.
- **WordPress core, third-party plugins, uploads, and the database** → **not** in Git. Third-party
  plugins are managed via **Composer (wpackagist)** where possible; Divi/premium via license.
- **Database changes** travel as **versioned WP-CLI/SQL migration scripts** run per environment (schema
  is not committed as data).

## CI (GitHub Actions)

- Now: repo hygiene (required files), JSON validation, secret scan (see `.github/workflows/ci.yml`).
- As code lands (path-filtered, currently stubbed): **PHPCS** (WordPress standards) for
  `child-theme/` + `mu-plugins/`, **lint+test** for `console/`, and **Divi Library JSON schema
  validation** for `asset-pipeline/`. Branch protection requires these green.

## Release checklist (both languages)

- Backups taken; migrations applied; smoke test EN `/` and ES `/es/`; `hreflang` + redirects verified;
  Divi layouts render; analytics intact.
