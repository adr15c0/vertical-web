-- Vertical tooling DB — schema v1 (registry data model).
--
-- Extends schema v0 (0001_init.sql). Design principles:
--   * CONTENT lives in WordPress (MySQL). This DB is a REGISTRY + review-state +
--     audit layer that POINTS AT WordPress content — never a second copy of it.
--   * Assets/content exist once but live at DIFFERENT WordPress post IDs per
--     ENVIRONMENT (local/staging/prod), so mappings are per-environment.
--   * Translation is field-level with review state and a divergence/lock guard
--     ("AI drafts, human decides, never overwrite intentional EN/ES divergence").
--
-- Idempotent: safe to re-run.

BEGIN;

-- --------------------------------------------------------------------------- --
-- environments — deploy targets (local / staging / prod)
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS environments (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key        text NOT NULL UNIQUE CHECK (key IN ('local','staging','prod')),
  label      text NOT NULL,
  base_url   text,
  is_default boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO environments(key, label, base_url, is_default) VALUES
  ('local',   'Local (DDEV)', 'https://vertical-web.ddev.site', true),
  ('staging', 'Staging (Azure)', NULL, false),
  ('prod',    'Production (Azure)', NULL, false)
ON CONFLICT (key) DO NOTHING;

-- --------------------------------------------------------------------------- --
-- console_users — who may use the console (auth/roles)
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS console_users (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email      text NOT NULL UNIQUE,
  name       text,
  role       text NOT NULL DEFAULT 'viewer'
               CHECK (role IN ('admin','editor','translator','viewer')),
  wp_user_id integer,
  active     boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- --------------------------------------------------------------------------- --
-- content_items — registry of WordPress content the tooling tracks.
-- Identity + metadata only (title is a convenience label; WP is source of truth).
-- translation_group links EN/ES siblings (Polylang pair).
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS content_items (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind              text NOT NULL,          -- page|post|event|sermon|ministry|staff|campus|location|divi_library|theme_builder
  slug              text,
  title             text,
  language          text,                   -- 'en' | 'es' | NULL (shared)
  translation_group uuid,                   -- shared by EN/ES siblings
  source_of_truth   text NOT NULL DEFAULT 'wordpress'
                      CHECK (source_of_truth IN ('wordpress','vertical_db')),
  metadata          jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kind, slug, language)
);
CREATE INDEX IF NOT EXISTS idx_content_items_group ON content_items(translation_group);
CREATE INDEX IF NOT EXISTS idx_content_items_kind  ON content_items(kind);
DROP TRIGGER IF EXISTS trg_content_items_updated ON content_items;
CREATE TRIGGER trg_content_items_updated BEFORE UPDATE ON content_items
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- --------------------------------------------------------------------------- --
-- content_locations — where a content_item lives in EACH environment
-- (solves "same content, different WP post id per environment").
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS content_locations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_item_id uuid NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  environment_id  uuid NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
  wp_post_id      integer,
  wp_post_type    text,
  url             text,
  status          text,                     -- draft|publish|private
  last_seen_at    timestamptz,
  UNIQUE (content_item_id, environment_id)
);
CREATE INDEX IF NOT EXISTS idx_content_locations_env ON content_locations(environment_id);

-- --------------------------------------------------------------------------- --
-- divi_assets — link the pipeline asset registry to a content_item.
-- (wp_post_id kept for backward-compat; real per-env mapping is asset_publications.)
-- --------------------------------------------------------------------------- --
ALTER TABLE divi_assets ADD COLUMN IF NOT EXISTS content_item_id uuid
  REFERENCES content_items(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_divi_assets_content ON divi_assets(content_item_id);

-- --------------------------------------------------------------------------- --
-- asset_publications — record of publishing an asset version to an environment
-- (which version is live where).
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS asset_publications (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id       uuid NOT NULL REFERENCES divi_assets(id) ON DELETE CASCADE,
  version        integer NOT NULL,
  environment_id uuid NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
  wp_post_id     integer,
  status         text NOT NULL DEFAULT 'live'
                   CHECK (status IN ('live','superseded','rolled_back')),
  published_by   text,
  job_id         bigint REFERENCES job_log(id) ON DELETE SET NULL,
  published_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_asset_pub_asset ON asset_publications(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_pub_env   ON asset_publications(environment_id);
-- one live publication per asset per environment
CREATE UNIQUE INDEX IF NOT EXISTS uq_asset_pub_live
  ON asset_publications(asset_id, environment_id) WHERE status = 'live';

-- --------------------------------------------------------------------------- --
-- translation_units — field-level translation + review state (replaces the
-- unused v0 translation_drafts starter). AI drafts, humans decide.
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS translation_units (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_item_id uuid REFERENCES content_items(id) ON DELETE CASCADE,
  object_type     text NOT NULL DEFAULT 'content_item'
                    CHECK (object_type IN ('content_item','divi_asset','string')),
  object_ref      text NOT NULL DEFAULT '',  -- asset_key / string key when not a content_item
  field           text NOT NULL,             -- e.g. post_title, body:section1, button_text
  source_lang     text NOT NULL DEFAULT 'en',
  target_lang     text NOT NULL DEFAULT 'es',
  source_text     text,
  source_hash     text,                      -- detects source changes -> re-draft
  draft_text      text,                      -- AI draft (Azure OpenAI)
  reviewed_text   text,                      -- human final
  status          text NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','drafted','in_review','approved','rejected','published')),
  engine          text,                      -- e.g. azure_openai:gpt-4o
  reviewer_id     uuid REFERENCES console_users(id) ON DELETE SET NULL,
  diverged        boolean NOT NULL DEFAULT false, -- intentional EN/ES divergence
  locked          boolean NOT NULL DEFAULT false, -- never let AI touch
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (object_type, object_ref, field, target_lang)
);
CREATE INDEX IF NOT EXISTS idx_tunits_status  ON translation_units(status);
CREATE INDEX IF NOT EXISTS idx_tunits_content ON translation_units(content_item_id);
DROP TRIGGER IF EXISTS trg_tunits_updated ON translation_units;
CREATE TRIGGER trg_tunits_updated BEFORE UPDATE ON translation_units
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Retire the empty v0 starter (0 rows, superseded by translation_units).
DROP TABLE IF EXISTS translation_drafts;

-- --------------------------------------------------------------------------- --
-- audit_log — human/console actions (complements job_log = pipeline jobs).
-- --------------------------------------------------------------------------- --
CREATE TABLE IF NOT EXISTS audit_log (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor          text NOT NULL,             -- user email or 'pipeline'
  action         text NOT NULL,             -- asset.publish | translation.approve | content.edit ...
  object_type    text,
  object_ref     text,
  environment_id uuid REFERENCES environments(id) ON DELETE SET NULL,
  detail         jsonb NOT NULL DEFAULT '{}'::jsonb,
  at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_at     ON audit_log(at DESC);

-- job_log: link jobs to an environment for filtering.
ALTER TABLE job_log ADD COLUMN IF NOT EXISTS environment_id uuid
  REFERENCES environments(id) ON DELETE SET NULL;

INSERT INTO schema_migrations(version) VALUES ('0002_registry_v1')
  ON CONFLICT (version) DO NOTHING;

COMMIT;
