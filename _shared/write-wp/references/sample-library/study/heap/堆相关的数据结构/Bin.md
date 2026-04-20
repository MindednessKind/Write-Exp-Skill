---
title: Bin
date: 2025-04-05T13:02:20+08:00
lastmod: 2025-04-05T22:34:58+08:00
---

# Bin

# [概述](Bin/概述.md)

> 我们曾说过，用户释放掉的 `chunk` 并不会马上归还给系统， ptmalloc 会统一管理 heap 以及 mmap 映射区域中的空闲的 chunk。
>
> 当用户再一次请求分配内存时，ptmalloc 分配器会试图在空闲的 `chunk` 中挑选一块合适的分配给用户。 这样的操作能够避免平凡的系统调用，以降低内存分配的开销。
>
> 我们在具体的实现中，ptmalloc 采用分箱式方法堆空闲的 `chunk` 进行管理。
>
> 首先，它会根据空闲的 `chunk`​ 的大小以及使用状态，将`chunk`初步分为4类：
>
> - Fast Bin
> - Small Bin
> - Large Bin
> - Unsorted Bin
>
> 对于每一类又有更细的划分，相似大小的 `chunk` 会用双向链表连接起来。
>
> 也就是说，在每类 Bin 的内部仍然会有多个互不相关的链表来保存不同大小的 chunk。
>
> 对于 Small Bin、Large Bin、Unsorted Bin 来说，ptmalloc 会将它们维护在同一个数组之中。
>
> 这些 Bin 对应的数据结构在 Malloc_state 中，如下
>
> ```c
> #define NBINS 128
> /* Normal bins packed as described above */
> mchunkptr bins[ NBINS * 2 - 2 ];
> ```
>
> ​`Bins` 主要是用于索引不同的 Bin 的 fd 以及 bk。
>
> 为了简化双向链表的使用，每个 Bin 的header都被设置为 malloc_chunk 类型。 这样可以避免 header 类型以及其特殊处理。
>
> 但为了节省空间以及提高局限性，我们只会分配 Bin 的 fd/bk 指针，然后再使用 respositioning tricks 将这些指针视为一个 `malloc_chunk*` 的字段。
>
> 这里我们以 32位系统为例子， Bin 的前四项含义如下
>
> |含义|bin1 的 fd/bin2 的 prev\_size|bin1 的 bk/bin2 的 size|bin2 的 fd/bin3 的 prev\_size|bin2 的 bk/bin3 的 size|
> | --------| ----------------------------| -----------------------| ----------------------------| -----------------------|
> |bin 下标|0|1|2|3|
>
> 我们可以看到，bin2 的 prev_size、size 以及 bin1 的 fd、bk 是重合的。
>
> 由于我们只会使用 fd 和 bk 来索引链表，所以该重合部分的数据其实记录的是 bin1 的 fd、bk 。也就是说，虽然 bin2 和 bin1 共用部分数据，但是记录的仍然是前一个 bin 的链表数据。
>
> 通过这样的数据复用，程序可以节省部分内存空间。
>
> 在 数组中的 Bin 以此如下
>
> 1. 第一个为 『Unsorted Bin』。正如其名，存在此处的 `chunk`​ 没有进行排序，存储的 `chunk` 比较杂乱。
> 2. 索引从 2 至 63 的 Bin 被称为 『Small Bin』。同一个 Small Bin 链表中的 `chunk` 的大小相同。
>
>    两个相邻索引的 Small Bin 链表中的 `chunk`​ 大小相差的字节数为 **2机器字长** ，即32位相差 8字节，64位相差 16字节。
> 3. Small Bin 之后的 Bin 被称作 『Large Bin』。Large Bin 中的每一个 Bin 都包含一定范围内的 `chunk`​ ，其中的 `chunk` 按 fd指针 的顺序从大到小排列。
>
>    相同大小的 `chunk` 同样按照最近使用的顺序排列。
>
> 此外，上述这些 Bin 的排布都会遵循一个原则：   **任意两个物理相邻的** **空闲**​**​`chunk`​**​ **的使用标记总是被置位的，因而上述原则在 两个物理相邻的空闲**​**​`chunk`​**​ **上无效**
>
> # Bin 的通用宏
>
> ```c
> typedef struct malloc_chunk *mbinptr;
>
> /* addressing -- note that bin_at(0) does not exist */
> #define bin_at(m, i)                                                           \
>     (mbinptr)(((char *) &((m)->bins[ ((i) -1) * 2 ])) -                        \
>               offsetof(struct malloc_chunk, fd))
>
> /* analog of ++bin */
> //获取下一个bin的地址
> #define next_bin(b) ((mbinptr)((char *) (b) + (sizeof(mchunkptr) << 1)))
>
> /* Reminders about list directionality within bins */
> // 这两个宏可以用来遍历bin
> // 获取 bin 的位于链表头的 chunk
> #define first(b) ((b)->fd)
> // 获取 bin 的位于链表尾的 chunk
> #define last(b) ((b)->bk)
> ```

