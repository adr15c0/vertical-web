# Planning Prompt: Church Website Consolidation and Modernization

Paste into Claude Code with planning mode on. Fill in every `[BRACKET]` before sending.
Anything you leave blank, the plan will guess at, and the guesses will be wrong.

---

## Role and mode

You are planning a WordPress consolidation and modernization project. Do not write
implementation code in this session. Produce a plan I can review, revise, and then
execute with you in stages.

Before proposing anything, inspect what is actually in this repository and in the
local WordPress environment. Ask me questions where the plan depends on facts you
cannot observe. Where you make an assumption, label it as an assumption.

## Context

We run a church website that currently exists as two separately maintained WordPress
installations, one English and one Spanish. Both are hosted and maintained manually.
Every content change, template change, and feature request has to be implemented twice.
Spanish content is hand-written by a person and intentionally diverges from the English
in places, so this is not a machine translation problem.

- English site: `https://goverticalchurch.com/`, approximately `44` pages, `42` posts
- Spanish site: `https://iglesiavertical.com/`, approximately `5` pages, `0` posts
- Current host: `DigitalOcean droplet at root@142.93.118.14, nginx, both sites on same server, no CDN`, SSH access: `NO`, WP-CLI available: `UNCONFIRMED`
- Current WordPress version: `7.0.2`
- Current theme(s): `Divi`
- Active plugins: `Divi, Supreme Modules for Divi, Wow Carousel for Divi Lite, Akismet, Google Site Kit`
- Existing analytics, forms, giving, or streaming integrations: `Google Analytics + GTM, YouTube embeds, Planning Center Church Center`

Editing is done by me and possibly one other technical person, not by non-technical
volunteers. Optimize for version control, reproducibility, and a real deploy pipeline
over drag-and-drop ease of use, but do not make routine content edits require a
developer.

There is an existing internal system called Vertical DB that holds church operational
data sourced from `[Planning Center / OTHER]`. It exposes `[REST / GraphQL / none yet]`.
Details: `Vertical DB is built on PostgreSQL and hosted on Azure, consider leveraging the same stack for this web backend for later horizontal integration.`.

## Decisions already made

These are settled. Do not re-litigate them, but do flag it if you find a hard technical
blocker.

1. Stay on WordPress. Do not propose a migration off the platform.
2. Consolidate into a single WordPress installation. Do not propose Multisite.
3. Use a multilingual plugin layer, Polylang or WPML, that links English and Spanish
   posts as translation pairs while allowing the content to differ.
4. The site skeleton, meaning header, footer, navigation, and page templates, must be
   authored once and shared across both languages.
5. Theme and custom plugin code live in Git. WordPress core, third-party plugins,
   uploads, and the database do not.
6. Development happens against a local environment seeded from production data. No
   direct editing of production.

## What I want you to plan

### 1. Content model

Propose a set of custom post types and taxonomies that replace free-form pages for
recurring content. At minimum consider events, sermons, ministries, staff, campuses,
and locations. For each, specify the fields, which fields are translatable versus
shared across languages, and the archive and single templates required.

Recommend how to register this. I am inclined toward a versioned mu-plugin rather than
clicking it into an admin UI. Tell me if you disagree and why.

### 2. Multilingual layer

Compare Polylang Pro and WPML for this specific case. Cover translation pair linkage,
handling of custom post types and custom fields, menu and widget translation, media
handling, the language switcher, URL structure options, REST API behavior, and known
migration paths from two separate installs. Give a recommendation with reasoning, not
a feature table alone.

Recommend a URL structure for Spanish, subdirectory versus subdomain versus separate
domain, and explain the SEO and migration consequences of each. Cover hreflang.

### 3. Theme architecture

Propose a block theme structure with `theme.json`, template parts, and custom block
patterns. Identify where custom blocks are genuinely needed versus where core blocks
plus patterns will do. Define the design token strategy in `theme.json` so styling is
centralized. State explicitly how the theme stays language-agnostic.

### 4. Vertical DB integration

Design the integration that makes Vertical DB the source of truth for operational data
such as service times, event schedules, and ministry rosters, with WordPress as a
rendering surface. Cover the fetch layer, caching strategy including transients and
object cache, scheduled refresh, failure and stale-data behavior, how the data is
exposed to templates and blocks, and how language selection is handled for data that
originates outside WordPress. Address authentication and secret storage.

### 5. Local environment and data pull

Specify the local setup. Compare wp-env, Local, and DDEV for this project and pick one.
Then give the exact procedure to pull production down, covering database export, the
`wp search-replace` invocation including the serialized-data concern, uploads handling
including a strategy for a large media library, and how to refresh local from
production later without redoing setup.

### 6. Migration and merge

Plan the one-time merge of the Spanish site into the canonical install. Decide which
install becomes canonical and justify it. Cover WXR export and import, media
attachment reconciliation, user and author mapping, establishing translation pairs
after import, menu reconstruction, and validation checks with specific pass criteria.

Produce a redirect map strategy and specify when redirects go live relative to the
cutover. Include a rollback plan and the exact backup taken immediately beforehand.

### 7. Deployment pipeline

Define the Git repository layout, branching model, the local to staging to production
promotion path, and the CI workflow. Cover how third-party plugins are managed, whether
via Composer or the host, how database changes are handled since they do not travel
through Git, and what the release checklist looks like in both languages.

### 8. Sequencing

Break the work into phases that each end in something reviewable and reversible. For
each phase give the objective, the tasks, the dependencies, the risks, and the
definition of done. Identify which phases can run in parallel. Flag every point where
production is at risk.

### 9. Open questions and costs

List what you cannot determine without more information from me. Separately, list the
things that cost money, including plugin licenses, hosting, and any services, and tell
me to verify current pricing myself rather than stating figures you are not sure of.

## Constraints on your output

- Write the plan to `docs/plan/` as numbered markdown files, one per section above,
  plus an `00-overview.md` that summarizes and links them.
- Where a decision has more than one defensible answer, present the alternatives and
  make a recommendation. Do not silently pick one.
- Prefer boring, well-supported approaches over clever ones. This site will be
  maintained by very few people for a long time.
- Call out anything in my stated decisions that you think is a mistake.
- Do not write implementation code in this session. Interfaces and file layouts are
  fine. Working code is not.
- Ask me your questions before writing the plan files, not after.
