---
title: Chunk 相关宏
date: 2025-04-05T13:11:23+08:00
lastmod: 2025-04-05T17:24:55+08:00
---

# Chunk 相关宏

# `chunk`chunk 与 mem 指针头部的转换

mem 指向用户得到的内存的起始位置

```c
/* conversion from malloc headers to user pointers, and back */
#define chunk2mem(p) ((void *) ((char *) (p) + 2 * SIZE_SZ))
#define mem2chunk(mem) ((mchunkptr)((char *) (mem) -2 * SIZE_SZ))
```

# 最小的chunk大小

```c
/* The smallest possible chunk */
#define MIN_CHUNK_SIZE (offsetof(struct malloc_chunk, fd_nextsize))
```

在这里， offsetof() 函数会计算出 fd_nextsize 在 malloc_chunk 中的便宜，说明最小的 chunk 至少要包含 bk 指针。

# 最小申请的堆内存大小

用户最小申请的内存大小必须是 2*SIZE_SZ 的最小整数倍

> Tip
>
> 就目前而看 MIN_CHUNK_SIZE 和 MINISIZE 大小是一致的，这样设置两个宏的目的推测是方便之后对malloc_chunk的修改
>
> ```c
> /* The smallest size we can malloc is an aligned minimal chunk */
> //MALLOC_ALIGN_MASK = 2 * SIZE_SZ -1
> #define MINSIZE                                                                \
>     (unsigned long) (((MIN_CHUNK_SIZE + MALLOC_ALIGN_MASK) &                   \
>                       ~MALLOC_ALIGN_MASK))
> ```

# 检查分配给用户的内存是否对齐

2 * SIZE_SZ 大小对齐

```c
/* Check if m has acceptable alignment */
// MALLOC_ALIGN_MASK = 2 * SIZE_SZ -1
#define aligned_OK(m) (((unsigned long) (m) & MALLOC_ALIGN_MASK) == 0)

#define misaligned_chunk(p)                                                    \
    ((uintptr_t)(MALLOC_ALIGNMENT == 2 * SIZE_SZ ? (p) : chunk2mem(p)) &       \
     MALLOC_ALIGN_MASK)
```

‍

# 请求字节数判断

```c
/*
   Check if a request is so large that it would wrap around zero when
   padded and aligned. To simplify some other code, the bound is made
   low enough so that adding MINSIZE will also not wrap around zero.
 */

#define REQUEST_OUT_OF_RANGE(req)                                              \
    ((unsigned long) (req) >= (unsigned long) (INTERNAL_SIZE_T)(-2 * MINSIZE))
```

‍

# 将用户请求内存大小转为实际分配内存大小

```c
/* pad request bytes into a usable size -- internal version */
//MALLOC_ALIGN_MASK = 2 * SIZE_SZ -1
#define request2size(req)                                                      \
    (((req) + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE)                           \
         ? MINSIZE                                                             \
         : ((req) + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)

/*  Same, except also perform argument check */

#define checked_request2size(req, sz)                                          \
    if (REQUEST_OUT_OF_RANGE(req)) {                                           \
        __set_errno(ENOMEM);                                                   \
        return 0;                                                              \
    }                                                                          \
    (sz) = request2size(req);
```

当一个 `chunk`​ 处于以分配状态时，它的物理相邻的下一个 `chunk`​ 的 prev_size 字段必然是无效的，故而这个字段就可以被当前这个 `chunk`​ 使用。 这就是 ptmalloc 中 `chunk` 间的复用。

具体流程如下

1. 首先利用 `REQUEST_OUT_OF_RANGE`​ 判断是否可以分配用户请求的字节大小的 `chunk`
2. 之后，需要注意的是用户请求的字节是用来存储数据的，即 `chunk header` 后面的部分。

   与此同时，由于 `chunk`​ 间复用，所以可以使用下一个 `chunk` 的 prev_size 字段。因此，这里只需要再添加 SIZE_SZ 大小即可完全存储内容。
3. 由于系统中所允许的申请的 `chunk` 最小的大小是 MINISIZE，所以对其进行比较，如果不满足最低要求，即直接分配 MINISIZE 字节。
4. 如果前一条的比较结果是大于 MINISIZE， 由于系统中申请的 `chunk`​ 需要进行对齐操作，所以这里需要加上 MALLOC_ALIGN_MASK 以便进行 `chunk` 的对齐

‍

# 标记位相关宏

