---
title: malloc_state
date: 2024-12-21T22:45:53+08:00
lastmod: 2025-04-23T00:51:58+08:00
---

# malloc_state

# 简述

这个结构用于管理堆块，用来记录每一个 Arena 当前申请的内存的具体状态，例如当前Arena是否存在空闲Chunk，存在什么大小的空闲Chunk等。

无论是 Main_arena 还是 Thread_arena，它们都只会有一个 Malloc_State 结构。

由于 Thread 的 Arena 可能拥有多个，因而 Malloc_State 会存在在最新申请的 Arena中。

‍

**注意： Main_Arena 中的 Malloc_State 并不是 Heap Segment 的一部分，而是一个全局变量，它存储在 Libc.so的数据段中**

‍

# 完整定义

```c
struct malloc_state {
    /* Serialize access.  */
    __libc_lock_define(, mutex);

    /* Flags (formerly in max_fast).  */
    int flags;

    /* Fastbins */
    mfastbinptr fastbinsY[ NFASTBINS ];

    /* Base of the topmost chunk -- not otherwise kept in a bin */
    mchunkptr top;

    /* The remainder from the most recent split of a small request */
    mchunkptr last_remainder;

    /* Normal bins packed as described above */
    mchunkptr bins[ NBINS * 2 - 2 ];

    /* Bitmap of bins, help to speed up the process of determinating if a given bin is definitely empty.*/
    unsigned int binmap[ BINMAPSIZE ];

    /* Linked list, points to the next arena */
    struct malloc_state *next;

    /* Linked list for free arenas.  Access to this field is serialized
       by free_list_lock in arena.c.  */
    struct malloc_state *next_free;

    /* Number of threads attached to this arena.  0 if the arena is on
       the free list.  Access to this field is serialized by
       free_list_lock in arena.c.  */
    INTERNAL_SIZE_T attached_threads;

    /* Memory allocated from the system in this arena.  */
    INTERNAL_SIZE_T system_mem;
    INTERNAL_SIZE_T max_system_mem;
};
```

- __libc_lock_define(, mutex);

  - 这个变量是用于控制程序串行访问同一个分配区的。当一个线程获取分配区后，其他线程想要访问该分配区，便必须等待该线程分配完成后方才可以使用。 (上🔒)
- flags

  - 它记录了分配区的一些标志，如 bit0 记录分配区是否存在 `fast_bin_chunk`，bit1标识着分配区是否能够返回一个连续的虚拟地址空间。

    具体如下
  - ```sh
    /*
       FASTCHUNKS_BIT held in max_fast indicates that there are probably
       some fastbin chunks. It is set true on entering a chunk into any
       fastbin, and cleared only in malloc_consolidate.
       The truth value is inverted so that have_fastchunks will be true
       upon startup (since statics are zero-filled), simplifying
       initialization checks.
     */

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
    ```
- fastbinsY[ NFASTBINS ]

  - 用于存放每个 `fast bin`链表头部的指针
- top

  - 其指向分配区的 Top_Chunk
- last_remainder

  - 指向最新`Chunk`分割后剩下的部分
- bins[ NBINS * 2 - 2 ]

  - 用于存储 `Unsorted Bin`​、`Small Bins`​以及`Large Bins`的链表
- binmap

  - ptmalloc 使用 Bitmap 来标识哪些 bin 中是非空的
- *next 

  - 指向Arena链表中的下一个节点
- \*next\_free

  - 用于管理 (未被线程占用的) Arena
  - 其被 `free_list_lock` 保护，仅在 Arena 未被使用时方才出现在链表中
- attached\_threads

  - 记录当前有多少个线程正使用该 Arena (若为0，则说明该Arena未被任何线程使用，可以进入Free List链表中)
- system\_mem

  - 记录该Arena从系统申请的内存总量 (包括了未分配出去的部分)
- max\_system\_mem

  - 记录历史上从系统申请的最大内存值

> ChatGPT Said:
>
> 	
>
> ## 总结一句话版本：
>
> 这个结构体代表了一个 **内存分配“arena”**  的内部状态。多个线程可以拥有各自的 arena，从而减小锁竞争。内部包含快速分配机制（fastbins）、正常分配机制（bins/top）、多线程支持（锁、线程计数）、以及从系统请求的内存记录等。

‍
