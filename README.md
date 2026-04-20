# Write Exp Skill

Codex skill repository for:

- `write-exp`: drafting and humanizing pwn exploit scripts in a local `Mypwn` style
- `write-wp`: writing Chinese CTF and pwn writeups in the user's personal note-derived style

## Install

Clone this repo directly into your Codex skills directory:

```bash
git clone https://github.com/MindednessKind/Write-Exp-Skill.git "${CODEX_HOME:-$HOME/.codex}/skills/write-exp"
```

Restart Codex after cloning.

### Register as Marketplace

If your installer supports Claude-style skill marketplaces, add this repository as a marketplace:

```bash
/plugin marketplace add MindednessKind/Write-Exp-Skill
```

## Additional Skill

This repository also ships `write-wp/` as a separate skill directory.
For installers such as `cc-switch` that prefer a nested compatibility directory, `Write-WP-Skill/` mirrors the same skill.

To install it from this checkout:

```bash
cp -a write-wp "${CODEX_HOME:-$HOME/.codex}/skills/write-wp"
```

If you prefer to keep it linked to this repository:

```bash
ln -s "$(pwd)/write-wp" "${CODEX_HOME:-$HOME/.codex}/skills/write-wp"
```

## Update

Pull the latest changes in place:

```bash
git -C "${CODEX_HOME:-$HOME/.codex}/skills/write-exp" pull --ff-only
```

Restart Codex after updating.

## Repository Layout

- The repository root remains the canonical install target for `write-exp`.
- `write-wp/` is a standalone sibling skill with its own references and sample library.
- `Write-WP-Skill/` is the compatibility mirror for `write-wp/`.
- `Write-Exp-Skill/` and `write-exp/` are compatibility mirrors for installers that expect a nested skill directory.
- `skills/write-exp/` and `skills/write-wp/` are marketplace-facing physical copies for multi-skill scanners.
- The `write-exp` canonical source lives under `_shared/write-exp/`.
- The `write-wp` canonical source lives under `_shared/write-wp/`.
- The install-facing directories are all physical files and directories; this repository intentionally avoids symlinks because some installers do not follow them.

## Sync Mirrors

To refresh the physical compatibility copies from `_shared/`, run:

```bash
python scripts/sync_skill_copies.py
```

This updates:

- root `write-exp` files
- `write-exp/`
- `Write-Exp-Skill/`
- `skills/write-exp/`
- `write-wp/`
- `Write-WP-Skill/`
- `skills/write-wp/`
