#!/usr/bin/env bash
#
# Bootstrap GitHub governance for vertical-web: labels, milestones, issues,
# and branch protection. Idempotent-ish (safe to re-run; existing objects are skipped).
#
# Prereqs: gh authenticated with repo+project+workflow scopes; run from repo root
# after the repo exists and `origin` is set.
set -euo pipefail

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Bootstrapping governance for: $REPO"

# ------------------------------------------------------------------ labels
create_label () { # name color description
  gh label create "$1" --color "$2" --description "$3" --force >/dev/null 2>&1 || true
}
echo "== labels =="
create_label "phase:0"   "1D76DB" "POC & Foundations"
create_label "phase:0.5" "1D76DB" "Repo governance"
create_label "phase:1"   "1D76DB" "Scaffolding, content model, Divi design system"
create_label "phase:2"   "1D76DB" "Internal admin console"
create_label "phase:3"   "1D76DB" "Consolidation & AI translation"
create_label "phase:4"   "1D76DB" "Azure host, migrate, cutover"
create_label "area:divi"       "5319E7" "Divi theme / Theme Builder / Library / presets"
create_label "area:pipeline"   "5319E7" "Divi asset pipeline"
create_label "area:console"    "5319E7" "React internal admin console"
create_label "area:mu-plugins" "5319E7" "Custom post types / integrations"
create_label "area:i18n"       "5319E7" "Multilingual / Polylang / translation"
create_label "area:infra"      "5319E7" "Azure, DDEV, DB, DNS, hosting"
create_label "area:governance" "5319E7" "Repo, CI, process, docs"
create_label "type:feature" "0E8A16" "New capability"
create_label "type:bug"     "D73A4A" "Defect"
create_label "type:spike"   "FBCA04" "Time-boxed research"
create_label "type:chore"   "C2E0C6" "Tooling / deps / maintenance"
create_label "priority:high"   "B60205" "Do first"
create_label "priority:medium" "D93F0B" "Normal"
create_label "priority:low"    "0E8A16" "Nice to have"
create_label "risk:prod"       "B60205" "Touches or risks production"

# -------------------------------------------------------------- milestones
create_milestone () { # title description
  local existing
  existing="$(gh api "repos/$REPO/milestones?state=all" --jq ".[] | select(.title==\"$1\") | .number" 2>/dev/null || true)"
  if [[ -z "$existing" ]]; then
    gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null
    echo "milestone created: $1"
  else
    echo "milestone exists:  $1"
  fi
}
echo "== milestones =="
create_milestone "Phase 0.5 — Repo Governance" "Repo bootstrap, protections, templates, CI, labels, milestones."
create_milestone "Phase 0 — POC & Foundations" "Local Divi asset pipeline POC + inventory/backup."
create_milestone "Phase 1 — Scaffolding, Content Model & Divi Design System" "Monorepo/CI, CPT mu-plugin, Theme Builder skeleton, design tokens."
create_milestone "Phase 2 — Internal Admin Console" "React console on WP REST for non-dev content/data."
create_milestone "Phase 3 — Consolidation & AI Translation" "Merge ES into English; Polylang; Azure OpenAI drafts + human review."
create_milestone "Phase 4 — Azure Host, Migrate & Cutover" "Provision Azure WordPress; migrate; DNS cutover; rollback."

# ------------------------------------------------------------------ issues
issue () { # title labels milestone body
  local title="$1" labels="$2" milestone="$3" body="$4"
  if gh issue list --state all --search "\"$title\" in:title" --json title --jq '.[].title' | grep -qxF "$title"; then
    echo "issue exists:  $title"; return
  fi
  gh issue create --title "$title" --label "$labels" --milestone "$milestone" --body "$body" >/dev/null
  echo "issue created: $title"
}
ac () { printf '## Acceptance criteria\n%s\n' "$1"; }  # helper

