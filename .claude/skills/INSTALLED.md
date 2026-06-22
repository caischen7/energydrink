# Installed skills — provenance & maintenance

A **curated set of 23 skills** lives under `.claude/skills/`, chosen for this
repo's frontend / marketing landing-page work. One skill (`add-ion-colorway`)
is authored in this repo; the other 22 are vendored from four public sources
and committed here so they persist (this environment is ephemeral — only
committed files survive).

> [!CAUTION]
> The `anthropics/skills` set is official. `alirezarezvani/claude-skills`,
> `antigravity-awesome-skills`, and `ipeirotis/cloud-bootstrap` are **community,
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
