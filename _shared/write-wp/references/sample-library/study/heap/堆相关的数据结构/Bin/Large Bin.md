---
title: Large Bin
date: 2025-04-05T22:17:58+08:00
lastmod: 2025-04-05T22:26:50+08:00
---

# Large Bin

Large Bin 中一共包括 63个 Bin，每个 Bin 中的 `chunk` 的大小不是一致，而是处于一定区间范围内。

此外，这 63个 Bin 被分为了 6组，每组 Bin 中的 `chunk` 大小之间的公差一致

具体如下:

|组|数量|公差|
| ----| ------| ---------|
|1|32|64B|
|2|16|512B|
|3|8|4096B|
|4|4|32768B|
|5|2|262144B|
|6|1|不限制|

‍

这里我们以 32位平台的 Large Bin 为例，第一个 Large Bin 的起始 `chunk`​ 大小为 512字节，位于第一组，所以该 Bin 可以存储的 `chunk` 的大小范围为 [512,512+64) 。

‍

关于 Large Bin 的宏如下

```c
#define largebin_index_32(sz)                                                  \
    (((((unsigned long) (sz)) >> 6) <= 38)                                     \
         ? 56 + (((unsigned long) (sz)) >> 6)                                  \
         : ((((unsigned long) (sz)) >> 9) <= 20)                               \
               ? 91 + (((unsigned long) (sz)) >> 9)                            \
               : ((((unsigned long) (sz)) >> 12) <= 10)                        \
                     ? 110 + (((unsigned long) (sz)) >> 12)                    \
                     : ((((unsigned long) (sz)) >> 15) <= 4)                   \
                           ? 119 + (((unsigned long) (sz)) >> 15)              \
                           : ((((unsigned long) (sz)) >> 18) <= 2)             \
                                 ? 124 + (((unsigned long) (sz)) >> 18)        \
                                 : 126)

#define largebin_index_32_big(sz)                                              \
    (((((unsigned long) (sz)) >> 6) <= 45)                                     \
         ? 49 + (((unsigned long) (sz)) >> 6)                                  \
         : ((((unsigned long) (sz)) >> 9) <= 20)                               \
               ? 91 + (((unsigned long) (sz)) >> 9)                            \
               : ((((unsigned long) (sz)) >> 12) <= 10)                        \
                     ? 110 + (((unsigned long) (sz)) >> 12)                    \
                     : ((((unsigned long) (sz)) >> 15) <= 4)                   \
                           ? 119 + (((unsigned long) (sz)) >> 15)              \
                           : ((((unsigned long) (sz)) >> 18) <= 2)             \
                                 ? 124 + (((unsigned long) (sz)) >> 18)        \
                                 : 126)

// XXX It remains to be seen whether it is good to keep the widths of
// XXX the buckets the same or whether it should be scaled by a factor
// XXX of two as well.
#define largebin_index_64(sz)                                                  \
    (((((unsigned long) (sz)) >> 6) <= 48)                                     \
         ? 48 + (((unsigned long) (sz)) >> 6)                                  \
         : ((((unsigned long) (sz)) >> 9) <= 20)                               \
               ? 91 + (((unsigned long) (sz)) >> 9)                            \
               : ((((unsigned long) (sz)) >> 12) <= 10)                        \
                     ? 110 + (((unsigned long) (sz)) >> 12)                    \
                     : ((((unsigned long) (sz)) >> 15) <= 4)                   \
                           ? 119 + (((unsigned long) (sz)) >> 15)              \
                           : ((((unsigned long) (sz)) >> 18) <= 2)             \
                                 ? 124 + (((unsigned long) (sz)) >> 18)        \
                                 : 126)

#define largebin_index(sz)                                                     \
    (SIZE_SZ == 8 ? largebin_index_64(sz) : MALLOC_ALIGNMENT == 16             \
                                                ? largebin_index_32_big(sz)    \
                                                : largebin_index_32(sz))
```

这里我们以 32位平台下，第一个 Large Bin 的起始 `chunk` 大小为例，其大小为 512字节，那么进行计算:  512>>6 == 8 ，所以其下标为 56 + ( 512 >> 6 ) == 64 。

‍
