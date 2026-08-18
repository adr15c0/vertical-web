# mu-plugins

Versioned **must-use plugins**: custom post types, taxonomies, and integration code that must load
on every environment.

Planned (Phase 1):
- Content model: `events`, `sermons`, `ministries`, `staff`, `campuses`, `locations` — with fields
  marked translatable vs. shared, rendered via Divi Theme Builder templates.
- Vertical DB integration (Phase 3+ spike): a language-aware fetch layer surfaced to Divi via a
  shortcode/module, transient-cached.

> Registered in code (not clicked into the admin) so the model is reproducible and reviewable.
