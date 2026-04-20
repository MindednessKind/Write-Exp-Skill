# Write Exp Skill

Minimal multi-skill repository for:

- `write-exp`: drafting and humanizing pwn exploit scripts in a local `Mypwn` style
- `write-wp`: writing Chinese CTF and pwn writeups in the user's personal note-derived style

## Install As Marketplace

If your installer supports Claude-style skill marketplaces, add this repository as a marketplace:

```bash
/plugin marketplace add MindednessKind/Write-Exp-Skill
```

## Repository Layout

- `.claude-plugin/marketplace.json` declares the marketplace plugin and the exported skills.
- `skills/write-exp/` is the `write-exp` skill.
- `skills/write-wp/` is the `write-wp` skill.
- The repository intentionally avoids compatibility mirrors, `_shared/`, and symlinks.
