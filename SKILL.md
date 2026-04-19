---
name: write-exp
description: Writes human-looking pwn exploit scripts in the user's local `Mypwn` style. Use when the user asks to write, adapt, humanize, or complete an exploit, exploit skeleton, menu helper set, ret2libc/heap script, shell-uploader flow, or other pwntools exploit that should match the user's actual `Mypwn` board instead of a generic template.
---

# Write Exp

Use this skill when the exploit should read like the user's normal hand-written `Mypwn` board, not a polished reusable framework.

## Quick Start

1. Look for an existing `exp.py`, old board, or nearby exploit in the same challenge folder before doing anything else.
2. If the user shared a board or an old exploit, follow that first and treat [references/mypwn-template.py](references/mypwn-template.py) as a fallback.
3. Patch an existing exploit in place when possible instead of rewriting from scratch.
4. Keep the final script target-specific and slightly rigid if that matches the user's style, but make sure the exploit still works.

## Required Style

- Default to `from Mypwn import *`.
- Add explicit `from pwn import args, process, remote` only when the script actually uses them. Do not assume `Mypwn` re-exports every pwntools symbol.
- Add `from libcfind import *` only when the exploit actually resolves an unknown libc from a real leak. Do not add it by default.
- Keep the config block shape centered on:
  - `FILE_NAME`
  - `LIBC_PATH`
  - `REMOTE_TARGET`
- Add optional knobs only when the target needs them, such as `IS_SSL`, `SNI_HOST`, `LOCAL_ARGV`, or a GDB `src` snippet.
- Call `init(...)` to set up `elf`, `libc`, `GDB`, and syscall helpers. Do not assume `init(...)` returns `io`, `elf`, or wrappers.
- Prefer `iopen(...)` when it can launch the target cleanly, because it injects `io`, `s`, `sl`, `sa`, `sla`, `rcv`, `rcu`, and `shell` into globals.
- For TLS remotes, prefer `iopen(..., ssl=True, sni=host)` or `iopen(..., ssl=True, sni=SNI_HOST)` when SNI matters. Keep `IsSSL=True` only when patching an older board that already uses the compatibility spelling.
- If a custom local launcher is needed, such as `ld-linux`, a wrapper script, or unusual argv, start it manually and bind thin wrappers with a short local `bind()` helper that also exposes `shell = lambda: io.interactive()`.
- For shell-based remote targets, prefer `prepare_shell(...)`, `upload(...)`, `execute(...)`, `execute_and_wait(...)`, and `upload_and_run(...)` from `Mypwn` before writing an ad-hoc base64 uploader.
- Use `Tool.get_arch_packer(elf)` and `Tool.get_byte_packer()` instead of ad-hoc pack/unpack helpers.
- Use `get_log_function()` for logging. Match the user's local naming, commonly `logHex, lg, info, debug`.
- Keep `dbg()` as `GDB(io)` plus `pause()`, or `GDB(io, scripts=src)` when the board already carries a local GDB script string.
- End with `shell()` only when the exploit is meant to stay interactive. If the exploit prints the flag and exits by design, stop there. If a manual launcher branch does not bind `shell`, call `io.interactive()` directly instead of relying on a stub.

## Workflow

### 1. Normalize the Skeleton

Start from the reference template and align it to the target immediately:

- First scan the current challenge directory for an existing `exp.py`, `solve.py`, or nearby sibling exploit and reuse that structure when it matches the user's style.
- Set `FILE_NAME` to the real binary, loader entry, or `None` if the exploit is purely remote.
- Set `LIBC_PATH` only when the libc is actually known and useful.
- Preserve the user's remote toggle style:
  - `REMOTE_TARGET = "host:port"`
  - `REMOTE_TARGET = None`
- If the challenge already contains an `exp.py` in the user's style, use it as the highest-priority structural reference.
- Remove placeholder helpers, dead imports, and template noise that the exploit does not need.

### 2. Match the Challenge Interface

Write thin helpers that mirror the real target:

- Menu binaries: `cmd`, `add`, `edit`, `dele`, `show`, and similar wrappers.
- Line-oriented services: small `start`, `bind`, `sendline`, or `recvuntil` helpers that match the prompts exactly.
- Shell uploader or kernel helpers: short wrappers named after the primitive, not a generic framework layer. Reuse `prepare_shell(...)` and the uploader helpers before writing a custom uploader.