# [Fast Bin](Bin/Fast%20Bin.md)

> # 概述
>
> 大多数程序，会经常申请以及释放一些比较小的内存块。
>
> 如果我们将一些较小的 `chunk`​ 释放，随后发现存在与之相邻的 空闲的 `chunk`​ ，对其进行合并，那么在下一次申请相应大小的 `chunk`​ 时，我们就需要对 `chunk` 进行分割，着就大大降低了堆的利用效率。
>
> **因为我们将大部分时间花在了合并、分割及检查的过程中。**
>
> 因此，ptmalloc设计了 FastBin应对当前场景。 其对应的变量是 Malloc_State 中的 fastbinY
>
> ```c
> /*
>    Fastbins
>
>     An array of lists holding recently freed small chunks.  Fastbins
>     are not doubly linked.  It is faster to single-link them, and
>     since chunks are never removed from the middles of these lists,
>     double linking is not necessary. Also, unlike regular bins, they
>     are not even processed in FIFO order (they use faster LIFO) since
>     ordering doesn't much matter in the transient contexts in which
>     fastbins are normally used.
>
>     Chunks in fastbins keep their inuse bit set, so they cannot
>     be consolidated with other free chunks. malloc_consolidate
>     releases all chunks in fastbins and consolidates them with
>     other free chunks.
>  */
> typedef struct malloc_chunk *mfastbinptr;
>
> /*
>     This is in malloc_state.
>     /* Fastbins */
>     mfastbinptr fastbinsY[ NFASTBINS ];
> */
> ```
>
> 为了更好的、更高效的使用 FastBin，glibc 采用了单向链表，对其涵盖的每个 Bin 进行组织，并**每个Bin都采用LIFO规则<sup>（最近释放的 chunk 会被更早的分配， 这样会更加适合于局部性）</sup>**。
>
> 也就是说，当用户需要的 `chunk`​ 大小小于 FastBin 的最大大小时， ptmalloc 将会优先判断 FastBin 中相应的 Bin 中是否有对应大小的空闲块，如果有，则直接从这个bin中获取其 `chunk`。
>
> 如果没有，ptmalloc 才会进行接下来的一系列的操作。
>
> 在默认情况下 (这里以32位系统为例) ， FastBin 中 默认支持最大的 `chunk`​ 的数据空间大小为 64字节，但其可以支持的 `chunk` 的数据空间最大为 80字节。
>
> 除此之外， FastBin 最多可以支持的 Bin 的个数为 10个，从数据空间为 8字节 开始，一直到 80字节 (注意，这里说的是数据空间大小，即除去了 prev_size 及 size 字段部分的大小)
>
> 定义如下
>
> ```c
> #define NFASTBINS (fastbin_index(request2size(MAX_FAST_SIZE)) + 1)
>
> #ifndef DEFAULT_MXFAST
> #define DEFAULT_MXFAST (64 * SIZE_SZ / 4)
> #endif
>
> /* The maximum fastbin request size we support */
> #define MAX_FAST_SIZE (80 * SIZE_SZ / 4)
>
> /*
>    Since the lowest 2 bits in max_fast don't matter in size comparisons,
>    they are used as flags.
>  */
>
> /*
>    FASTCHUNKS_BIT held in max_fast indicates that there are probably
>    some fastbin chunks. It is set true on entering a chunk into any
>    fastbin, and cleared only in malloc_consolidate.
>
>    The truth value is inverted so that have_fastchunks will be true
>    upon startup (since statics are zero-filled), simplifying
>    initialization checks.
>  */
> //判断分配区是否有 fast bin chunk，1表示没有
> #define FASTCHUNKS_BIT (1U)
>
> #define have_fastchunks(M) (((M)->flags & FASTCHUNKS_BIT) == 0)
> #define clear_fastchunks(M) catomic_or(&(M)->flags, FASTCHUNKS_BIT)
> #define set_fastchunks(M) catomic_and(&(M)->flags, ~FASTCHUNKS_BIT)
>
> /*
>    NONCONTIGUOUS_BIT indicates that MORECORE does not return contiguous
>    regions.  Otherwise, contiguity is exploited in merging together,
>    when possible, results from consecutive MORECORE calls.
>
>    The initial value comes from MORECORE_CONTIGUOUS, but is
>    changed dynamically if mmap is ever used as an sbrk substitute.
>  */
> // MORECORE是否返回连续的内存区域。
> // 主分配区中的MORECORE其实为sbr()，默认返回连续虚拟地址空间
> // 非主分配区使用mmap()分配大块虚拟内存，然后进行切分来模拟主分配区的行为
> // 而默认情况下mmap映射区域是不保证虚拟地址空间连续的，所以非主分配区默认分配非连续虚拟地址空间。
> #define NONCONTIGUOUS_BIT (2U)
>
> #define contiguous(M) (((M)->flags & NONCONTIGUOUS_BIT) == 0)
> #define noncontiguous(M) (((M)->flags & NONCONTIGUOUS_BIT) != 0)
> #define set_noncontiguous(M) ((M)->flags |= NONCONTIGUOUS_BIT)
> #define set_contiguous(M) ((M)->flags &= ~NONCONTIGUOUS_BIT)
>
> /* ARENA_CORRUPTION_BIT is set if a memory corruption was detected on the
>    arena.  Such an arena is no longer used to allocate chunks.  Chunks
>    allocated in that arena before detecting corruption are not freed.  */
>
> #define ARENA_CORRUPTION_BIT (4U)
>
> #define arena_is_corrupt(A) (((A)->flags & ARENA_CORRUPTION_BIT))
> #define set_arena_corrupt(A) ((A)->flags |= ARENA_CORRUPTION_BIT)
>
> /*
>    Set value of max_fast.
>    Use impossibly small value if 0.
>    Precondition: there are no existing fastbin chunks.
>    Setting the value clears fastchunk bit but preserves noncontiguous bit.
>  */
>
> #define set_max_fast(s)                                                        \
>     global_max_fast =                                                          \
>         (((s) == 0) ? SMALLBIN_WIDTH : ((s + SIZE_SZ) & ~MALLOC_ALIGN_MASK))
> #define get_max_fast() global_max_fast
> ```
>
> ptmalloc 默认情况下会调用 set_max_fast(s)，将全局变量 global_max_fast 设置为 DEFAULT_MXFAST ，也就是设置 FastBin 中 `chunk` 的最大值。
>
> 当 MAX_FAST_SIZE 被设置为0时，系统不会支持 FastBin。
>
> # FastBin 的索引
>
> ```c
> #define fastbin(ar_ptr, idx) ((ar_ptr)->fastbinsY[ idx ])
>
> /* offset 2 to use otherwise unindexable first 2 bins */
> // chunk size=2*size_sz*(2+idx)
> // 这里要减2，否则的话，前两个bin没有办法索引到。
> #define fastbin_index(sz)                                                      \
>     ((((unsigned int) (sz)) >> (SIZE_SZ == 8 ? 4 : 3)) - 2)
> ```
>
> ​**需要特别注意的是，fastbin 范围的** **​`chunk`​**​ **的 inuse 始终会被设置为 1。**
>
> **因此它们不会和其他被释放的** **​`chunk`​**​ **合并。**
>
> 当释放的 `chunk`​ 与该 `chunk`​ 相邻的空闲 `chunk`​ 合并后的大小大于 FASTBIN_CONSOLIDATION_THRESHOLD 时，这时内存碎片可能比较多了，我们需要将 FastBin 中的 `chunk` 全部进行合并，以减少内存碎片对于系统的影响。
>
> ```c
> /*
>    FASTBIN_CONSOLIDATION_THRESHOLD is the size of a chunk in free()
>    that triggers automatic consolidation of possibly-surrounding
>    fastbin chunks. This is a heuristic, so the exact value should not
>    matter too much. It is defined at half the default trim threshold as a
>    compromise heuristic to only attempt consolidation if it is likely
>    to lead to trimming. However, it is not dynamically tunable, since
>    consolidation reduces fragmentation surrounding large chunks even
>    if trimming is not used.
>  */
>
> #define FASTBIN_CONSOLIDATION_THRESHOLD (65536UL)
> ```
>
> **malloc_consolidate 函数可以将 FastBin 中的所有能与其他**  ****  **​`chunk`​**​ **合并的** **​`chunk`​**​ **合并在一起。**
>
> **具体的实现方法参见后续的详细 函数分析。**
>
> ```c
> /*
>     Chunks in fastbins keep their inuse bit set, so they cannot
>     be consolidated with other free chunks. malloc_consolidate
>     releases all chunks in fastbins and consolidates them with
>     other free chunks.
>  */
> ```