```c
/* size field is or'ed with PREV_INUSE when previous adjacent chunk in use */
#define PREV_INUSE 0x1

/* extract inuse bit of previous chunk */
#define prev_inuse(p) ((p)->mchunk_size & PREV_INUSE)

/* size field is or'ed with IS_MMAPPED if the chunk was obtained with mmap() */
#define IS_MMAPPED 0x2

/* check for mmap()'ed chunk */
#define chunk_is_mmapped(p) ((p)->mchunk_size & IS_MMAPPED)

/* size field is or'ed with NON_MAIN_ARENA if the chunk was obtained
   from a non-main arena.  This is only set immediately before handing
   the chunk to the user, if necessary.  */
#define NON_MAIN_ARENA 0x4

/* Check for chunk from main arena.  */
#define chunk_main_arena(p) (((p)->mchunk_size & NON_MAIN_ARENA) == 0)

/* Mark a chunk as not being on the main arena.  */
#define set_non_main_arena(p) ((p)->mchunk_size |= NON_MAIN_ARENA)

/*
   Bits to mask off when extracting size
   Note: IS_MMAPPED is intentionally not masked off from size field in
   macros for which mmapped chunks should never be seen. This should
   cause helpful core dumps to occur if it is tried by accident by
   people extending or adapting this malloc.
 */
#define SIZE_BITS (PREV_INUSE | IS_MMAPPED | NON_MAIN_ARENA)
```

# 获取 chunk size

```c
/* Get size, ignoring use bits */
#define chunksize(p) (chunksize_nomask(p) & ~(SIZE_BITS))

/* Like chunksize, but do not mask SIZE_BITS.  */
#define chunksize_nomask(p) ((p)->mchunk_size)
```

‍

# 获取下一个物理相邻的 chunk

```c
/* Ptr to next physical malloc_chunk. */
#define next_chunk(p) ((mchunkptr)(((char *) (p)) + chunksize(p)))
```

‍

# 获取前一个 chunk 的信息

```c
/* Size of the chunk below P.  Only valid if !prev_inuse (P).  */
#define prev_size(p) ((p)->mchunk_prev_size)

/* Set the size of the chunk below P.  Only valid if !prev_inuse (P).  */
#define set_prev_size(p, sz) ((p)->mchunk_prev_size = (sz))

/* Ptr to previous physical malloc_chunk.  Only valid if !prev_inuse (P).  */
#define prev_chunk(p) ((mchunkptr)(((char *) (p)) - prev_size(p)))
```

‍

# 当前 chunk 使用状态的相关操作

```c
/* extract p's inuse bit */
#define inuse(p)                                                               \
    ((((mchunkptr)(((char *) (p)) + chunksize(p)))->mchunk_size) & PREV_INUSE)

/* set/clear chunk as being inuse without otherwise disturbing */
#define set_inuse(p)                                                           \
    ((mchunkptr)(((char *) (p)) + chunksize(p)))->mchunk_size |= PREV_INUSE

#define clear_inuse(p)                                                         \
    ((mchunkptr)(((char *) (p)) + chunksize(p)))->mchunk_size &= ~(PREV_INUSE)
```

# 设置 chunk 的 size 字段

```c
/* Set size at head, without disturbing its use bit */
// SIZE_BITS = 7
#define set_head_size(p, s)                                                    \
    ((p)->mchunk_size = (((p)->mchunk_size & SIZE_BITS) | (s)))

/* Set size/use field */
#define set_head(p, s) ((p)->mchunk_size = (s))

/* Set size at footer (only when chunk is not in use) */
#define set_foot(p, s)                                                         \
    (((mchunkptr)((char *) (p) + (s)))->mchunk_prev_size = (s))
```

‍

# 获取指定偏移的 chunk

```c
/* Treat space at ptr + offset as a chunk */
#define chunk_at_offset(p, s) ((mchunkptr)(((char *) (p)) + (s)))
```

‍

# 制定偏移处 chunk 使用状态的相关操作

```c
/* check/set/clear inuse bits in known places */
#define inuse_bit_at_offset(p, s)                                              \
    (((mchunkptr)(((char *) (p)) + (s)))->mchunk_size & PREV_INUSE)

#define set_inuse_bit_at_offset(p, s)                                          \
    (((mchunkptr)(((char *) (p)) + (s)))->mchunk_size |= PREV_INUSE)

#define clear_inuse_bit_at_offset(p, s)                                        \
    (((mchunkptr)(((char *) (p)) + (s)))->mchunk_size &= ~(PREV_INUSE))
```

‍
