# Contributing

## Workflow (trunk-based)

1. Branch off `main` with a short-lived branch:
   - `feat/<scope>-<short-desc>` — new capability
   - `fix/<scope>-<short-desc>` — bug fix
   - `chore/<scope>-<short-desc>` — tooling, docs, deps, refactors
2. Make focused commits using **Conventional Commits** (see below).
3. Open a PR into `main`. Fill in the PR template. Link the issue with `Closes #<n>`.
4. CI must be green and at least one review approved. Merge via **squash-merge**.
5. `main` is protected: no direct pushes, linear history, required checks + review.

## Conventional Commits

```
<type>(<scope>): <subject>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `build`, `perf`.
Scopes (suggested): `divi`, `console`, `pipeline`, `mu-plugins`, `theme`, `infra`, `i18n`,
`docs`, `governance`.

Examples:
- `feat(pipeline): generate Divi Library layout JSON from a design token set`
- `fix(mu-plugins): correct events CPT rewrite slug`
- `docs(plan): clarify Divi Theme Builder × Polylang validation step`

## Branch → PR → Issue linking

- One issue per unit of work; PRs reference issues (`Closes #`, `Refs #`).
- Issues are attached to a **Milestone** (Phase 0–4) and carry `phase:*`, `area:*`, and
  `type:*` labels.

## Local expectations

- Never commit WordPress core, uploads, DB dumps, third-party plugins, or secrets.
- Custom theme code lives only in `child-theme/`. Site behavior/CPTs live in `mu-plugins/`.
- Database changes travel as versioned WP-CLI/SQL migration scripts, not as schema in Git.
