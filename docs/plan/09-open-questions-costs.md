# 09 — Open questions & costs

## Resolved during planning
- **Divi license:** active and current (English site) — not nulled. ES license not separately confirmed
  (low risk, same account likely).
- **Infra access:** Ploi/DigitalOcean/ManageWP owner not found → legacy droplet is a **read-only data
  source**; target is **new WordPress on Azure** (subscription owned).
- **DNS:** both domains controlled via **GoDaddy** → Phase 4 cutover unblocked.
- **Canonical install:** English. **POC:** runs on a **local** DDEV copy of English (no production edits).

## Still open
- **ASE (Admin & Site Enhancements)** on the Spanish site — inventory its active settings before the
  merge (it can alter permalinks/redirects/login behavior).
- **Divi Theme Builder × Polylang** — explicit validation needed (template translation/assignment).
- **Vertical DB integration** — research spike (access method, caching, scheduled refresh).
- **Azure WordPress hosting shape** — App Service for Containers vs VM (Phase 4 decision).
- **ES Divi license** — quick confirm when convenient.

## Costs — verify current pricing yourself (do not rely on figures here)
- **Polylang Pro** license (annual).
- **Azure OpenAI** usage (translation drafting) — token-based.
- **Azure Postgres** (tooling DB) + **Azure WordPress hosting** + **Redis** cache.
- **Divi** renewal (already licensed) and any third-party module Pro upgrades if needed.
- Domain renewals (GoDaddy).

> Recommendation: price the Azure footprint with the Azure Pricing Calculator against expected traffic
> before committing to a hosting shape in Phase 4.