Keep prompts and payloads in `bytes`. Use `itb()` for numeric menu arguments when that fits the board.

### 3. Build the Exploit in the User's Mypwn Style

- Parse leaks close to where they are received.
- Keep offsets, gadgets, fake chunks, and ROP setup grouped near the exploit step that uses them.
- Prefer short comments only around the non-obvious transitions.
- Avoid over-abstracting. The exploit should look like it was written for this target, not prepared as a reusable library.
- Keep retries, CLI parsing, or extra configurability only when the exploit genuinely needs them.
- For shell targets, only keep custom upload code when `Mypwn.uploader` genuinely cannot handle the environment.
- Do not force `upload_and_run(...)` when the target's post-exec behavior is unusual. If output collection is target-specific, use `upload(...)` for transport and then drive execution and reads manually.

### 4. Finish Cleanly

Before returning the exploit:

- Remove `pass`, `NotImplementedError`, unused helper stubs, and scratch code.
- Make sure local and remote branches are both coherent.
- Ensure SSL handling, custom loaders, and prompt sync match the actual target.
- Keep the script runnable as a single file unless the challenge already depends on a helper binary or build step.
- Run a real verification when practical. A human-looking exploit still needs to exploit successfully.

## Libc Policy

- If `LIBC_PATH` is known, prefer it and avoid `libcfind`.
- If libc is unknown but there is a meaningful leak path, add `from libcfind import *` and resolve it from the leak close to where the leak is parsed.
- If libc is unknown and there is no leak yet, keep `LIBC_PATH = None` and write the current stage cleanly instead of inventing fake resolution logic.

Minimal pattern:

```python
from libcfind import *

puts_addr = unpk(rcu(b"\x7f", drop=False)[-6:])
db = LibcSearcher("puts", puts_addr)
libc.address = puts_addr - db.symbols["puts"]
```

## Launcher and Remote Notes

- For SSL services, prefer `iopen(..., ssl=True)` and add `sni=host` when the endpoint expects SNI. Keep `IsSSL=True` only for compatibility with older boards.
- If `iopen` is not flexible enough for that target, fall back to `remote(host, port, ssl=True, sni=host)` with the smallest possible wrapper layer.
- If you must keep an older `init(..., target=..., IsBomb=False)` board layout, `ssl=True` also works on that legacy path. Prefer the split `init(...)` plus `iopen(...)` shape for fresh scripts.
- For local runs that need a loader such as `./ld-linux-x86-64.so.2`, use `process([...])` and then bind wrappers manually, including a real `shell` helper.
- For shell upload challenges, prefer this flow:
  - `prepare_shell(io, expect=..., timeout=..., disable_echo=...)`
  - `upload(...)`, `execute(...)`, `execute_and_wait(...)`, or `upload_and_run(...)` depending on how the target behaves after exec
- Prefer this decision order:
  - If the binary returns cleanly to the same shell, `execute_and_wait(...)` is a good fit.
  - If the exploit only needs fire-and-forget execution and then custom parsing, use `upload(...)` plus `execute(...)` and read manually.
  - If upload and immediate exec are enough and no special post-processing is needed, use `upload_and_run(...)`.
- `prepare_shell(...)` can take either a prompt token or a callable `expect` function. Use the callable form for odd shells that need custom prompt synchronization.
- For terminals that emit cursor-position queries such as `\x1b[6n`, prefer `terminal_reply=make_terminal_reply()` or a custom reply map before writing target-specific recv hacks.
- Keep shell upload logic separate from the memory-corruption primitive so iteration stays easy.
- If a remote shell needs special decoders, custom probes, or setup commands, use the uploader module knobs first before writing a one-off uploader.
- Prefer direct decoder commands such as `base64 -d`, `gzip -d -c`, or `openssl base64 -d -A` when you override uploader behavior. Do not switch to `busybox ...` decoder wrappers unless the user explicitly asks for that environment.

## Output Expectations

- Produce a complete exploit, not a half-template.
- Stay close to the user's current naming and board layout.
- Prefer concise target-shaped helpers over framework-like abstraction.
- When the user asks to "humanize" an exploit, preserve the exploit path but remove the obviously over-engineered structure.
- When the exploit depends on uploading a local helper, prefer the shared uploader helpers unless the target proves they are insufficient.
