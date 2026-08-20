#!/usr/bin/env bash
#
# seed-local.sh — Build/refresh the local DDEV WordPress from the extracted
# English production backup (backups/en). Faithful Phase 0 replica.
#
# Safe to re-run: re-imports the DB and re-syncs theme/plugins/uploads.
# Requires: ddev, the extracted backups/en/database.sql (from the AIOWM .wpress).
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

BACKUP_DIR="backups/en"
DB_SRC="$BACKUP_DIR/database.sql"
DB_IMPORT="$BACKUP_DIR/database.import.sql"
WP_DIR="wordpress"
PROD_URL="https://goverticalchurch.com"
LOCAL_URL="https://vertical-web.ddev.site"
WP_VERSION="7.0.4"   # match production; falls back to latest if unavailable

log() { printf '\n==> %s\n' "$*"; }

command -v ddev >/dev/null 2>&1 || { echo "ERROR: ddev not installed"; exit 1; }
[ -f "$DB_SRC" ] || { echo "ERROR: $DB_SRC not found — extract the .wpress first"; exit 1; }

log "[1/8] Build import file: de-token prefix + disable FK/unique checks"
# AIOWM stores table names AND prefixed option/meta keys (wp_user_roles, wp_capabilities, ...)
# tokenized as SERVMASK_PREFIX_. A global replace restores all of them correctly.
# AIOWM's dump does not manage FOREIGN_KEY_CHECKS, so plugin tables with inter-table
# FKs (e.g. wp_userfeedback_survey_responses -> wp_userfeedback_surveys) fail on CREATE
# unless checks are off for the session. Prepend the guards; they persist for the import.
{
  echo "SET FOREIGN_KEY_CHECKS=0;"
  echo "SET UNIQUE_CHECKS=0;"
  sed 's/SERVMASK_PREFIX_/wp_/g' "$DB_SRC"
  echo "SET FOREIGN_KEY_CHECKS=1;"
  echo "SET UNIQUE_CHECKS=1;"
} > "$DB_IMPORT"

log "[2/8] Start DDEV"
ddev start

log "[3/8] Download WordPress core (if missing)"
if [ ! -f "$WP_DIR/wp-load.php" ]; then
  ddev wp core download --version="$WP_VERSION" --force \
    || ddev wp core download --force
fi

log "[4/8] Ensure wp-config (DDEV DB creds: db/db/db, host 'db')"
if [ ! -f "$WP_DIR/wp-config.php" ]; then
  ddev wp config create --dbname=db --dbuser=db --dbpass=db --dbhost=db --force
fi
# DDEV injects wp-config-ddev.php include on start; re-run start to be safe.
ddev start >/dev/null

log "[5/8] Import database"
ddev import-db --file="$DB_IMPORT"

log "[6/8] Sync Divi theme + third-party plugins + mu-plugins from backup"
mkdir -p "$WP_DIR/wp-content/themes" "$WP_DIR/wp-content/plugins"
rsync -a --delete "$BACKUP_DIR/themes/Divi/" "$WP_DIR/wp-content/themes/Divi/"
[ -d "$BACKUP_DIR/plugins" ]    && rsync -a "$BACKUP_DIR/plugins/"    "$WP_DIR/wp-content/plugins/"
if [ -d "$BACKUP_DIR/mu-plugins" ]; then
  mkdir -p "$WP_DIR/wp-content/mu-plugins"
  rsync -a "$BACKUP_DIR/mu-plugins/" "$WP_DIR/wp-content/mu-plugins/"
fi

log "[7/8] Merge uploads (uploads + uploads-2..9 volumes) into one tree"
mkdir -p "$WP_DIR/wp-content/uploads"
for d in "$BACKUP_DIR"/uploads "$BACKUP_DIR"/uploads-*; do
  [ -d "$d" ] || continue
  rsync -a "$d/" "$WP_DIR/wp-content/uploads/"
done

log "[8/9] Serialized-safe URL search-replace + flush caches/rewrites"
ddev wp search-replace "$PROD_URL" "$LOCAL_URL" --all-tables --precise --skip-columns=guid
# also normalize any protocol-relative or http variants
ddev wp search-replace "//goverticalchurch.com" "//vertical-web.ddev.site" --all-tables --precise --skip-columns=guid || true
ddev wp cache flush   || true
ddev wp rewrite flush || true

log "[9/9] Activate Divi + production plugin set (AIOWM DB-only export blanks these)"
# AIOWM blanks template/stylesheet/active_plugins when files are excluded from export.
# Re-activate to faithfully match production (EN active set; Site Kit stays inactive).
ddev wp theme activate Divi
# Production EN active plugins (slugs as they appear on disk):
PROD_PLUGINS=(
  akismet
  tuxedo-big-file-uploads      # Big File Uploads
  classic-editor
  wow-carousel-for-divi-lite   # Divi Carousel Free
  divi-dashboard
  filester
  independent-analytics
  worker                       # ManageWP Worker
  mime-types-plus
  supreme-modules-for-divi     # Supreme Modules Lite
  updraftplus
  insert-headers-and-footers   # WPCode Lite
)
for p in "${PROD_PLUGINS[@]}"; do
  ddev wp plugin activate "$p" 2>/dev/null || echo "  (skip: $p not present)"
done
# Site Kit stays INACTIVE to match production.
ddev wp cache flush || true

log "Seed complete."
echo "  Site:  $LOCAL_URL"
echo "  Admin: $LOCAL_URL/wp-admin  (use the production admin credentials in the DB)"
echo "  Verify a Divi page opens in the Visual Builder to close issue #p0-1."
