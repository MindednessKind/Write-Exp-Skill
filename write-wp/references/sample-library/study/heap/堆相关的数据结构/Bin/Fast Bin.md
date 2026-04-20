---
title: Fast Bin
date: 2025-04-05T19:40:40+08:00
lastmod: 2025-04-05T22:36:36+08:00
---

# Fast Bin

# 概述

大多数程序，会经常申请以及释放一些比较小的内存块。

如果我们将一些较小的 `chunk`​ 释放，随后发现存在与之相邻的 空闲的 `chunk`​ ，对其进行合并，那么在下一次申请相应大小的 `chunk`​ 时，我们就需要对 `chunk` 进行分割，着就大大降低了堆的利用效率。

**因为我们将大部分时间花在了合并、分割及检查的过程中。**

因此，ptmalloc设计了 FastBin应对当前场景。 其对应的变量是 Malloc_State 中的 fastbinY

```c
/*
   Fastbins

    An array of lists holding recently freed small chunks.  Fastbins
    are not doubly linked.  It is faster to single-link them, and
    since chunks are never removed from the middles of these lists,
    double linking is not necessary. Also, unlike regular bins, they
    are not even processed in FIFO order (they use faster LIFO) since
    ordering doesn't much matter in the transient contexts in which
    fastbins are normally used.

    Chunks in fastbins keep their inuse bit set, so they cannot
    be consolidated with other free chunks. malloc_consolidate
    releases all chunks in fastbins and consolidates them with
    other free chunks.
 */
typedef struct malloc_chunk *mfastbinptr;

/*
    This is in malloc_state.
    /* Fastbins */
    mfastbinptr fastbinsY[ NFASTBINS ];
*/
```

为了更好的、更高效的使用 FastBin，glibc 采用了单向链表，对其涵盖的每个 Bin 进行组织，并**每个Bin都采用LIFO规则<sup>（最近释放的 chunk 会被更早的分配， 这样会更加适合于局部性）</sup>**。

也就是说，当用户需要的 `chunk`​ 大小小于 FastBin 的最大大小时， ptmalloc 将会优先判断 FastBin 中相应的 Bin 中是否有对应大小的空闲块，如果有，则直接从这个bin中获取其 `chunk`。

如果没有，ptmalloc 才会进行接下来的一系列的操作。

‍

在默认情况下 (这里以32位系统为例) ， FastBin 中 默认支持最大的 `chunk`​ 的数据空间大小为 64字节，但其可以支持的 `chunk` 的数据空间最大为 80字节。

除此之外， FastBin 最多可以支持的 Bin 的个数为 10个，从数据空间为 8字节 开始，一直到 80字节 (注意，这里说的是数据空间大小，即除去了 prev_size 及 size 字段部分的大小)

定义如下