echo "== issues: Phase 0.5 =="
issue "chore(governance): finalize branch protection on main" "type:chore,area:governance,phase:0.5,priority:high" "Phase 0.5 — Repo Governance" \
"$(ac '- [ ] `main` requires PR + green CI (Repo hygiene & docs)\n- [ ] Linear history; no force-push/deletion\n- [ ] Review required for non-admins; owner may bypass in emergencies')"
issue "chore(governance): create GitHub Project board and wire milestones" "type:chore,area:governance,phase:0.5,priority:medium" "Phase 0.5 — Repo Governance" \
"$(ac '- [ ] Project board created\n- [ ] Milestones (Phases 0–4) visible\n- [ ] Issues added to the board')"
issue "ci(governance): expand CI (PHPCS, console lint/test, Divi JSON schema) as code lands" "type:chore,area:governance,phase:0.5,priority:medium" "Phase 0.5 — Repo Governance" \
"$(ac '- [ ] Path-filtered PHPCS for child-theme/ + mu-plugins/\n- [ ] Lint+test for console/\n- [ ] Divi Library JSON schema validation for asset-pipeline/')"

echo "== issues: Phase 0 =="
issue "feat(infra): stand up DDEV WordPress locally seeded from English export" "type:feature,area:infra,phase:0,priority:high" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] DDEV WP runs locally\n- [ ] Seeded from EN UpdraftPlus/WXR export\n- [ ] wp search-replace handles serialized Divi data\n- [ ] A real Divi page opens in the Visual Builder')"
issue "chore(divi): install Divi + pinned add-ons locally; catalog module dependencies" "type:chore,area:divi,phase:0,priority:high" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] Divi + Supreme Modules Lite + Divi Carousel Free installed at pinned versions\n- [ ] Documented list of which layouts use which modules')"
issue "feat(infra): stand up Postgres tooling DB (schema v0)" "type:feature,area:infra,phase:0,priority:high" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] Postgres runs alongside DDEV\n- [ ] Tables: divi_assets, asset_versions, translation_drafts, inventory_snapshots, job_log')"
issue "feat(pipeline): inventory + backup job (incl. Divi Library/Theme Builder/Global Colors)" "type:feature,area:pipeline,phase:0,priority:high" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] Inventory of pages/posts/media/menus/plugins\n- [ ] Divi Library, Theme Builder templates, Global Colors captured\n- [ ] Snapshot rows written; full backup artifact produced')"
issue "feat(pipeline): Divi asset pipeline POC (generate layout JSON + preset + Global Colors, push via WP-CLI)" "type:feature,area:pipeline,phase:0,priority:high" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] Generate a Divi Library layout JSON (hero + card) using MUI as reference only\n- [ ] Generate a module preset + Global Colors\n- [ ] Push via WP-CLI (avoids 2M limit)\n- [ ] Layout is visible AND editable in the Divi Visual Builder')"
issue "feat(pipeline): REST <-> WP-CLI round-trip test with Divi builder meta intact" "type:feature,area:pipeline,phase:0,priority:medium" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] Create/update/read a page via REST + WP-CLI\n- [ ] _et_pb_use_builder meta + shortcodes intact\n- [ ] Result logged to job_log\n- [ ] REST-vs-CLI responsibilities documented')"
issue "spike(infra): verify full WP-CLI capability checklist" "type:spike,area:infra,phase:0,priority:medium" "Phase 0 — POC & Foundations" \
"$(ac '- [ ] core/plugin/theme/db export, search-replace --dry-run, option get all verified\n- [ ] Gaps documented')"

