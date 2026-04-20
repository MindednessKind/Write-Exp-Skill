---
title: Unsorted Bin
date: 2025-04-05T22:27:22+08:00
lastmod: 2025-04-05T22:36:16+08:00
---

# Unsorted Bin

Unsorted Bin 可以视为空闲 `chunk` 回归其所属 Bin 之前的缓冲区。

其在 Glibc 中具体的说明如下:

```c
/*
   Unsorted chunks

    All remainders from chunk splits, as well as all returned chunks,
    are first placed in the "unsorted" bin. They are then placed
    in regular bins after malloc gives them ONE chance to be used before
    binning. So, basically, the unsorted_chunks list acts as a queue,
    with chunks being placed on it in free (and malloc_consolidate),
    and taken off (to be either used or placed in bins) in malloc.

    The NON_MAIN_ARENA flag is never set for unsorted chunks, so it
    does not have to be taken into account in size comparisons.
 */
```

‍

```c
/* The otherwise unindexable 1-bin is used to hold unsorted chunks. */
#define unsorted_chunks(M) (bin_at(M, 1))
```

从该宏我们可以看出， Unsorted Bin 处于我们之前所说的 Bin 数组 Index = 1 处，故而 Unsorted Bin 只有一个链表。

Unsorted Bin 中的空闲 `chunk` 处于乱序状态，主要是有两个来源:

1. 当一个较大的 `chunk` 被分割为两半后，如果剩下的部分大于 MINISIZE，就会被 " 流放 " 到 Unsorted Bin 中。
2. 当释放一个不属于 FastBin 的 `chunk`​ ， 且该 `chunk`​ 不与 `Top chunk`​ 紧邻，该 `chunk` 会首先被放入 Unsorted Bin 中。

   关于`Top chunk` 的解释，请参考后面的介绍。

此外，Unsorted Bin 在使用的过程中，采用的遍历顺序是 **FIFO规则** 。

‍