```c
#define NFASTBINS (fastbin_index(request2size(MAX_FAST_SIZE)) + 1)

#ifndef DEFAULT_MXFAST
#define DEFAULT_MXFAST (64 * SIZE_SZ / 4)
#endif

/* The maximum fastbin request size we support */
#define MAX_FAST_SIZE (80 * SIZE_SZ / 4)

/*
   Since the lowest 2 bits in max_fast don't matter in size comparisons,
   they are used as flags.
 */

/*
   FASTCHUNKS_BIT held in max_fast indicates that there are probably
   some fastbin chunks. It is set true on entering a chunk into any
   fastbin, and cleared only in malloc_consolidate.

   The truth value is inverted so that have_fastchunks will be true
   upon startup (since statics are zero-filled), simplifying
   initialization checks.
 */
//判断分配区是否有 fast bin chunk，1表示没有
#define FASTCHUNKS_BIT (1U)

#define have_fastchunks(M) (((M)->flags & FASTCHUNKS_BIT) == 0)
#define clear_fastchunks(M) catomic_or(&(M)->flags, FASTCHUNKS_BIT)
#define set_fastchunks(M) catomic_and(&(M)->flags, ~FASTCHUNKS_BIT)

/*
   NONCONTIGUOUS_BIT indicates that MORECORE does not return contiguous
   regions.  Otherwise, contiguity is exploited in merging together,
   when possible, results from consecutive MORECORE calls.

   The initial value comes from MORECORE_CONTIGUOUS, but is
   changed dynamically if mmap is ever used as an sbrk substitute.
 */
// MORECORE是否返回连续的内存区域。
// 主分配区中的MORECORE其实为sbr()，默认返回连续虚拟地址空间
// 非主分配区使用mmap()分配大块虚拟内存，然后进行切分来模拟主分配区的行为
// 而默认情况下mmap映射区域是不保证虚拟地址空间连续的，所以非主分配区默认分配非连续虚拟地址空间。
#define NONCONTIGUOUS_BIT (2U)

#define contiguous(M) (((M)->flags & NONCONTIGUOUS_BIT) == 0)
#define noncontiguous(M) (((M)->flags & NONCONTIGUOUS_BIT) != 0)
#define set_noncontiguous(M) ((M)->flags |= NONCONTIGUOUS_BIT)
#define set_contiguous(M) ((M)->flags &= ~NONCONTIGUOUS_BIT)

/* ARENA_CORRUPTION_BIT is set if a memory corruption was detected on the
   arena.  Such an arena is no longer used to allocate chunks.  Chunks
   allocated in that arena before detecting corruption are not freed.  */

#define ARENA_CORRUPTION_BIT (4U)

#define arena_is_corrupt(A) (((A)->flags & ARENA_CORRUPTION_BIT))
#define set_arena_corrupt(A) ((A)->flags |= ARENA_CORRUPTION_BIT)

/*
   Set value of max_fast.
   Use impossibly small value if 0.
   Precondition: there are no existing fastbin chunks.
   Setting the value clears fastchunk bit but preserves noncontiguous bit.
 */

#define set_max_fast(s)                                                        \
    global_max_fast =                                                          \
        (((s) == 0) ? SMALLBIN_WIDTH : ((s + SIZE_SZ) & ~MALLOC_ALIGN_MASK))
#define get_max_fast() global_max_fast
```

ptmalloc 默认情况下会调用 set_max_fast(s)，将全局变量 global_max_fast 设置为 DEFAULT_MXFAST ，也就是设置 FastBin 中 `chunk` 的最大值。

当 MAX_FAST_SIZE 被设置为0时，系统不会支持 FastBin。

‍

# FastBin 的索引

```c
#define fastbin(ar_ptr, idx) ((ar_ptr)->fastbinsY[ idx ])

/* offset 2 to use otherwise unindexable first 2 bins */
// chunk size=2*size_sz*(2+idx)
// 这里要减2，否则的话，前两个bin没有办法索引到。
#define fastbin_index(sz)                                                      \
    ((((unsigned int) (sz)) >> (SIZE_SZ == 8 ? 4 : 3)) - 2)
```

​**需要特别注意的是，fastbin 范围的** **​`chunk`​**​ **的 inuse 始终会被设置为 1。**

**因此它们不会和其他被释放的** **​`chunk`​**​ **合并。**

‍

当释放的 `chunk`​ 与该 `chunk`​ 相邻的空闲 `chunk`​ 合并后的大小大于 FASTBIN_CONSOLIDATION_THRESHOLD 时，这时内存碎片可能比较多了，我们需要将 FastBin 中的 `chunk` 全部进行合并，以减少内存碎片对于系统的影响。

```c
/*
   FASTBIN_CONSOLIDATION_THRESHOLD is the size of a chunk in free()
   that triggers automatic consolidation of possibly-surrounding
   fastbin chunks. This is a heuristic, so the exact value should not
   matter too much. It is defined at half the default trim threshold as a
   compromise heuristic to only attempt consolidation if it is likely
   to lead to trimming. However, it is not dynamically tunable, since
   consolidation reduces fragmentation surrounding large chunks even
   if trimming is not used.
 */

#define FASTBIN_CONSOLIDATION_THRESHOLD (65536UL)
```

‍

**malloc_consolidate 函数可以将 FastBin 中的所有能与其他**  ****  **​`chunk`​**​ **合并的** **​`chunk`​**​ **合并在一起。**

**具体的实现方法参见后续的详细 函数分析。**

```c
/*
    Chunks in fastbins keep their inuse bit set, so they cannot
    be consolidated with other free chunks. malloc_consolidate
    releases all chunks in fastbins and consolidates them with
    other free chunks.
 */
```

‍
