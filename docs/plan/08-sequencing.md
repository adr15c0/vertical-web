# 08 — Sequencing

Each phase ends in something **reviewable and reversible**. Production is only touched in Phase 4.

## Phase 0.5 — Repo governance (Step 0)
Bootstrap the repo with best practices **before** feature work: structure, protected `main`,
Conventional Commits, PR/issue templates, label taxonomy, milestones, CI, Dependabot.
**DoD:** repo initialized; protections + templates + labels + milestones live; CI green on bootstrap PR.

## Phase 0 — POC & Foundations (this week, local only)
Prove the **Divi asset pipeline** + programmatic round-trip locally; take inventory + backup.
DDEV WordPress seeded from an English export; verify WP-CLI; Postgres tooling DB; Divi-aware inventory;
MUI-referenced → Divi Library layout pushed via WP-CLI and **editable in the Visual Builder**;
REST↔WP-CLI round-trip with builder meta intact.
**DoD:** a Divi layout is visible + editable locally; backup + inventory exist; round-trip green.

## Phase 1 — Scaffolding, content model, Divi design system
Monorepo + CI; versioned **mu-plugin CPTs**; **Divi Theme Builder** skeleton; centralized **Global
Colors/presets**; **Divi child theme**. Can run partly in parallel with Phase 0's tail.
**DoD:** CI green; CPTs registered; Theme Builder skeleton renders EN; child theme active.

## Phase 2 — Internal admin console
React console on the WP REST API for non-dev **content/data** editing + Divi asset catalog +
translation queue. Layout stays in Divi. **Depends on** Phase 1 content model.
**DoD:** a staff editor updates content + swaps media via the console (locally), audited.

## Phase 3 — Consolidation + AI translation
English canonical; install UpdraftPlus on ES; standardize versions; **Polylang** pairs; **/es/** +
`hreflang` + 301s; Divi-aware merge; **Azure OpenAI** drafts → human review (field-guarded).
**Staging-first. Depends on** Phases 1 + 2.
**DoD (staging):** one install serves EN `/` and ES `/es/` with linked pairs; AI drafts flow through review.

## Phase 4 — Azure host, migrate, cutover
Provision Azure WordPress (+ Redis, raised upload limit); staging mirror; migrate data off the orphaned
droplet; **DNS cutover via GoDaddy**; rehearsed rollback. **Unblocked** (Azure + DNS owned).
**DoD:** rehearsed staging cutover + verified rollback; production cutover to Azure.

## Parallelism & production-risk flags
- Phase 0 and the Phase 0.5 governance run together at the start.
- Phase 1 and early Phase 2 can overlap once CPTs exist.
- **Production risk is confined to Phase 4** (DNS cutover). Phase 3 runs on staging.
