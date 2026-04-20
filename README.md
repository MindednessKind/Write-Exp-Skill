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

## Additional Skill

This repository also ships `write-wp/` as a separate skill directory.

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
- `Write-Exp-Skill/` and `write-exp/` are compatibility mirrors for installers that expect a nested skill directory.
- The `write-exp` implementation is deduplicated under `_shared/write-exp/`, and the root plus both compatibility directories point to that shared source.
