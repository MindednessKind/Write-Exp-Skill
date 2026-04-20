---
title: House of Orange
date: 2025-12-11T20:49:24+08:00
lastmod: 2025-12-12T20:40:42+08:00
---

# House of Orange

书接上文，这个时候我们已经获得了一个 Libc地址；接下来我们就是需要通过我们能够进行的操作getshell。

# 适用范围

glibc 2.23 - 2.26

没有 free，且可以进行 unsortedbin attack时

# 原理

我们首先需要明确一个glibc的机制

当你当前申请的chunk大小大于 top chunk 此时的大小时，会进行 sysmalloc()

这个时候，堆内存的分配会有两种分配方式，也就是 mmap 和 brk

这里如果以brk进行拓展，glibc会让原先的top chunk free掉，重新创建一个top chunk

这就是我们需要利用的点了

# 具体流程

### 1.sysmalloc

首先，我们通过一个 leak来覆盖到 top chunk 的 size 域，从而将size改小，实现brk扩展。

这个时候，我们需要让其满足以下条件:

1. top chunk 的 size 能让其对其内存页
2. size 大于 MINSIZE(0x10)
3. size 小于之后申请的 chunk_size + MINSIZE(0x10)
4. size 的 prev_inuse 位为1

从而让原先的 top chunk 执行 `_int_free` ，从而进入 unsortedbin 中

这样，我们也就得到了一个 unsortedbin 大小的 free chunk，且其fd及bk指向main_arena

### leak libc

这时候，我们就能够申请一个较小的chunk，从而切割 free chunk，得到内存中残留的 fd,bk值

从而也就 leak libc 了

### hijack _IO_list_all

这时候，我们进行一次 unsortedbin attack，将 _IO_list_all劫持下来。

> 关于这里的 Unsortedbin Attack
>
> 1. 通过溢界写将 bk 修改为 _IO_list_all-0x10
> 2. ‍

# 适用范围

glibc 2.23 - 2.26

没有 free，且可以进行 unsortedbin attack时

# 原理

我们需要知道以下原理：

1. 在malloc chunk发现 unsortedbin 中的 size 与所申请的大小不匹配时，会让

# 具体流程
