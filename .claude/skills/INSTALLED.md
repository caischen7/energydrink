# Installed skills — provenance & maintenance

This directory was populated by request on 2026-06-18. It contains
**345 skill directories**, each a `<name>/SKILL.md` (some with supporting
`scripts/`, `references/`, `assets/`). Of these, **`add-ion-colorway` is
authored in this repo**; the rest are vendored from three public sources.

> [!CAUTION]
> The `anthropics/skills` set is official. The other two are **community,
> unverified** content (`risk: unknown` in their frontmatter). Skills are
> instructions an agent may auto-load based on their `description`. Review a
> skill before relying on it, and treat bundled scripts as untrusted code.

## Sources

| Source | Ref | Installed | Notes |
| --- | --- | --- | --- |
| [anthropics/skills](https://github.com/anthropics/skills) | `5754626` | official set | pdf, docx, xlsx, pptx, mcp-builder, webapp-testing, etc. |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | `4a3c05b` | community collection | canonical skills under team folders; `.gemini/skills` symlinks were dereferenced |
| [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills/tree/main/skills/frontend-ui-dark-ts) | `943cecf` | `frontend-ui-dark-ts` only | the single skill explicitly requested |

**Dedup policy:** installed in the order above; on a name collision the
earlier (more authoritative) skill wins and the later one is skipped. Symlinks
were dereferenced (`cp -L`) so nothing dangling is committed.

## Repo-authored skill

- **`add-ion-colorway`** — how to add/edit a colorway on the ION 3D can
  (synchronized edits across `src/can.js`, `index.html`, `src/fx.js`).

## Update / uninstall

```bash
# remove a single skill
rm -rf .claude/skills/<name>

# remove ALL vendored skills but keep the repo-authored one
find .claude/skills -maxdepth 1 -mindepth 1 -type d ! -name add-ion-colorway -exec rm -rf {} +

# revert the whole install (before it's merged): drop the commit
git revert <commit>   # or: git reset --hard HEAD~1 on this branch
```

## Official skills installed (from anthropics/skills)

- algorithmic-art
- brand-guidelines
- canvas-design
- claude-api
- doc-coauthoring
- docx
- frontend-design
- internal-comms
- mcp-builder
- pdf
- pptx
- skill-creator
- slack-gif-creator
- theme-factory
- web-artifacts-builder
- webapp-testing
- xlsx
