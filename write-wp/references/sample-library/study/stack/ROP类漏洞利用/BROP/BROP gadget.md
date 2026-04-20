---
title: BROP gadget
date: 2024-12-14T12:54:26+08:00
lastmod: 2024-12-14T12:59:22+08:00
---

# BROP gadget

​`BROP gadget` 一般被认为是六个连续的 pop chain ，在最后接续上一个ret指令。

即：

```x86asm
pop rbx
pop rbp

pop r12

pop r13

pop r14

pop r15

ret
```

因而我们为了得到**BROP gadget**，我们一般会进行一下栈帧构建：

​`ret_addr + (crash_addr) * 6 + stop_gadget`

通过这种栈帧构建，我们可以获得该种 `BROP gadget`

（ 如果想要得到 `pop rdi ; ret`​，将`BROP gadget`​的地址**偏移**加9 即可 ）

‍
