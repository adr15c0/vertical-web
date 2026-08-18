# 01 — Content model

Replace free-form pages for recurring content with **custom post types (CPTs)** and taxonomies,
registered in a **versioned must-use plugin** (not clicked into the admin) so the model is
reproducible and reviewable. Rendering uses **Divi Theme Builder** templates assigned per CPT.

## Proposed CPTs

| CPT | Purpose | Key fields | Translatable vs shared |
|-----|---------|-----------|------------------------|
| `event` | Services, one-off events | title, start/end, location (rel), description, CTA, image | title/description translatable; datetime/location shared |
| `sermon` | Message archive | title, speaker (rel staff), series (tax), date, video URL, scripture | title/notes translatable; video/date shared |
| `ministry` | Ministries/groups | name, description, leader (rel staff), meeting time, campus (rel) | name/description translatable; times/relations shared |
| `staff` | People | name, role, bio, photo, contact | role/bio translatable; photo/contact shared |
| `campus` | Physical campuses | name, address, service times, map | name translatable; address/map shared |
| `location` | Reusable place records | name, address, geo | name translatable; geo shared |

Taxonomies: `series` (sermons), `ministry_type`, `campus` (as relation/taxonomy where useful).

## Registration approach

- **Versioned mu-plugin** under `mu-plugins/` — recommended (agrees with the prompt). Rationale:
  survives theme changes, travels through Git, is diff-able and PR-reviewed, and can be unit-tested.
- Each CPT declares `show_in_rest = true` so the internal console and the asset pipeline can read/write
  it over the REST API.
- Translatable-vs-shared is enforced at the field level and honored by Polylang (see
  [02](02-multilingual.md)) and by the AI translation field-guard (see [06](06-migration-merge.md)).

## Templates

- Each CPT gets an **archive** and a **single** template built in **Divi Theme Builder**, assigned by
  post type. This keeps rendering inside Divi (no block templates) and language-agnostic (all copy comes
  from content/Polylang, no hardcoded strings).

## Open items

- Exact field lists per CPT to be finalized with staff during Phase 1.
- Whether `campus` is a CPT or a taxonomy depends on how much structured data each campus carries.
