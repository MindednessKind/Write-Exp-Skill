---
title: unlink
date: 2026-04-01T16:42:06+08:00
lastmod: 2026-04-01T17:09:20+08:00
---

# unlink

依旧 unlink

到现在也没成功修复

‍

简单来说, unlink 操作就是将下一个 chunk 的 prev_inuse 位置空，再伪造 fd 和 bk 及 prev_size，使得当前指针在解链时被移动到原先的地址-0x18位置

‍

我们最主要需要绕过这几个检查

1. ```c
   if (__builtin_expect(FD->bk != P || BK->fd != P, 0))                
       malloc_printerr(check_action, "corrupted double-linked list", P, AV);
   ```
2. ```c
   if (__builtin_expect(chunksize(P) != prev_size(next_chunk(P)), 0))  
       malloc_printerr("corrupted size vs. prev_size");  
   ```
3. ```c
   if (!in_smallbin_range(chunksize_nomask(P)) &&                                
       __builtin_expect(P->fd_nextsize != NULL, 0)) {                            
       if (__builtin_expect(P->fd_nextsize->bk_nextsize != P, 0) ||              
           __builtin_expect(P->bk_nextsize->fd_nextsize != P, 0))                
           malloc_printerr(check_action, "corrupted double-linked list (not small)", P, AV);
   ```

‍

# 绕过

由于 `->bk`​ 的操作实际上是 `*(addr + 0x18)`​ , 而  `->fd` 同理

所以关于第一个检查，我们可以这样构造:

FD = &P - 0x18

BK = &P - 0x10

这样就能保证  `FD->bk == BK->fd == P`

‍

第二个检查也很简单，只需要在 edit 时完成一次 prev_size 的伪造即可

‍

至于第三个检查，我们只需要让我们的 fake_chunk 的大小在 small_bin 的范围内即可

‍

于是，我们进行 unlink 操作所需要进行的东西也就很明显了

‍

# 执行

‍

1. fake chunk 大小处于 smallbin 范围内
2. chunk2 的 prev_inuse 位为 0, 且大小不处于 fastbin 内
3. chunk2 的 prev_size 设置为 fake chunk 的大小
4. fake chunk 的 fd 与 bk 分别设置为 target-0x18 和 target-0x10

‍

从而让 target 被设置为 target-0x18

‍
