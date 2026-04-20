---
title: Top Chunk
date: 2025-01-10T20:43:18+08:00
lastmod: 2025-04-06T21:07:53+08:00
---

# Top Chunk

Glibc 中对于 Top Chunk 的描述如下

```sh
/*
   Top

    The top-most available chunk (i.e., the one bordering the end of
    available memory) is treated specially. It is never included in
    any bin, is used only if no other chunk is available, and is
    released back to the system if it is very large (see
    M_TRIM_THRESHOLD).  Because top initially
    points to its own bin with initial zero size, thus forcing
    extension on the first malloc request, we avoid having any special
    code in malloc to check whether it even exists yet. But we still
    need to do so when getting memory from system, so we make
    initial_top treat the bin as a legal but unusable chunk during the
    interval between initialization and the first call to
    sysmalloc. (This is somewhat delicate, since it relies on
    the 2 preceding words to be zero during this interval as well.)
 */

/* Conveniently, the unsorted bin can be used as dummy top on first call */
#define initial_top(M) (unsorted_chunks(M))
```

程序在第一次进行 malloc 时， Heap 会被分成两块，一块给用户 ，另一块分配给 Top Chunk。

其实，所谓的 Top Chunk 就是处于当前堆的物理地址最高的 `chunk`。

这个 `chunk` 不属于任何一个 Bin，它的作用在于当所有的 Bin 都无法满足用户请求的大小时，如果其大小不小于指定的大小，则进行分配操作，并将剩下的部分作为新的 Top Chunk。

但如果其大小大于指定的大小，程序会对 Heap 进行扩展后，再进行分配。

在 Main Arena 中通过 sbrk 扩展 Heap 段，在 Thread Arena 中通过 mmap 分配新的 Heap。

‍

需要注意的是， Top Chunk 的 prev_inuse 位始终为 1，否则其前方的 `chunk` 会被合并到 Top Chunk 中。

‍

**在初始情况下，我们可以将 Unsorted Chunk 作为 Top Chunk。**

‍
