# console

The **internal admin console** — a React app on the WordPress REST API for **non-developer staff**.

Scope (intentionally narrow):
- Edit **content/data** (pages, CPT entries), swap media.
- Browse the **Divi asset library** (from the Postgres tooling DB).
- **Translation queue**: review AI-drafted translations (Phase 3).

Out of scope: building layouts. **Layout/design stays in the Divi Visual Builder.** The console must
not try to reinvent Divi's builder.

Backends: WordPress REST API (content) + Postgres tooling DB (asset registry, translation drafts,
audit log). Local-only hosting for now; production hosting decided during the Azure build (Phase 4).