# [Small Bin](Bin/Small%20Bin.md)

> Small Bin 中每个 `chunk` 的大小与其所在的 Bin 的 Index 的关系为:
>
> Chunk_Size = 2 * SIZE_SZ * Index
>
> 具体如下
>
> |下标|SIZE\_SZ\=4（32 位）|SIZE\_SZ\=8（64 位）|
> | ----| ------------------| ------------------|
> |2|16|32|
> |3|24|48|
> |4|32|64|
> |5|40|80|
> |x|2\*4\*x|2\*8\*x|
> |63|504|1008|
>
> Small Bin 中一共有 62个循环双向链表，每个链表中存储的`chunk` 大小都一致。
>
> 比如对于 32位的系统而言，下表2所对应的双向链表中存储的 `chunk` 大小均为 16字节 。
>
> 每个链表都拥有链表头节点，这样方便于对链表内部节点的管理。
>
> 特别的，**Small Bin 中每个 Bin 对应的链表都采用** **FIFO规则**，所以同一个链表中先被释放的 `chunk` 会先被分配出去。
>
> Small Bin 相关的宏如下
>
> ```c
> #define NSMALLBINS 64
> #define SMALLBIN_WIDTH MALLOC_ALIGNMENT
> // 是否需要对small bin的下标进行纠正
> #define SMALLBIN_CORRECTION (MALLOC_ALIGNMENT > 2 * SIZE_SZ)
>
> #define MIN_LARGE_SIZE ((NSMALLBINS - SMALLBIN_CORRECTION) * SMALLBIN_WIDTH)
> //判断chunk的大小是否在small bin范围内
> #define in_smallbin_range(sz)                                                  \
>     ((unsigned long) (sz) < (unsigned long) MIN_LARGE_SIZE)
> // 根据chunk的大小得到small bin对应的索引。
> #define smallbin_index(sz)                                                     \
>     ((SMALLBIN_WIDTH == 16 ? (((unsigned) (sz)) >> 4)                          \
>                            : (((unsigned) (sz)) >> 3)) +                       \
>      SMALLBIN_CORRECTION)
> ```
>
> **或许大家会疑惑，那 Small Bin 是否与 FastBin 中的** **​`chunk`​**​ **的大小会有大部分的重合？ 那么 Small Bin 中对应大小的 Bin 是否是没有太大的作用？**
>
> 其实不然， FastBin 中的 `chunk` 是有可能被放到 Small Bin 中去的，在我们后面分析具体的源码时，会有更深刻的理解。

