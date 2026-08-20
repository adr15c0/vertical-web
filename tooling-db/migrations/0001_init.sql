-- Vertical tooling DB — schema v0 (issue #6)
--
-- The tooling DB is the project's own store (separate from the operational
-- "Vertical DB"). It holds the Divi asset registry + versions, AI translation
-- drafts with human-review state, inventory snapshots, and a job/audit log.
--
-- Idempotent: safe to run repeatedly. Used both as the Postgres initdb bootstrap
-- (.ddev/docker-compose.postgres.yaml) and by scripts/local/tooling_db.sh migrate.

BEGIN;

-- Auto-maintain updated_at on UPDATE.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1) divi_assets — registry of managed Divi assets (Library layouts, presets,
--    Theme Builder templates, Global Colors sets, page layouts).
CREATE TABLE IF NOT EXISTS divi_assets (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_key       text NOT NULL UNIQUE,
  asset_type      text NOT NULL CHECK (asset_type IN
                    ('library_layout','module_preset','theme_builder_template',
                     'global_colors','page_layout')),
  title           text NOT NULL,
  language        text,                              -- 'en' | 'es' | NULL (shared)
  wp_post_id      integer,                           -- linked WP post, if any
  source          text NOT NULL DEFAULT 'generated'
                    CHECK (source IN ('generated','imported','manual')),
  status          text NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','active','archived')),
  current_version integer,                           -- -> asset_versions.version
  metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_divi_assets_type   ON divi_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_divi_assets_lang   ON divi_assets(language);
CREATE INDEX IF NOT EXISTS idx_divi_assets_status ON divi_assets(status);
DROP TRIGGER IF EXISTS trg_divi_assets_updated ON divi_assets;
CREATE TRIGGER trg_divi_assets_updated BEFORE UPDATE ON divi_assets
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 2) asset_versions — immutable content versions of an asset (the Divi JSON /
--    shortcode / preset / global-colors payload).
CREATE TABLE IF NOT EXISTS asset_versions (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id       uuid NOT NULL REFERENCES divi_assets(id) ON DELETE CASCADE,
  version        integer NOT NULL,
  content        jsonb NOT NULL,
  content_format text NOT NULL DEFAULT 'divi_layout_json'
                    CHECK (content_format IN
                      ('divi_layout_json','shortcode','preset_json','global_colors_json')),
  checksum       text,                               -- sha256 of canonical content
  created_by     text,
  created_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (asset_id, version)
);
CREATE INDEX IF NOT EXISTS idx_asset_versions_asset ON asset_versions(asset_id);

-- 3) translation_drafts — AI draft + human review state, per field/segment.
--    Preserves intentional EN/ES divergence via the `diverged` guard.
CREATE TABLE IF NOT EXISTS translation_drafts (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  object_type   text NOT NULL CHECK (object_type IN ('wp_post','divi_asset','string')),
  source_ref    text NOT NULL,                       -- wp post id / asset_key / string key
  field         text NOT NULL,                       -- which field / segment
  source_lang   text NOT NULL DEFAULT 'en',
  target_lang   text NOT NULL DEFAULT 'es',
  source_text   text,
  draft_text    text,                                -- AI draft (Azure OpenAI)
  reviewed_text text,                                -- human override (bilingual reviewer)
  status        text NOT NULL DEFAULT 'pending'
                  CHECK (status IN
                    ('pending','drafted','in_review','approved','rejected','published')),
  engine        text,                                -- e.g. 'azure_openai:gpt-4o'
  reviewer      text,
  diverged      boolean NOT NULL DEFAULT false,      -- intentional EN/ES divergence
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (object_type, source_ref, field, target_lang)
);
CREATE INDEX IF NOT EXISTS idx_tdrafts_status ON translation_drafts(status);
CREATE INDEX IF NOT EXISTS idx_tdrafts_object ON translation_drafts(object_type, source_ref);
DROP TRIGGER IF EXISTS trg_tdrafts_updated ON translation_drafts;
CREATE TRIGGER trg_tdrafts_updated BEFORE UPDATE ON translation_drafts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 4) inventory_snapshots — point-in-time inventory captures (e.g. divi_recon).
CREATE TABLE IF NOT EXISTS inventory_snapshots (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  taken_at      timestamptz NOT NULL DEFAULT now(),
  environment   text NOT NULL DEFAULT 'local'
                  CHECK (environment IN ('local','staging','prod')),
  site          text NOT NULL DEFAULT 'en' CHECK (site IN ('en','es')),
  kind          text NOT NULL,                       -- 'divi_recon','content','media',...
  summary       jsonb NOT NULL DEFAULT '{}'::jsonb,
  artifact_path text
);
CREATE INDEX IF NOT EXISTS idx_inv_kind  ON inventory_snapshots(kind);
CREATE INDEX IF NOT EXISTS idx_inv_taken ON inventory_snapshots(taken_at DESC);

-- 5) job_log — audit/job log for pipeline + refresh operations.
CREATE TABLE IF NOT EXISTS job_log (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job         text NOT NULL,                         -- job name / type
  status      text NOT NULL DEFAULT 'started'
                CHECK (status IN ('started','success','error','warning')),
  ran_at      timestamptz NOT NULL DEFAULT now(),
  duration_ms integer,
  context     jsonb NOT NULL DEFAULT '{}'::jsonb,
  message     text,
  error       text
);
CREATE INDEX IF NOT EXISTS idx_joblog_job    ON job_log(job);
CREATE INDEX IF NOT EXISTS idx_joblog_status ON job_log(status);
CREATE INDEX IF NOT EXISTS idx_joblog_ran    ON job_log(ran_at DESC);

-- Applied-migrations marker.
CREATE TABLE IF NOT EXISTS schema_migrations (
  version    text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO schema_migrations(version) VALUES ('0001_init')
  ON CONFLICT (version) DO NOTHING;

COMMIT;
