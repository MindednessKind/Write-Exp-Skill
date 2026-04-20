---
title: heap_info
date: 2024-12-21T22:45:24+08:00
lastmod: 2025-04-23T00:24:30+08:00
---

# heap_info

# 简述

在程序刚开始执行的时候，每个线程都是不存在 Heap区域的。 当当前线程申请内存时，就需要一个结构来记录对应的信息，此时，Heap_info结构应运而生。

当该Heap的资源被耗尽后，就需要再次申请内存。

此外，一般申请的 Heap 在物理内存上 是不连续的， 因此我们需要记录不同Heap之间的链接结构。

‍

**该数据结构是特意为了 从&lt;Memory Mapping Segment&gt;处申请的内存而准备的，即 为非主线程所准备的。**

‍

主线程可以通过 sbrk()函数 扩展 Program Break Location 获得 (直到申请至使用完全，触及 **&lt;Memory Mapping Segment&gt;** )，主线程仅拥有一个Heap，不存在 Heap_info 结构。

‍

‍

# 完整定义

```c
#define HEAP_MIN_SIZE (32 * 1024)
#ifndef HEAP_MAX_SIZE
# ifdef DEFAULT_MMAP_THRESHOLD_MAX
#  define HEAP_MAX_SIZE (2 * DEFAULT_MMAP_THRESHOLD_MAX)
# else
#  define HEAP_MAX_SIZE (1024 * 1024) /* must be a power of two */
# endif
#endif

/* HEAP_MIN_SIZE and HEAP_MAX_SIZE limit the size of mmap()ed heaps
   that are dynamically created for multi-threaded programs.  The
   maximum size must be a power of two, for fast determination of
   which heap belongs to a chunk.  It should be much larger than the
   mmap threshold, so that requests with a size just below that
   threshold can be fulfilled without creating too many heaps.  */

/***************************************************************************/

/* A heap is a single contiguous memory region holding (coalesceable)
   malloc_chunks.  It is allocated with mmap() and always starts at an
   address aligned to HEAP_MAX_SIZE.  */

typedef struct _heap_info
{
  mstate ar_ptr; /* Arena for this heap. */
  struct _heap_info *prev; /* Previous heap. */
  size_t size;   /* Current size in bytes. */
  size_t mprotect_size; /* Size in bytes that has been mprotected
                           PROT_READ|PROT_WRITE.  */
  /* Make sure the following data is properly aligned, particularly
     that sizeof (heap_info) + 2 * SIZE_SZ is a multiple of
     MALLOC_ALIGNMENT. */
  char pad[-6 * SIZE_SZ & MALLOC_ALIGN_MASK];
} heap_info;
```

这个结构主要描述了堆的基本信息，包括了:

- 堆所对应的 Arena 地址
- 如果一个线程使用的堆占满，则必须再次申请。 因而一个线程可能具有多个堆结构。

  prev 记录着上一个 Heap_info 的地址。 这里可以发现，堆的Heap_info 是通过一个单向链表所链接的。
- Size 表示当前堆的大小
- 最后一个部分是保证内存空间对齐。 (即 pad[...] )

> Q:  为何 `pad` 的空间大小存在 "-6" ?
>
> A:  `pad`​是为了确保分配的空间是按照 `MALLOC_ALIGN_MASK +1`​(又被记为 `MALLOC_ALIGN_MASK_1`​ )对齐的。  在`pad`​之前，该结构体一共存在6个 `SIZE_SZ`​ 大小的成员，为了确保 `MALLOC_ALIGN_MASK_1`​ 字节的对其，我们可能会需要进行 `pad`​ ，因而我们不妨假设 该结构体的最终大小为`MALLOC_ALIGN_MASK_1 + X`​，其中`X`​为自然数。那么，需要`pad`​的空间即为`MALLOC_ALIGN_MASK_1 * X  -  6 * SIZE_SZ`​ -> `(MALLOC_ALIGN_MASK_1 * x  -  6 * SIZE_SZ) % MALLOC_ALIGN_MASK_1`​ -> `0  -  6 * SIZE_SZ % MALLOC_ALIGN_MASK_1`​ -> `-6 * SIZE_SZ % MALLOC_ALIGN_MASK_1`​ -> `-6 * SIZE_SZ & MALLOC_ALIGN_MASK`  因此, pad的空间如此表示

到现在为止，这个结构看起来是相当重要的，但若是我们看完 Malloc 的实现后，会发现其出现的频率实际并不高。
