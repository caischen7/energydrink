# Installed skills — provenance & maintenance

A **curated set of 22 skills** lives under `.claude/skills/`, chosen for this
repo's frontend / marketing landing-page work. One skill (`add-ion-colorway`)
is authored in this repo; the other 21 are vendored from three public sources
and committed here so they persist (this environment is ephemeral — only
committed files survive).

> [!CAUTION]
> The `anthropics/skills` set is official. `alirezarezvani/claude-skills` and
> `antigravity-awesome-skills` are **community, unverified** (`risk: unknown`).
> Skills are instructions an agent may auto-load based on their `description`;
> review one before relying on it and treat bundled scripts as untrusted code.

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
