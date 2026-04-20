---
title: Last Remainder Chunk
date: 2025-04-06T21:08:26+08:00
lastmod: 2025-04-06T21:14:58+08:00
---

# Last Remainder Chunk

在用户使用 Malloc 请求分配内存时， Ptmalloc2 找到的 `chunk` 可能并不和申请的内存大小一致，这时候就将分割之后的剩余部分称为 Last Remainder Chunk。

Unsorted Bin 中也会有这一个切割后的剩余部分。

解释：

	分配给其他Chunk时对后剩下的
