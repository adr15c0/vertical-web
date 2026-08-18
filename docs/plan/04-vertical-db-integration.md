# 04 — Vertical DB integration

**Status:** research spike (do not block earlier phases on this).

**Vertical DB** is an existing **PostgreSQL** database **hosted on Azure** that pulls church
operational data from **Planning Center** via the Planning Center API. It should be the **source of
truth** for operational data (service times, event schedules, ministry rosters), with WordPress as a
**rendering surface** only.

## Design (to be validated in the spike)

- **Fetch layer:** a small mu-plugin service that reads Vertical DB (or a thin API in front of it) on a
  schedule and on demand. Prefer a read-only connection / dedicated API rather than coupling WordPress
  to the DB directly.
- **Caching:** WordPress **transients** today (the legacy host has **no object cache**); on Azure, add
  **Redis** object cache for a shared, faster layer. Cache keys include language.
- **Scheduled refresh:** WP-Cron (or a real cron on Azure) refreshes cached operational data; stale
  data is served if a refresh fails, with a visible "last updated" and error logging to `job_log`.
- **Exposure to templates/blocks:** surface data through a **Divi shortcode/module** (Divi-native), so
  it drops into Theme Builder templates and Divi layouts.
- **Language handling:** operational data originating outside WordPress is mapped to the current
  Polylang language at render time (labels/strings via Polylang; raw data shared).
- **Auth & secrets:** connection string / API key stored in **Azure Key Vault** (never in Git);
  least-privilege, read-only credentials.

## Spike deliverables

- Confirm access method (direct read-only DB vs. REST/GraphQL in front of Vertical DB).
- A minimal proof: fetch service times, cache, and render via a Divi shortcode in both languages.
- A decision memo on scheduled-refresh + stale-data behavior.

Because Vertical DB is already **Postgres on Azure**, the project's **tooling DB** uses the same stack
for later horizontal integration.
