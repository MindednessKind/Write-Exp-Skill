---
title: SROP
date: 2024-12-14T12:53:35+08:00
lastmod: 2025-10-19T17:35:23+08:00
---

# SROP

# 基本介绍

SROP，是一种利用 系统在内核态及用户态转换时 的机制，来伪造一个Signal Frame传入其中，从而让程序以规定的参数来运行想要运行的函数，也从而几乎完全控制了程序的执行流，也就能够达成目的了

# Signal机制

Signal机制是 类UNIX系统下，进程之间相互传递信息的一种方法。我们一般将其称为软中断信号(或软中断)。

例如，进程之间会通过 "Kill" 这个系统调用来发送软中断信号。

Signal机制 如图所示

![](https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/figure/ProcessOfSignalHandlering.png "引用自 https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/srop/#signal")

首先，内核会向某个进程发送一个 Signal机制，该进程将会暂时挂起，进入内核态

此时，内核会为该进程保存相应的上下文，将**所有的寄存器、Signal信息、指向Sigreturn的系统调用地址**全部压入栈中。此时，栈的结构如图所示。

> 需要注意的是，这一部分是存储在用户进程的地址空间中的

![](https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/figure/signal2-stack.png "引用自 https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/srop/#signal")

在此之后，执行流将会跳转至注册过的 Signal Handler 中来处理相应的 Signal；

Signal Handler 返回后，内核将执行 Sigreturn 系统调用，为进程恢复之前保存的上下文，最后再恢复进程的执行。

其中，32位的 Sitreturn 的调用号为 0x77 (119)，64位的调用号为 0xf (15)

对于不同架构而言，Signal Frame的结构也会有所不同，因而这里将给出 64位及32位相应的 sigcontext 以供参考。

64位

```c
struct _fpstate
{
  /* FPU environment matching the 64-bit FXSAVE layout.  */
  __uint16_t        cwd;
  __uint16_t        swd;
  __uint16_t        ftw;
  __uint16_t        fop;
  __uint64_t        rip;
  __uint64_t        rdp;
  __uint32_t        mxcsr;
  __uint32_t        mxcr_mask;
  struct _fpxreg    _st[8];
  struct _xmmreg    _xmm[16];
  __uint32_t        padding[24];
};

struct sigcontext
{
  __uint64_t r8;
  __uint64_t r9;
  __uint64_t r10;
  __uint64_t r11;
  __uint64_t r12;
  __uint64_t r13;
  __uint64_t r14;
  __uint64_t r15;
  __uint64_t rdi;
  __uint64_t rsi;
  __uint64_t rbp;
  __uint64_t rbx;
  __uint64_t rdx;
  __uint64_t rax;
  __uint64_t rcx;
  __uint64_t rsp;
  __uint64_t rip;
  __uint64_t eflags;
  unsigned short cs;
  unsigned short gs;
  unsigned short fs;
  unsigned short __pad0;
  __uint64_t err;
  __uint64_t trapno;
  __uint64_t oldmask;
  __uint64_t cr2;
  __extension__ union
    {
      struct _fpstate * fpstate;
      __uint64_t __fpstate_word;
    };
  __uint64_t __reserved1 [8];
};

```

32位

```c
struct sigcontext
{
  unsigned short gs, __gsh;
  unsigned short fs, __fsh;
  unsigned short es, __esh;
  unsigned short ds, __dsh;
  unsigned long edi;
  unsigned long esi;
  unsigned long ebp;
  unsigned long esp;
  unsigned long ebx;
  unsigned long edx;
  unsigned long ecx;
  unsigned long eax;
  unsigned long trapno;
  unsigned long err;
  unsigned long eip;
  unsigned short cs, __csh;
  unsigned long eflags;
  unsigned long esp_at_signal;
  unsigned short ss, __ssh;
  struct _fpstate * fpstate;
  unsigned long oldmask;
  unsigned long cr2;
};
```

# 攻击原理

Signal机制将会将所有的寄存器保存在栈中，包括 RIP， RDI，RSI，RDX，RAX。

如果我们能够将RIP指向 syscall，将 RAX写为我们想要执行的 系统调用号，再控制RDI等寄存器为设计的值，那么我们就能够完全的控制一次syscall，这样我们就能够在知晓 "/bin/sh\x00\"的地址、知晓Stack Frame的地址、知晓Syscall的地址、知晓Sigreturn的地址 的情况下，直接调用 execve(b'/bin/sh\\x00\',0,0);亦或其他系统调用

![](https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/figure/srop-example-1.png "引用自 https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/srop/#shell")

当然，我们也能够通过构造一个 Syscall Chain 实现 socket() -> bind() -> listen() 等一系列的执行链

‍

![](https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/figure/srop-example-2.png "引用自 https://ctf-wiki.org/pwn/linux/user-mode/stackoverflow/x86/advanced-rop/srop/#system-call-chains")

# 攻击实例

在实际解决这类考察SROP的CTF题目时，我们只需使用 pwntools 中的一整条链即可，我们需要的只是提供相应寄存器的值即可

Example：

```python
from pwn import *
sigframe = SigreturnFrame()
sigframe.rax = constants.SYS_read
sigframe.rdi = 0
sigframe.rsi = target
sigframe.rdx = 0x400
sigframe.rdi = syscall_ret_addr #这里如果没有下一条链，可以直接使用 syscall_addr
sigframe.rsp = Next_addr
# => 
#	read(0,target,0x400) ->(return to) Next_addr

```

‍

题目略

‍
