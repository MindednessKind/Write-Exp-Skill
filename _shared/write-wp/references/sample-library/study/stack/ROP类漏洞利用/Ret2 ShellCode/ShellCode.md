---
title: ShellCode
date: 2025-01-21T10:57:00+08:00
lastmod: 2025-01-21T11:20:44+08:00
---

# ShellCode

Source Code 经过 Compiler 后会成为一套Machine Code<sup>(一系列OPCode的组合)</sup>，汇编语言与Machine Code是一一对应的。

我们构建ShellCode时实际是在写汇编语言，后转换为机器码。

我们ShellCode一般有两种，一种是获取Shell，一种是通过orw绕过部分沙箱实现目的

- ==execve==
- int execve( const char *pathname, char *const argv[], char *const envp[] )
- Spawn a shell

  - execve( "/bin/sh\", NULL, NULL )
- rax = execve_syscall_number<sup>(x86 0x0b x64 0x3b)</sup>
- rdi = address of "/bin/sh\"
- rsi = 0x0
- rdx = 0x0

‍
