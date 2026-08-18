# 02 — Multilingual layer

**Decision:** **Polylang (Pro)** links English and Spanish as translation pairs while allowing content
to differ. Spanish lives at **`/es/`** (subdirectory) on the canonical domain.

## Polylang Pro vs WPML (summary)

Both link posts as translation pairs and handle CPTs, custom fields, menus, widgets, media, a language
switcher, and REST. For this project **Polylang Pro** is recommended: lighter, well-supported, clean
REST behavior, and strong support for CPTs/custom fields via the ACF/Polylang patterns we'll use. WPML
is heavier and its all-in-one bundle adds surface area we don't need. The deciding factor is
operational simplicity for a very small maintenance team.

> **Validation required:** Divi **Theme Builder × Polylang** interaction (how Theme Builder templates
> are assigned/translated per language). This is a known edge area and is an explicit Phase 3 check.

## URL structure — Spanish

**Chosen: subdirectory `/es/`** on `goverticalchurch.com`.

| Option | SEO / migration consequence |
|--------|-----------------------------|
| **Subdirectory `/es/`** ✅ | Consolidates domain authority; simplest `hreflang`; cleanest single-install ops |
| Subdomain `es.` | Treated more independently by search; extra DNS/cert surface |
| Separate domain (`iglesiavertical.com`) | Retains legacy authority but fights the consolidation goal |

- Implement **`hreflang`** (`en` ↔ `es`) sitewide.
- **301-redirect** `iglesiavertical.com` URLs to their `/es/` equivalents (redirect map built in
  [06](06-migration-merge.md)); redirects go live at cutover.

## Translation content model

- **AI drafts, humans decide.** Azure OpenAI proposes translations into a review queue; a **bilingual
  reviewer** approves/edits. Approved text writes to the Polylang Spanish post.
- **Field-level guard:** AI only fills empty/flagged fields and never overwrites human-edited content,
  preserving the intentional EN/ES divergence. This is *not* a blind machine-translation project.
