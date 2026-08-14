# Installed skills — provenance & maintenance

A **set of 55 skills** lives under `.claude/skills/`, chosen for this
repo's frontend / marketing landing-page work. One skill (`add-ion-colorway`)
is authored in this repo; the other 54 are vendored from six public sources
and committed here so they persist (this environment is ephemeral — only
committed files survive).

> [!CAUTION]
> The `anthropics/skills` set is official. `alirezarezvani/claude-skills`,
> `antigravity-awesome-skills`, `spjoshis/claude-code-plugins`,
> `nimrodfisher/data-analytics-skills` and
> `ipeirotis/cloud-bootstrap` are **community,
> unverified** (`risk: unknown`). Skills are instructions an agent may auto-load
> based on their `description`; review one before relying on it and treat bundled
> scripts as untrusted code. **`cloud-bootstrap` handles cloud credentials and
> bundles `install.sh`/`update.sh` — review before use; never commit unencrypted
> credentials.**

## Repo-authored (1)

- **add-ion-colorway** — add/edit a colorway on the ION 3D can (synchronized
  edits across `src/can.js`, `index.html`, `src/fx.js`).

## anthropics/skills — official — `5754626` (7)

- frontend-design, web-artifacts-builder, theme-factory, canvas-design,
  algorithmic-art, webapp-testing, skill-creator

## alirezarezvani/claude-skills — community — `4a3c05b` (13)

- senior-frontend, ui-design-system, design-system, landing-page-generator,
  a11y-audit, performance-profiler, seo-audit, schema-markup, site-architecture,
  copywriting, form-cro, page-cro, full-page-screenshot

## antigravity-awesome-skills — community — `943cecf` (1)

- frontend-ui-dark-ts (the single skill explicitly requested; React/Tailwind/
  Framer Motion — not directly used by this vanilla three.js site)

## spjoshis/claude-code-plugins — community — `ddcf16e` (1)

- **data-visualization** — chart-selection guide, dashboard layout principles and
  data-storytelling practice. Guidance text only: a single `SKILL.md`, no scripts
  and no network calls (checked before installing).

  Requested as `npx skillfish add spjoshis/claude-code-plugins data-visualization`.
  skillfish could not fetch it — this environment's `GITHUB_TOKEN` returns 401 and
  the unauthenticated GitHub API was rate-limited — so the repo was cloned directly
  and the one file copied in. Note the skill lives at
  `plugins/data-analyst/skills/data-visualization/`, nested inside a plugin rather
  than at the top level.

## nimrodfisher/data-analytics-skills — community — `8849884` (31)

The full set, requested for the energy-drink analysis work. Six categories:

- **Data quality / validation** — data-quality-audit, programmatic-eda, query-validation,
  metric-reconciliation, schema-mapper
- **Documentation** — analysis-assumptions-log, analysis-documentation, data-catalog-entry,
  semantic-model-builder, sql-to-business-logic
- **Analysis** — ab-test-analysis, business-metrics-calculator, cohort-analysis,
  funnel-analysis, root-cause-investigation, segmentation-analysis, time-series-analysis
- **Storytelling** — dashboard-specification, data-narrative-builder,
  executive-summary-generator, insight-synthesis, visualization-builder
- **Stakeholder comms** — analysis-qa-checklist, impact-quantification, methodology-explainer,
  stakeholder-requirements-gathering, technical-to-business-translator
- **Workflow** — analysis-planning, analysis-retrospective, context-packager, peer-review-template

> [!WARNING]
> These bundle **69 Python scripts** — far more executable code than any other vendored
> set here. A keyword scan flagged network/exec/secret strings in `context-packager` and
> `schema-mapper`. Nothing has been executed: the two skills used so far
> (`data-quality-audit`, `analysis-assumptions-log`) were applied by following their
> written method, not by running their CLIs. Review any script before running it.

`metric-reconciliation` and `schema-mapper` appear twice in the source repo (categories 01
and 02); the first copy of each was taken.

## ipeirotis/cloud-bootstrap — community — `f8984b7` (1)

- **cloud-bootstrap** (v1.4.0) — manages encrypted cloud-provider credentials
  (GCP / AWS / Azure) committed to the repo so they **persist across Claude Code
  sessions**; triggers on "set up cloud credentials", cloud-auth failures (401/403),
  or detecting `.cloud-config.json` / `.cloud-credentials.*.enc`. Directly relevant
  here: it's the mechanism that would let a future session authenticate to GCP and
  run `./deploy.sh` without the manual Cloud Shell step. Vendored whole (incl.
  `references/`, `workflows/`, `install.sh`, `update.sh`). Handles secrets — see the
  CAUTION above.

## Notes

- A much larger set was briefly installed, then curated down to the above.
  Symlinks were dereferenced (`cp -L`) so nothing dangling is committed.
- On name collisions the more authoritative source won (repo > antigravity >
  anthropics > alirezarezvani).

## Add more / uninstall

```bash
# remove one skill
rm -rf .claude/skills/<name>

# remove all vendored skills, keep the repo-authored one
find .claude/skills -maxdepth 1 -mindepth 1 -type d ! -name add-ion-colorway -exec rm -rf {} +
```

To add more later, re-clone a source repo and copy the desired
`<skill>/SKILL.md` (plus any `scripts/`, `references/`, `assets/`) into
`.claude/skills/<name>/`.