‍

# [Large Bin](Bin/Large%20Bin.md)

> Large Bin 中一共包括 63个 Bin，每个 Bin 中的 `chunk` 的大小不是一致，而是处于一定区间范围内。
>
> 此外，这 63个 Bin 被分为了 6组，每组 Bin 中的 `chunk` 大小之间的公差一致
>
> 具体如下:
>
> |组|数量|公差|
> | --| ----| -------|
> |1|32|64B|
> |2|16|512B|
> |3|8|4096B|
> |4|4|32768B|
> |5|2|262144B|
> |6|1|不限制|
>
> 这里我们以 32位平台的 Large Bin 为例，第一个 Large Bin 的起始 `chunk`​ 大小为 512字节，位于第一组，所以该 Bin 可以存储的 `chunk` 的大小范围为 [512,512+64) 。
>
> 关于 Large Bin 的宏如下
>
> ```c
> #define largebin_index_32(sz)                                                  \
>     (((((unsigned long) (sz)) >> 6) <= 38)                                     \
>          ? 56 + (((unsigned long) (sz)) >> 6)                                  \
>          : ((((unsigned long) (sz)) >> 9) <= 20)                               \
>                ? 91 + (((unsigned long) (sz)) >> 9)                            \
>                : ((((unsigned long) (sz)) >> 12) <= 10)                        \
>                      ? 110 + (((unsigned long) (sz)) >> 12)                    \
>                      : ((((unsigned long) (sz)) >> 15) <= 4)                   \
>                            ? 119 + (((unsigned long) (sz)) >> 15)              \
>                            : ((((unsigned long) (sz)) >> 18) <= 2)             \
>                                  ? 124 + (((unsigned long) (sz)) >> 18)        \
>                                  : 126)
>
> #define largebin_index_32_big(sz)                                              \
>     (((((unsigned long) (sz)) >> 6) <= 45)                                     \
>          ? 49 + (((unsigned long) (sz)) >> 6)                                  \
>          : ((((unsigned long) (sz)) >> 9) <= 20)                               \
>                ? 91 + (((unsigned long) (sz)) >> 9)                            \
>                : ((((unsigned long) (sz)) >> 12) <= 10)                        \
>                      ? 110 + (((unsigned long) (sz)) >> 12)                    \
>                      : ((((unsigned long) (sz)) >> 15) <= 4)                   \
>                            ? 119 + (((unsigned long) (sz)) >> 15)              \
>                            : ((((unsigned long) (sz)) >> 18) <= 2)             \
>                                  ? 124 + (((unsigned long) (sz)) >> 18)        \
>                                  : 126)
>
> // XXX It remains to be seen whether it is good to keep the widths of
> // XXX the buckets the same or whether it should be scaled by a factor
> // XXX of two as well.
> #define largebin_index_64(sz)                                                  \
>     (((((unsigned long) (sz)) >> 6) <= 48)                                     \
>          ? 48 + (((unsigned long) (sz)) >> 6)                                  \
>          : ((((unsigned long) (sz)) >> 9) <= 20)                               \
>                ? 91 + (((unsigned long) (sz)) >> 9)                            \
>                : ((((unsigned long) (sz)) >> 12) <= 10)                        \
>                      ? 110 + (((unsigned long) (sz)) >> 12)                    \
>                      : ((((unsigned long) (sz)) >> 15) <= 4)                   \
>                            ? 119 + (((unsigned long) (sz)) >> 15)              \
>                            : ((((unsigned long) (sz)) >> 18) <= 2)             \
>                                  ? 124 + (((unsigned long) (sz)) >> 18)        \
>                                  : 126)
>
> #define largebin_index(sz)                                                     \
>     (SIZE_SZ == 8 ? largebin_index_64(sz) : MALLOC_ALIGNMENT == 16             \
>                                                 ? largebin_index_32_big(sz)    \
>                                                 : largebin_index_32(sz))
> ```
>
> 这里我们以 32位平台下，第一个 Large Bin 的起始 `chunk` 大小为例，其大小为 512字节，那么进行计算:  512>>6 == 8 ，所以其下标为 56 + ( 512 >> 6 ) == 64 。