echo "== issues: Phase 1 =="
issue "feat(mu-plugins): register CPTs + taxonomies (events, sermons, ministries, staff, campuses, locations)" "type:feature,area:mu-plugins,phase:1,priority:high" "Phase 1 — Scaffolding, Content Model & Divi Design System" \
"$(ac '- [ ] CPTs + taxonomies registered in a versioned mu-plugin\n- [ ] Translatable-vs-shared fields defined\n- [ ] show_in_rest enabled')"
issue "feat(divi): Theme Builder skeleton (global header/footer + CPT templates)" "type:feature,area:divi,phase:1,priority:high" "Phase 1 — Scaffolding, Content Model & Divi Design System" \
"$(ac '- [ ] Global header/footer authored once\n- [ ] Archive + single templates per CPT\n- [ ] Renders EN content; no hardcoded strings')"
issue "feat(divi): centralize design tokens (Global Colors + module presets)" "type:feature,area:divi,phase:1,priority:medium" "Phase 1 — Scaffolding, Content Model & Divi Design System" \
"$(ac '- [ ] Global Colors defined\n- [ ] Core module presets defined\n- [ ] Pages reference tokens, not hardcoded styles')"
issue "feat(theme): initialize the Divi child theme" "type:feature,area:divi,phase:1,priority:medium" "Phase 1 — Scaffolding, Content Model & Divi Design System" \
"$(ac '- [ ] child-theme/ activated\n- [ ] functions.php scaffold\n- [ ] Custom code lives only here')"
issue "chore(infra): Composer-managed third-party plugins (wpackagist)" "type:chore,area:infra,phase:1,priority:low" "Phase 1 — Scaffolding, Content Model & Divi Design System" \
"$(ac '- [ ] composer.json manages third-party plugins where possible\n- [ ] Divi/premium documented as license-installed')"

echo "== issues: Phase 2 =="
issue "feat(console): scaffold React console on WP REST (Application Passwords auth)" "type:feature,area:console,phase:2,priority:high" "Phase 2 — Internal Admin Console" \
"$(ac '- [ ] React app scaffolded in console/\n- [ ] Auth to WP via Application Passwords\n- [ ] Reads content over REST')"
issue "feat(console): content/data editing + media swap for staff" "type:feature,area:console,phase:2,priority:high" "Phase 2 — Internal Admin Console" \
"$(ac '- [ ] Edit pages/CPT entries + swap media\n- [ ] Preview-before-publish\n- [ ] Audit log entry written\n- [ ] No layout building (stays in Divi)')"
issue "feat(console): Divi asset library browser (from tooling DB)" "type:feature,area:console,phase:2,priority:medium" "Phase 2 — Internal Admin Console" \
"$(ac '- [ ] Browse divi_assets from the tooling DB\n- [ ] View versions/metadata')"
issue "feat(console): translation review queue (Phase 3 hook)" "type:feature,area:console,phase:2,priority:low" "Phase 2 — Internal Admin Console" \
"$(ac '- [ ] Queue UI reads translation_drafts\n- [ ] Approve/edit stub wired for Phase 3')"

