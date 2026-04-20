---
title: Allocated chunk
date: 2024-12-22T21:44:23+08:00
lastmod: 2025-03-24T19:59:20+08:00
---

# Allocated chunk

![](assets/image-20241222170126-ojqudw6.png "Allocated Chunk 构造")

chunk指针是真正chunk的起始位置

mem指针是用户数据存储的起始位置

‍

第一个部分<sup>（32位中为 4B ；64位中为 8B）</sup> 叫做`prev_size`，在前一个chunk空闲时表示前一个块的大小，非空闲时有可能被前一个块征用，用于存储用户数据。

> 这里的前一个chunk指的是内存中所相邻的前一个，而不是在`freelist`链表中的前一个。
>
> ​`PREV_INUSE`代表的“前一个chunk同理”

第二个部分的高位存储chunk的大小，低三位因为不会被存储的大小用到，所以分别会表示

- P -- `PREV_INUSE` 之前的 chunk 已经被分配时记为 1，未被分配为 0
- M -- `IS_MMAPED`​ 当前 chunk 时`mmap()`得到的则记为 1， 反之则为 0
- N -- `NON_MAIN_ARENA`​ 当前 chunk 在`non_main_arena`里则为 1， 反之则为0

对应的源码如下

```c
/* size field is or'ed with PREV_INUSE when previous adjacent chunk in use */
#define PREV_INUSE 0x1

/* extract inuse bit of previous chunk */
#define prev_inuse(p)       ((p)->size & PREV_INUSE)


/* size field is or'ed with IS_MMAPPED if the chunk was obtained with mmap() */
#define IS_MMAPPED 0x2

/* check for mmap()'ed chunk */
#define chunk_is_mmapped(p) ((p)->size & IS_MMAPPED)


/* size field is or'ed with NON_MAIN_ARENA if the chunk was obtained
   from a non-main arena.  This is only set immediately before handing
   the chunk to the user, if necessary.  */
#define NON_MAIN_ARENA 0x4

/* check for chunk from non-main arena */
#define chunk_non_main_arena(p) ((p)->size & NON_MAIN_ARENA)
```

# Q&A

1. Q: `fd`​、`bk`​、`fd_nextsize`​、`bk_nextsize`这几个字段去哪里了？

   A: 对于**已分配的chunk**来说这几个字段是没有作用的，因而这几个字段被chunk征用，拿来存储用户的数据。
2. Q:为何第二个部分的低3位被存储其他信息而不会影响`size`?

   A: 这是因为`malloc`​会将用户申请的内存大小转化为实际分配的内存，以此满足八字节对齐<sup>（最少）</sup>的要求，同时留出额外空间存放 chunk 的头部。由于进行了八字节的对齐，则低三位失去了其作用。因而就可以使用低三位存储其他信息了。我们在获取真正的`size`时，是会忽略低三位的。

   ```c
   /*
      Bits to mask off when extracting size

      Note: IS_MMAPPED is intentionally not masked off from size field in
      macros for which mmapped chunks should never be seen. This should
      cause helpful core dumps to occur if it is tried by accident by
      people extending or adapting this malloc.
    */
   #define SIZE_BITS (PREV_INUSE | IS_MMAPPED | NON_MAIN_ARENA)

   /* Get size, ignoring use bits */
   #define chunksize(p)         ((p)->size & ~(SIZE_BITS))
   ```
3. Q: `malloc` 是如何将申请的大小转化为实际分配的大小呢?

   A: 其核心在于 `request2size`宏

   ```c
   /* pad request bytes into a usable size -- internal version */

   #define request2size(req)                                         \
     (((req) + SIZE_SZ + MALLOC_ALIGN_MASK < MINSIZE)  ?             \
      MINSIZE :                                                      \
      ((req) + SIZE_SZ + MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK)
   ```

   其中用到了其他的几个宏定义，这里也贴出来

   ```c
   #  define MALLOC_ALIGNMENT       (2 *SIZE_SZ)

   /* The corresponding bit mask value */
   #define MALLOC_ALIGN_MASK      (MALLOC_ALIGNMENT - 1)

   /* The smallest possible chunk */
   #define MIN_CHUNK_SIZE        (offsetof(struct malloc_chunk, fd_nextsize))

   /* The smallest size we can malloc is an aligned minimal chunk */
   #define MINSIZE  \
     (unsigned long)(((MIN_CHUNK_SIZE+MALLOC_ALIGN_MASK) & ~MALLOC_ALIGN_MASK))
   ```
4. Q: 这个 `mem指针`是干什么用的?

   A: `mem指针`​是调用`malloc`​时返回给用户的指针。实际上，真正的chunk是从`chunk指针`开始的。

   ```c
   /* The corresponding word size */
   #define SIZE_SZ                (sizeof(INTERNAL_SIZE_T))

   /* conversion from malloc headers to user pointers, and back */

   #define chunk2mem(p)   ((void*)((char*)(p) + 2*SIZE_SZ))
   #define mem2chunk(mem) ((mchunkptr)((char*)(mem) - 2*SIZE_SZ))
   ```
5. Q: 用户申请的内存大小就是用户数据可用的内存大小吗？

   A: 这件事是不一定的，原因是字节对齐的问题。

   实际可用内存大小，是从`malloc_usable_size()`获得的，其核心函数如下

   ```c
   static size_t
   musable (void *mem)
   {
     mchunkptr p;
     if (mem != 0)
       {
         p = mem2chunk (mem);

         if (__builtin_expect (using_malloc_checking == 1, 0))
           return malloc_check_get_size (p);

         if (chunk_is_mmapped (p))
           return chunksize (p) - 2 * SIZE_SZ;
         else if (inuse (p))
           return chunksize (p) - SIZE_SZ;
       }
     return 0;
   }
   ```

‍
