---
title: Small Bin
date: 2025-04-05T21:36:27+08:00
lastmod: 2025-04-05T22:17:07+08:00
---

# Small Bin

Small Bin 中每个 `chunk` 的大小与其所在的 Bin 的 Index 的关系为:

	Chunk_Size = 2 * SIZE_SZ * Index

具体如下

|下标|SIZE\_SZ\=4（32 位）|SIZE\_SZ\=8（64 位）|
| ------| ----------------------------| ----------------------------|
|2|16|32|
|3|24|48|
|4|32|64|
|5|40|80|
|x|2\*4\*x|2\*8\*x|
|63|504|1008|

‍

Small Bin 中一共有 62个循环双向链表，每个链表中存储的`chunk` 大小都一致。

比如对于 32位的系统而言，下表2所对应的双向链表中存储的 `chunk` 大小均为 16字节 。

每个链表都拥有链表头节点，这样方便于对链表内部节点的管理。

特别的，**Small Bin 中每个 Bin 对应的链表都采用** **FIFO规则**，所以同一个链表中先被释放的 `chunk` 会先被分配出去。

‍

Small Bin 相关的宏如下

```c
#define NSMALLBINS 64
#define SMALLBIN_WIDTH MALLOC_ALIGNMENT
// 是否需要对small bin的下标进行纠正
#define SMALLBIN_CORRECTION (MALLOC_ALIGNMENT > 2 * SIZE_SZ)

#define MIN_LARGE_SIZE ((NSMALLBINS - SMALLBIN_CORRECTION) * SMALLBIN_WIDTH)
//判断chunk的大小是否在small bin范围内
#define in_smallbin_range(sz)                                                  \
    ((unsigned long) (sz) < (unsigned long) MIN_LARGE_SIZE)
// 根据chunk的大小得到small bin对应的索引。
#define smallbin_index(sz)                                                     \
    ((SMALLBIN_WIDTH == 16 ? (((unsigned) (sz)) >> 4)                          \
                           : (((unsigned) (sz)) >> 3)) +                       \
     SMALLBIN_CORRECTION)
```

**或许大家会疑惑，那 Small Bin 是否与 FastBin 中的** **​`chunk`​**​ **的大小会有大部分的重合？ 那么 Small Bin 中对应大小的 Bin 是否是没有太大的作用？**

其实不然， FastBin 中的 `chunk` 是有可能被放到 Small Bin 中去的，在我们后面分析具体的源码时，会有更深刻的理解。

‍

‍

‍
