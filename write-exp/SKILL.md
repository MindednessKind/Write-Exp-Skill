---
name: write-exp
description: Writes pwntools exploit scripts in the user's local `Mypwn` style. Use when the user asks to write, adapt, or complete a pwn exploit, exploit skeleton, menu helper set, ret2libc/heap script, or shell-uploader flow that should follow `from Mypwn import *`, `init(...)`, wrapper helpers, and the user's preferred exploit board.
---

# Write Exp

Use this skill when the exploit should look like the user's normal `Mypwn` board, not a generic pwntools template.

## Quick Start

1. Read [references/mypwn-template.py](references/mypwn-template.py) before writing the exploit.
2. Keep the overall structure unless the user explicitly asks for a different style.
3. Fill in target-specific helpers completely. Do not leave `pass` in the final exploit.
4. If the local `Mypwn` implementation and the user's supplied board differ, follow the board or exploit style the user explicitly provided for the current task.

## Required Style

- Default to `from Mypwn import *`.
- Only keep `from libcfind import *` when the exploit actually needs leak-based libc identification.
- Preserve the config block pattern:
  - `FILE_NAME`
  - `LIBC_PATH`
  - `REMOTE_TARGET`
- Prefer `init(...)` as the main entry point when binary and target info are known.
- For single-connection exploits, default to `get_static_wrappers(io)`.
- Use `Tool.get_arch_packer(elf)` and `Tool.get_byte_packer()` instead of ad-hoc pack/unpack helpers.
- Use `get_log_function()` and `get_loglevel_function()` for logging helpers.
- Keep `dbg()` as `GDB()` plus `pause()` unless the exploit needs a custom attach flow.
- End with `shell()` unless the exploit clearly needs a custom post-exploit interaction.

## Workflow

### 1. Normalize the Skeleton

Start from the reference template and immediately align it to the challenge:

- Set `FILE_NAME` to the local binary or loader path.
- Set `LIBC_PATH` only if the libc is actually known.
- Keep the user's local-debug toggle style when the target may be switched:
  - `REMOTE_TARGET = "host:port"`
  - `REMOTE_TARGET = None`
- If the challenge directory already contains an existing `exp.py` in the user's preferred style, use that as the highest-priority structural reference.
- Remove unused imports and placeholder helper functions.

### 2. Match the Challenge Interface

Write thin helper functions that mirror the binary or service:

- Menu challenges: `cmd`, `add`, `edit`, `dele`, `show`, and similar wrappers.
- Structured protocols: dedicated send/recv helpers with exact prompts.
- Kernel or ioctl-style interfaces: thin syscall/ioctl/read/write wrappers named after the primitive.

Keep prompts and payloads in `bytes`. Use `itb()` for integer-to-bytes menu arguments.

### 3. Build the Exploit in Mypwn Style

- Parse leaks near the action that receives them.
- Keep symbol resolution, offsets, and ROP or heap targets grouped tightly.
- Use `logHex`, `log`, `info`, and `debug` instead of random `print()` calls.
- Add only short comments around non-obvious exploit transitions.

### 4. Finish Cleanly

Before returning the exploit:

- Remove `pass`, dead helpers, and unused scratch code.
- Ensure local and remote modes are both coherent.
- Keep the script runnable as a single file.
- Drop to `shell()` unless the script intentionally stops earlier.

## Libc Policy

- If `LIBC_PATH` is known, prefer it and avoid `libcfind`.
- If libc is unknown but there is a meaningful leak path, keep `libcfind` and resolve it from the leak.
- If libc is unknown and there is no leak yet, keep `LIBC_PATH = None` and write the current stage cleanly instead of inventing fake resolution logic.

## Upload and Kernel Note

If the challenge gives a shell and the exploit requires uploading a local ELF such as `./exp`, prefer the `Mypwn` uploader helpers already available in the toolkit. Keep upload logic separate from the vulnerability primitive so the exploit remains easy to iterate on.

## Output Expectations

- Produce a complete exploit, not a half-template.
- Stay close to the user's existing naming and board layout.
- Prefer concise, reusable helper functions over one-off inline send sequences.
- When the user shares an existing exploit draft, patch it in place instead of rewriting the whole structure unless the current layout is blocking progress.