‍

# [Unsorted Bin](Bin/Unsorted%20Bin.md)

> Unsorted Bin 可以视为空闲 `chunk` 回归其所属 Bin 之前的缓冲区。
>
> 其在 Glibc 中具体的说明如下:
>
> ```c
> /*
>    Unsorted chunks
>
>     All remainders from chunk splits, as well as all returned chunks,
>     are first placed in the "unsorted" bin. They are then placed
>     in regular bins after malloc gives them ONE chance to be used before
>     binning. So, basically, the unsorted_chunks list acts as a queue,
>     with chunks being placed on it in free (and malloc_consolidate),
>     and taken off (to be either used or placed in bins) in malloc.
>
>     The NON_MAIN_ARENA flag is never set for unsorted chunks, so it
>     does not have to be taken into account in size comparisons.
>  */
> ```
>
> ```c
> /* The otherwise unindexable 1-bin is used to hold unsorted chunks. */
> #define unsorted_chunks(M) (bin_at(M, 1))
> ```
>
> 从该宏我们可以看出， Unsorted Bin 处于我们之前所说的 Bin 数组 Index = 1 处，故而 Unsorted Bin 只有一个链表。
>
> Unsorted Bin 中的空闲 `chunk` 处于乱序状态，主要是有两个来源:
>
> 1. 当一个较大的 `chunk` 被分割为两半后，如果剩下的部分大于 MINISIZE，就会被 " 流放 " 到 Unsorted Bin 中。
> 2. 当释放一个不属于 FastBin 的 `chunk`​ ， 且该 `chunk`​ 不与 `Top chunk`​ 紧邻，该 `chunk` 会首先被放入 Unsorted Bin 中。
>
>    关于`Top chunk` 的解释，请参考后面的介绍。
>
> 此外，Unsorted Bin 在使用的过程中，采用的遍历顺序是 **FIFO规则** 。

‍

# 常用宏

根据 chunk 大小统一地获取 chunk 所在的索引

```c
#define bin_index(sz)                                                          \
    ((in_smallbin_range(sz)) ? smallbin_index(sz) : largebin_index(sz))
```

‍

‍
