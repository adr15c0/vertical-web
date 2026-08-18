# 03 — Theme architecture (Divi-native)

> **This section is deliberately rewritten away from the original prompt's "block theme + `theme.json`"
> framing.** The site stays on **Divi 4 + Classic Editor** (explicit decision), so a block theme is out
> of scope. The concept — a centralized, authored-once design system with reusable, programmatically
> managed assets — is delivered with **Divi's own primitives**.

## Concept → Divi mapping

| Goal (unchanged) | Block-theme idea (rejected) | Divi-native implementation |
|------------------|-----------------------------|----------------------------|
| Author skeleton once, shared across languages | Template parts | **Divi Theme Builder** global header/footer + body templates (already in use — 3 templates) |
| Centralized design tokens | `theme.json` | **Divi Global Colors + module presets + Theme Options** |
| Reusable, managed assets | Block patterns | **Divi Library layouts** (`et_pb_layout` JSON) + **module presets** |
| Custom code | `functions.php` in block theme | **Divi child theme** (`child-theme/`) |

## Design token strategy

- Centralize palette, typography, and spacing in **Divi Global Colors** and a small set of **module
  presets**; pages reference these rather than hardcoding styles.
- The **asset pipeline** (`asset-pipeline/`) generates Divi Library layouts, presets, and Global Colors
  — using Material UI patterns only as a **design reference** — and pushes them via WP-CLI/REST. A
  creative then assembles/edits them in the **Divi Visual Builder**.

## Language-agnostic guarantee

- Theme Builder templates and Divi layouts contain **no hardcoded UI strings**; all copy comes from
  content or **Polylang string translation**. Language selection never forks the skeleton.

## Hard dependency: third-party modules

Divi stores layouts as **shortcodes**; a shortcode only renders if its plugin is present. Layouts use
**Supreme Modules Lite** (EN) and **Divi Carousel Free** (both). Every environment (local, staging,
merged, Azure) **must carry the same add-ons at pinned versions**, or layouts render blank. Cataloguing
these module dependencies is a Phase 0 task.

## Divi 5

The sites are on **Divi 4**. Divi 5 is a ground-up rewrite with a migration path and add-on
compatibility risk. **Stay on Divi 4** for the entire consolidation; evaluate Divi 5 separately on
staging later. Do **not** enable Divi 5 updates on production.