echo "== issues: Phase 3 =="
issue "chore(i18n): install UpdraftPlus on ES + full backups of both sites" "type:chore,area:i18n,phase:3,priority:high" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] UpdraftPlus installed on ES\n- [ ] Full DB+uploads backups of EN and ES stored off the orphaned host')"
issue "chore(divi): standardize Divi + Carousel versions across envs; inventory ASE" "type:chore,area:divi,phase:3,priority:high" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] Divi 4.27.4->4.27.7 and Carousel 3.0.6->3.2.1 aligned\n- [ ] ASE settings inventoried; keep/drop decided')"
issue "feat(i18n): install + configure Polylang Pro; establish EN<->ES pairs" "type:feature,area:i18n,phase:3,priority:high" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] Polylang Pro configured\n- [ ] EN<->ES translation pairs established for imported content')"
issue "feat(i18n): merge ES into English (WXR import + Divi-aware globals reconcile)" "type:feature,area:i18n,phase:3,risk:prod,priority:high" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] ES imported via WXR; media/authors/menus reconciled\n- [ ] Global Colors, presets, Theme Builder, et_pb_layout reconciled\n- [ ] Divi shortcode content renders post-import (staging)')"
issue "feat(i18n): /es/ URL structure + hreflang + 301 redirect map" "type:feature,area:i18n,phase:3,priority:medium" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] Spanish served at /es/\n- [ ] hreflang valid\n- [ ] iglesiavertical.com -> /es/ 301 map prepared (go-live at cutover)')"
issue "spike(i18n): validate Divi Theme Builder x Polylang" "type:spike,area:i18n,phase:3,priority:high" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] Documented behavior of Theme Builder template translation/assignment under Polylang\n- [ ] Go/no-go + workarounds')"
issue "feat(i18n): Azure OpenAI translation-draft service with field-level guard" "type:feature,area:i18n,phase:3,priority:medium" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] Azure OpenAI drafts EN<->ES into translation_drafts\n- [ ] Never overwrites human-edited fields (field guard)\n- [ ] Bilingual reviewer approves; approved text writes to ES post\n- [ ] Secrets in Azure Key Vault')"
issue "feat(i18n): merge validation pass-criteria script" "type:feature,area:i18n,phase:3,priority:medium" "Phase 3 — Consolidation & AI Translation" \
"$(ac '- [ ] Checks counts, broken media/links, pairs, menus, Theme Builder assignments, hreflang\n- [ ] Green on staging before cutover')"

echo "== issues: Phase 4 =="
issue "spike(infra): choose Azure WordPress hosting (App Service for Containers vs VM)" "type:spike,area:infra,phase:4,priority:high" "Phase 4 — Azure Host, Migrate & Cutover" \
"$(ac '- [ ] Decision memo comparing App Service for Containers vs VM\n- [ ] Cost estimate via Azure Pricing Calculator')"
issue "feat(infra): provision Azure WordPress + Redis object cache + raised upload limit" "type:feature,area:infra,phase:4,priority:high" "Phase 4 — Azure Host, Migrate & Cutover" \
"$(ac '- [ ] Azure WordPress provisioned (IaC preferred)\n- [ ] Redis object cache enabled\n- [ ] PHP upload limit raised well above 2M')"
issue "feat(infra): staging mirror + local->staging->prod promotion pipeline" "type:feature,area:infra,phase:4,priority:medium" "Phase 4 — Azure Host, Migrate & Cutover" \
"$(ac '- [ ] Staging mirrors prod\n- [ ] Promotion pipeline documented + working\n- [ ] DB migration scripts run per env')"
issue "feat(infra): production cutover runbook (DNS via GoDaddy) + rehearsed rollback" "type:feature,area:infra,phase:4,risk:prod,priority:high" "Phase 4 — Azure Host, Migrate & Cutover" \
"$(ac '- [ ] Runbook: final export, import to Azure, verify, DNS cutover, smoke tests\n- [ ] Rollback rehearsed (legacy droplet serves until DNS verified)\n- [ ] Production cutover executed')"

echo "== branch protection: main (ruleset) =="
# NOTE: On a FREE PRIVATE repo, GitHub blocks both classic branch protection AND
# rulesets (HTTP 403 "Upgrade to GitHub Pro or make this repository public").
# This ruleset applies automatically once the repo is PUBLIC or on GitHub Pro/Team.
# required_approving_review_count is 0 for a solo maintainer (enforces PR + CI +
# linear history without needing a second reviewer); bump to 1 when a collaborator joins.
if gh api -X POST "repos/$REPO/rulesets" --input - >/dev/null 2>&1 <<'JSON'
{
  "name": "main-protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "required_linear_history" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
    }},
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [ { "context": "Repo hygiene & docs" } ]
    }}
  ]
}
JSON
then
  echo "ruleset 'main-protection' applied"
else
  echo "SKIPPED: branch protection needs a PUBLIC repo or GitHub Pro/Team."
  echo "         Local stopgap: run 'git config core.hooksPath scripts/git-hooks' to block direct pushes to main."
fi

echo "Done."
