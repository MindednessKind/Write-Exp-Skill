---
title: Malloc指令
date: 2024-12-13T17:40:22+08:00
lastmod: 2024-12-19T22:50:42+08:00
tags:
  - 'heap'
  - 'knowledge'
---

# Malloc指令

‍

通过分析((20241215230734-mxqhuhw "Glibc-malloc指令"))可以得到实际的实现操作：

	malloc指令会返回指向**对应大小字节的内存块**的指针

在一些异常情况下，会进行特殊的处理：

- 满足`n=0`时，malloc函数会返回当前系统所允许的堆的最小的内存块
- 满足`n<0`​ 即n为负数时， 程序会申请极大的内存空间<sup>（原因： size_t 是一个 无符号数 ）</sup>，但通常来说都会申请失败，原因是系统无法调度出足够的内存给其堆块

‍

<span data-type="text" style="background-color: var(--b3-card-info-background); color: var(--b3-card-info-color);">即 即使你申请</span>**0字节**<span data-type="text" style="background-color: var(--b3-card-info-background); color: var(--b3-card-info-color);">的内存，</span>`malloc`​<span data-type="text" style="background-color: var(--b3-card-info-background); color: var(--b3-card-info-color);">依然会分配一个最小的chunk。</span>

‍
