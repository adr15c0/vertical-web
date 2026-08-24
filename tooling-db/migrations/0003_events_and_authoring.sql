-- Vertical tooling DB — schema v1.1 (events catalog + source-language authoring).
--
-- Extends v1 (0002_registry_v1.sql). Two capabilities:
--   1. AUTHORING BUFFER — non-devs author field-level SOURCE text in the console.
--      Stored here as versioned, reviewable drafts (content_fields +
--      content_field_revisions), then PUBLISHED into WordPress. WordPress stays
--      the PUBLISHED source of truth; this is the working copy + history + review
--      state — the symmetric source-language half of translation_units.
--      Boundary: console-authored fields flow one-way console -> WP (single writer
--      per field); layout stays in the Divi Visual Builder, so drafts never drift.
--   2. EVENTS CATALOG — structured events (like christfellowship.church/events):
--      campuses + categories (filters), fuzzy "when", registration, featured.
--      Runtime rendering is a WP CPT `event`; this models the authoring/registry
--      side. Nullable external_source/external_id/last_synced_at make a Planning
--      Center feed possible later with NO migration (deferred by decision).
--
-- Idempotent: safe to re-run.

BEGIN;

-- ========================================================================== --
-- AUTHORING
-- ========================================================================== --

-- --------------------------------------------------------------------------- --
-- content_fields — field-level SOURCE content authored in the console.
-- field_key vocabulary is per content kind (e.g. page/event): title, summary,
-- body, when_text, cta_label, cta_url, ... value = plain text, value_json =
-- structured/rich payload when a field needs it.
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS content_fields (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_item_id uuid NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  field_key       text NOT NULL,
  language        text NOT NULL DEFAULT 'en',
  value           text,
  value_json      jsonb,
  status          text NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','in_review','approved','published')),
  version         integer NOT NULL DEFAULT 1,
  updated_by      uuid REFERENCES console_users(id) ON DELETE SET NULL,
  published_at    timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (content_item_id, field_key, language)
);
CREATE INDEX IF NOT EXISTS idx_content_fields_item   ON content_fields(content_item_id);
CREATE INDEX IF NOT EXISTS idx_content_fields_status ON content_fields(status);
DROP TRIGGER IF EXISTS trg_content_fields_updated ON content_fields;
CREATE TRIGGER trg_content_fields_updated BEFORE UPDATE ON content_fields
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- --------------------------------------------------------------------------- --
-- content_field_revisions — append-only edit history (rollback + audit).
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS content_field_revisions (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  content_field_id uuid NOT NULL REFERENCES content_fields(id) ON DELETE CASCADE,
  version          integer NOT NULL,
  value            text,
  value_json       jsonb,
  status           text,
  edited_by        uuid REFERENCES console_users(id) ON DELETE SET NULL,
  edited_at        timestamptz NOT NULL DEFAULT now(),
  note             text,
  UNIQUE (content_field_id, version)
);
CREATE INDEX IF NOT EXISTS idx_field_rev_field ON content_field_revisions(content_field_id);

-- ========================================================================== --
-- EVENTS CATALOG
-- ========================================================================== --

-- --------------------------------------------------------------------------- --
-- campuses — controlled vocab for the "filter by campus" dropdown. Optionally
-- linked to a content_items row (kind='campus') when a campus landing page exists.
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS campuses (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key             text NOT NULL UNIQUE,
  name            text NOT NULL,
  city            text,
  address         text,
  timezone        text,
  content_item_id uuid REFERENCES content_items(id) ON DELETE SET NULL,
  active          boolean NOT NULL DEFAULT true,
  sort            integer NOT NULL DEFAULT 0,
  external_source text CHECK (external_source IN ('planning_center')),
  external_id     text,
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- --------------------------------------------------------------------------- --
-- event_categories — controlled vocab for the audience/category tabs
-- (e.g. Kids, Men, Next Steps, Special Events). Org-specific; seed via console.
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS event_categories (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key        text NOT NULL UNIQUE,
  name       text NOT NULL,
  sort       integer NOT NULL DEFAULT 0,
  active     boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- --------------------------------------------------------------------------- --
-- event_details — structured catalog attributes for a content_items row of
-- kind='event' (1:1). Dates are all nullable; when_text carries the fuzzy
-- display cases ("Monthly", "Sept 24 OR 25", "See Details for Date").
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS event_details (
  content_item_id     uuid PRIMARY KEY REFERENCES content_items(id) ON DELETE CASCADE,
  starts_at           timestamptz,
  ends_at             timestamptz,
  all_day             boolean NOT NULL DEFAULT false,
  recurrence          text,                 -- 'none' | 'weekly' | 'monthly' | rrule
  when_text           text,                 -- free display override for fuzzy dates
  location_text       text,                 -- e.g. "Multiple Locations" free display
  registration_url    text,
  registration_status text NOT NULL DEFAULT 'none'
                        CHECK (registration_status IN ('none','open','closed','waitlist')),
  cost_text           text,
  featured            boolean NOT NULL DEFAULT false, -- "Discover Events For You"
  external_source     text CHECK (external_source IN ('planning_center')),
  external_id         text,
  last_synced_at      timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_event_details_starts   ON event_details(starts_at);
CREATE INDEX IF NOT EXISTS idx_event_details_featured ON event_details(featured) WHERE featured;
DROP TRIGGER IF EXISTS trg_event_details_updated ON event_details;
CREATE TRIGGER trg_event_details_updated BEFORE UPDATE ON event_details
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- --------------------------------------------------------------------------- --
-- event_campus_map / event_category_map — many-to-many (an event can be at
-- "Multiple Locations" and tagged with several audiences).
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS event_campus_map (
  event_item_id uuid NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  campus_id     uuid NOT NULL REFERENCES campuses(id) ON DELETE CASCADE,
  PRIMARY KEY (event_item_id, campus_id)
);

CREATE TABLE IF NOT EXISTS event_category_map (
  event_item_id uuid NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  category_id   uuid NOT NULL REFERENCES event_categories(id) ON DELETE CASCADE,
  PRIMARY KEY (event_item_id, category_id)
);

INSERT INTO schema_migrations(version) VALUES ('0003_events_and_authoring')
  ON CONFLICT (version) DO NOTHING;

COMMIT;
