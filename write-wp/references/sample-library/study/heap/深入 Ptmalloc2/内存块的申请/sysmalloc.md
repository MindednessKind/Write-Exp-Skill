---
title: sysmalloc
date: 2025-04-23T02:40:54+08:00
lastmod: 2025-04-27T22:14:45+08:00
---

# sysmalloc

# 前言

正如该函数头的注释所言，该函数用于当前堆内存不足时，需要向系统申请更多的内存时。

```c
/*
   sysmalloc handles malloc cases requiring more memory from the system.
   On entry, it is assumed that av->top does not have enough
   space to service request for nb bytes, thus requiring that av->top
   be extended or replaced.
 */
```

# 基本定义

```c
static void *sysmalloc(INTERNAL_SIZE_T nb, mstate av) {
  mchunkptr old_top;        /* incoming value of av->top */
  INTERNAL_SIZE_T old_size; /* its size */
  char *old_end;            /* its end address */

  long size; /* arg to first MORECORE or mmap call */
  char *brk; /* return value from MORECORE */

  long correction; /* arg to 2nd MORECORE call */
  char *snd_brk;   /* 2nd return val */

  INTERNAL_SIZE_T front_misalign; /* unusable bytes at front of new space */
  INTERNAL_SIZE_T end_misalign;   /* partial page left at end of new space */
  char *aligned_brk;              /* aligned offset into brk */

  mchunkptr p;                  /* the allocated/returned chunk */
  mchunkptr remainder;          /* remainder frOm allocation */
  unsigned long remainder_size; /* its size */

  size_t pagesize = GLRO(dl_pagesize);
  bool tried_mmap = false;
```

我们可以主要关注一下 `pagesize`

```c
#ifndef EXEC_PAGESIZE
#define EXEC_PAGESIZE   4096
#endif
# define GLRO(name) _##name
size_t _dl_pagesize = EXEC_PAGESIZE;
```

所以，当前的 `pagesize = 4096 == 0x1000`

# 考虑 mmap

正如开头的注释所言，如果满足一下任意一种条件

1. 没有分配堆
2. 申请的内存大于 `mp_.mmap_threshold`，并且 mmap 的数量小于最大值，就可以尝试使用 mmap。

默认情况下，临界值为

```c
static struct malloc_par mp_ = {
    .top_pad = DEFAULT_TOP_PAD,
    .n_mmaps_max = DEFAULT_MMAP_MAX,
    .mmap_threshold = DEFAULT_MMAP_THRESHOLD,
    .trim_threshold = DEFAULT_TRIM_THRESHOLD,
#define NARENAS_FROM_NCORES(n) ((n) * (sizeof(long) == 4 ? 2 : 8))
    .arena_test = NARENAS_FROM_NCORES(1)
#if USE_TCACHE
        ,
    .tcache_count = TCACHE_FILL_COUNT,
    .tcache_bins = TCACHE_MAX_BINS,
    .tcache_max_bytes = tidx2usize(TCACHE_MAX_BINS - 1),
    .tcache_unsorted_limit = 0 /* No limit.  */
#endif
};
```

​`DEFAULT_MMAP_THRESHOLD`​ 为 128*1024 字节，即 `128 K`。

```c
#ifndef DEFAULT_MMAP_THRESHOLD
#define DEFAULT_MMAP_THRESHOLD DEFAULT_MMAP_THRESHOLD_MIN
#endif
/*
  MMAP_THRESHOLD_MAX and _MIN are the bounds on the dynamically
  adjusted MMAP_THRESHOLD.
*/

#ifndef DEFAULT_MMAP_THRESHOLD_MIN
#define DEFAULT_MMAP_THRESHOLD_MIN (128 * 1024)
#endif

#ifndef DEFAULT_MMAP_THRESHOLD_MAX
/* For 32-bit platforms we cannot increase the maximum mmap
   threshold much because it is also the minimum value for the
   maximum heap size and its alignment.  Going above 512k (i.e., 1M
   for new heaps) wastes too much address space.  */
#if __WORDSIZE == 32
#define DEFAULT_MMAP_THRESHOLD_MAX (512 * 1024)
#else
#define DEFAULT_MMAP_THRESHOLD_MAX (4 * 1024 * 1024 * sizeof(long))
#endif
#endif
```

下面就是这部分代码，但目前并不是我们所关心的重点，所以我们可以暂时跳过。

```c
  /*
     If have mmap, and the request size meets the mmap threshold, and
     the system supports mmap, and there are few enough currently
     allocated mmapped regions, try to directly map this request
     rather than expanding top.
   */

  if (av == NULL ||
      ((unsigned long)(nb) >= (unsigned long)(mp_.mmap_threshold) &&
       (mp_.n_mmaps < mp_.n_mmaps_max))) {
    char *mm; /* return value from mmap call*/

  try_mmap:
    /*
       Round up size to nearest page.  For mmapped chunks, the overhead
       is one SIZE_SZ unit larger than for normal chunks, because there
       is no following chunk whose prev_size field could be used.

       See the front_misalign handling below, for glibc there is no
       need for further alignments unless we have have high alignment.
     */
    if (MALLOC_ALIGNMENT == 2 * SIZE_SZ)
      size = ALIGN_UP(nb + SIZE_SZ, pagesize);
    else
      size = ALIGN_UP(nb + SIZE_SZ + MALLOC_ALIGN_MASK, pagesize);
    tried_mmap = true;

    /* Don't try if size wraps around 0 */
    if ((unsigned long)(size) > (unsigned long)(nb)) {
      mm = (char *)(MMAP(0, size, PROT_READ | PROT_WRITE, 0));

      if (mm != MAP_FAILED) {
        /*
           The offset to the start of the mmapped region is stored
           in the prev_size field of the chunk. This allows us to adjust
           returned start address to meet alignment requirements here
           and in memalign(), and still be able to compute proper
           address argument for later munmap in free() and realloc().
         */

        if (MALLOC_ALIGNMENT == 2 * SIZE_SZ) {
          /* For glibc, chunk2mem increases the address by 2*SIZE_SZ and
             MALLOC_ALIGN_MASK is 2*SIZE_SZ-1.  Each mmap'ed area is page
             aligned and therefore definitely MALLOC_ALIGN_MASK-aligned.  */
          assert(((INTERNAL_SIZE_T)chunk2mem(mm) & MALLOC_ALIGN_MASK) == 0);
          front_misalign = 0;
        } else
          front_misalign = (INTERNAL_SIZE_T)chunk2mem(mm) & MALLOC_ALIGN_MASK;
        if (front_misalign > 0) {
          correction = MALLOC_ALIGNMENT - front_misalign;
          p = (mchunkptr)(mm + correction);
          set_prev_size(p, correction);
          set_head(p, (size - correction) | IS_MMAPPED);
        } else {
          p = (mchunkptr)mm;
          set_prev_size(p, 0);
          set_head(p, size | IS_MMAPPED);
        }

        /* update statistics */

        int new = atomic_exchange_and_add(&mp_.n_mmaps, 1) + 1;
        atomic_max(&mp_.max_n_mmaps, new);

        unsigned long sum;
        sum = atomic_exchange_and_add(&mp_.mmapped_mem, size) + size;
        atomic_max(&mp_.max_mmapped_mem, sum);

        check_chunk(av, p);

        return chunk2mem(p);
      }
    }
  }
```

# 当 mmap 失败 或者 堆未被分配 时

```c
  /* There are no usable arenas and mmap also failed.  */
  if (av == NULL)
    return 0;
```

这两种情况，将会直接退出。

# 记录旧堆信息

```c
  /* Record incoming configuration of top */

  old_top = av->top;
  old_size = chunksize(old_top);
  old_end = (char *)(chunk_at_offset(old_top, old_size));

  brk = snd_brk = (char *)(MORECORE_FAILURE);
```

# 检查旧堆信息

## 1

```c
  /*
     If not the first time through, we require old_size to be
     at least MINSIZE and to have prev_inuse set.
   */

  assert((old_top == initial_top(av) && old_size == 0) ||
         ((unsigned long)(old_size) >= MINSIZE && prev_inuse(old_top) &&
          ((unsigned long)old_end & (pagesize - 1)) == 0));
```

这里区分两种情况

- **如果是第一次建堆：**

  - ​`old_top == initial_top(av)`：top chunk 还指着默认初始值（不是实际堆空间）。
  - ​`old_size == 0`：大小也是 0，说明还没有堆内存。
- **如果已经建过堆了：**

  - ​`old_size >= MINSIZE`：堆中 top chunk 至少要有 MINSIZE 大小（保证安全）。
  - ​`prev_inuse(old_top)`：top chunk 的前一个 chunk 应该是 inuse 状态（防止非法合并）。
  - ​`old_end` 应该页对齐（符合系统管理要求）。

> 这块断言就是在验证 arena 的健康状态：  
> 	**要么就是第一次初始化，要么就是已有堆且状态正常。**

>> “为什么需要 old\_end 页对齐？”
>>
>
> **因为在堆（heap）管理中，每次向系统申请新堆内存（通过** **​`sbrk`​**​ **或** **​`mmap`​**​ **）的时候，内存分配单位是按照“页”（Page）对齐的。**
>
> 而且特别重要的是：**如果 top chunk（空闲区）不是以页为单位对齐，后面再扩展堆、或者释放堆，就很容易出错。**
>
> 因此，**在每次使用** **​`sysmalloc`​**​ **之前，一定要确认当前已有的堆空间末尾（也就是 old_end）是页对齐的！**
>
> 否则，系统内存管理就会崩坏，不能正确管理 brk 或 mmap。

## 2

```c
  /* Precondition: not enough current space to satisfy nb request */
  assert((unsigned long)(old_size) < (unsigned long)(nb + MINSIZE));
```

根据 malloc 中的定义

```c
static void *_int_malloc(mstate av, size_t bytes) {
    INTERNAL_SIZE_T nb;  /* normalized request size */
```

> Q:  `nb`​ 应已经加上 chunk 头部的字节，为何还要加上 `MINSIZE` 呢？
>
> A:  因为 Top Chunk 的大小应该至少预留 MINSIZE 的空间，以便于其进行合并。

# 对于 非 Main_Arena

下面这段代码暂不分析。

```c
  if (av != &main_arena) {
    heap_info *old_heap, *heap;
    size_t old_heap_size;

    /* First try to extend the current heap. */
    old_heap = heap_for_ptr(old_top);
    old_heap_size = old_heap->size;
    if ((long)(MINSIZE + nb - old_size) > 0 &&
        grow_heap(old_heap, MINSIZE + nb - old_size) == 0) {
      av->system_mem += old_heap->size - old_heap_size;
      set_head(old_top,
               (((char *)old_heap + old_heap->size) - (char *)old_top) |
                   PREV_INUSE);
    } else if ((heap = new_heap(nb + (MINSIZE + sizeof(*heap)), mp_.top_pad))) {
      /* Use a newly allocated heap.  */
      heap->ar_ptr = av;
      heap->prev = old_heap;
      av->system_mem += heap->size;
      /* Set up the new top.  */
      top(av) = chunk_at_offset(heap, sizeof(*heap));
      set_head(top(av), (heap->size - sizeof(*heap)) | PREV_INUSE);

      /* Setup fencepost and free the old top chunk with a multiple of
         MALLOC_ALIGNMENT in size. */
      /* The fencepost takes at least MINSIZE bytes, because it might
         become the top chunk again later.  Note that a footer is set
         up, too, although the chunk is marked in use. */
      old_size = (old_size - MINSIZE) & ~MALLOC_ALIGN_MASK;
      set_head(chunk_at_offset(old_top, old_size + 2 * SIZE_SZ),
               0 | PREV_INUSE);
      if (old_size >= MINSIZE) {
        set_head(chunk_at_offset(old_top, old_size),
                 (2 * SIZE_SZ) | PREV_INUSE);
        set_foot(chunk_at_offset(old_top, old_size), (2 * SIZE_SZ));
        set_head(old_top, old_size | PREV_INUSE | NON_MAIN_ARENA);
        _int_free(av, old_top, 1);
      } else {
        set_head(old_top, (old_size + 2 * SIZE_SZ) | PREV_INUSE);
        set_foot(old_top, (old_size + 2 * SIZE_SZ));
      }
    } else if (!tried_mmap)
      /* We can at least try to use to mmap memory.  */
      goto try_mmap;
  }
```

# Main_Arena 的处理

## 计算内存

计算可以满足其请求的内存大小

```c
else { /* av == main_arena */

    /* Request enough space for nb + pad + overhead */
    size = nb + mp_.top_pad + MINSIZE;
```

在默认情况下，`top_pad` 会被定义为 131072 字节，即 0x20000字节

```c
#ifndef DEFAULT_TOP_PAD
# define DEFAULT_TOP_PAD 131072
#endif
```

## 是否连续

如果我们希望堆的空间连续的话，那么其实是可以复用之前的内存的

```c
    /*
       If contiguous, we can subtract out existing space that we hope to
       combine with new space. We add it back later only if
       we don't actually get contiguous space.
     */

    if (contiguous(av))
      size -= old_size;
```

## 对齐页大小

```c
    /*
       Round to a multiple of page size.
       If MORECORE is not contiguous, this ensures that we only call it
       with whole-page arguments.  And if MORECORE is contiguous and
       this is not first time through, this preserves page-alignment of
       previous calls. Otherwise, we correct to page-align below.
     */

    size = ALIGN_UP(size, pagesize);
```

## 申请内存

```c
    /*
       Don't try to call MORECORE if argument is so big as to appear
       negative. Note that since mmap takes size_t arg, it may succeed
       below even if we cannot call MORECORE.
     */

    if (size > 0) {
      brk = (char *)(MORECORE(size));
      LIBC_PROBE(memory_sbrk_more, 2, brk, size);
    }
```

### 成功

考虑则使用 hook

```c
    if (brk != (char *)(MORECORE_FAILURE)) {
      /* Call the `morecore' hook if necessary.  */
      void (*hook)(void) = atomic_forced_read(__after_morecore_hook);
      if (__builtin_expect(hook != NULL, 0))
        (*hook)();
    }
```

### 失败

失败则考虑使用mmap

```c
else {
      /*
         If have mmap, try using it as a backup when MORECORE fails or
         cannot be used. This is worth doing on systems that have "holes" in
         address space, so sbrk cannot extend to give contiguous space, but
         space is available elsewhere.  Note that we ignore mmap max count
         and threshold limits, since the space will not be used as a
         segregated mmap region.
       */

      /* Cannot merge with old top, so add its size back in */
      if (contiguous(av))
        size = ALIGN_UP(size + old_size, pagesize);

      /* If we are relying on mmap as backup, then use larger units */
      if ((unsigned long)(size) < (unsigned long)(MMAP_AS_MORECORE_SIZE))
        size = MMAP_AS_MORECORE_SIZE;

      /* Don't try if size wraps around 0 */
      if ((unsigned long)(size) > (unsigned long)(nb)) {
        char *mbrk = (char *)(MMAP(0, size, PROT_READ | PROT_WRITE, 0));

        if (mbrk != MAP_FAILED) {
          /* We do not need, and cannot use, another sbrk call to find end */
          brk = mbrk;
          snd_brk = brk + size;

          /*
             Record that we no longer have a contiguous sbrk region.
             After the first time mmap is used as backup, we do not
             ever rely on contiguous space since this could incorrectly
             bridge regions.
           */
          set_noncontiguous(av);
        }
      }
    }
```

## 可能申请成功？

```c
    if (brk != (char *)(MORECORE_FAILURE)) {
      if (mp_.sbrk_base == 0)
        mp_.sbrk_base = brk;
      av->system_mem += size;
```

接下来进行判断

### 情况1

```c
      /*
         If MORECORE extends previous space, we can likewise extend top size.
       */

      if (brk == old_end && snd_brk == (char *)(MORECORE_FAILURE))
        set_head(old_top, (size + old_size) | PREV_INUSE);
```

### 情况2 - 内存意外耗尽

```c
      else if (contiguous(av) && old_size && brk < old_end)
        /* Oops!  Someone else killed our space..  Can't touch anything.  */
        malloc_printerr("break adjusted to free malloc space");
```

### 处理其他意外情况

```c
      /*
         Otherwise, make adjustments:

       * If the first time through or noncontiguous, we need to call sbrk
          just to find out where the end of memory lies.

       * We need to ensure that all returned chunks from malloc will meet
          MALLOC_ALIGNMENT

       * If there was an intervening foreign sbrk, we need to adjust sbrk
          request size to account for fact that we will not be able to
          combine new space with existing space in old_top.

       * Almost all systems internally allocate whole pages at a time, in
          which case we might as well use the whole last page of request.
          So we allocate enough more memory to hit a page boundary now,
          which in turn causes future contiguous calls to page-align.
       */

      else {
        front_misalign = 0;
        end_misalign = 0;
        correction = 0;
        aligned_brk = brk;
```

#### 处理连续内存

```c
        /* handle contiguous cases */
        if (contiguous(av)) {
          /* Count foreign sbrk as system_mem.  */
          if (old_size)
            av->system_mem += brk - old_end;

          /* Guarantee alignment of first new chunk made from this space */

          front_misalign = (INTERNAL_SIZE_T)chunk2mem(brk) & MALLOC_ALIGN_MASK;
          if (front_misalign > 0) {
            /*
               Skip over some bytes to arrive at an aligned position.
               We don't need to specially mark these wasted front bytes.
               They will never be accessed anyway because
               prev_inuse of av->top (and any chunk created from its start)
               is always true after initialization.
             */

            correction = MALLOC_ALIGNMENT - front_misalign;
            aligned_brk += correction;
          }

          /*
             If this isn't adjacent to existing space, then we will not
             be able to merge with old_top space, so must add to 2nd request.
           */

          correction += old_size;

          /* Extend the end address to hit a page boundary */
          end_misalign = (INTERNAL_SIZE_T)(brk + size + correction);
          correction += (ALIGN_UP(end_misalign, pagesize)) - end_misalign;

          assert(correction >= 0);
          snd_brk = (char *)(MORECORE(correction));

          /*
             If can't allocate correction, try to at least find out current
             brk.  It might be enough to proceed without failing.

             Note that if second sbrk did NOT fail, we assume that space
             is contiguous with first sbrk. This is a safe assumption unless
             program is multithreaded but doesn't use locks and a foreign sbrk
             occurred between our first and second calls.
           */

          if (snd_brk == (char *)(MORECORE_FAILURE)) {
            correction = 0;
            snd_brk = (char *)(MORECORE(0));
          } else {
            /* Call the `morecore' hook if necessary.  */
            void (*hook)(void) = atomic_forced_read(__after_morecore_hook);
            if (__builtin_expect(hook != NULL, 0))
              (*hook)();
          }
        }
```

#### 处理不连续内存

```c
        /* handle non-contiguous cases */
        else {
          if (MALLOC_ALIGNMENT == 2 * SIZE_SZ)
            /* MORECORE/mmap must correctly align */
            assert(((unsigned long)chunk2mem(brk) & MALLOC_ALIGN_MASK) == 0);
          else {
            front_misalign =
                (INTERNAL_SIZE_T)chunk2mem(brk) & MALLOC_ALIGN_MASK;
            if (front_misalign > 0) {
              /*
                 Skip over some bytes to arrive at an aligned position.
                 We don't need to specially mark these wasted front bytes.
                 They will never be accessed anyway because
                 prev_inuse of av->top (and any chunk created from its start)
                 is always true after initialization.
               */

              aligned_brk += MALLOC_ALIGNMENT - front_misalign;
            }
          }

          /* Find out current end of memory */
          if (snd_brk == (char *)(MORECORE_FAILURE)) {
            snd_brk = (char *)(MORECORE(0));
          }
        }
```

#### 调整

```c
        /* Adjust top based on results of second sbrk */
        if (snd_brk != (char *)(MORECORE_FAILURE)) {
          av->top = (mchunkptr)aligned_brk;
          set_head(av->top, (snd_brk - aligned_brk + correction) | PREV_INUSE);
          av->system_mem += correction;

          /*
             If not the first time through, we either have a
             gap due to foreign sbrk or a non-contiguous region.  Insert a
             double fencepost at old_top to prevent consolidation with space
             we don't own. These fenceposts are artificial chunks that are
             marked as inuse and are in any case too small to use.  We need
             two to make sizes and alignments work out.
           */

          if (old_size != 0) {
            /*
               Shrink old_top to insert fenceposts, keeping size a
               multiple of MALLOC_ALIGNMENT. We know there is at least
               enough space in old_top to do this.
             */
            old_size = (old_size - 4 * SIZE_SZ) & ~MALLOC_ALIGN_MASK;
            set_head(old_top, old_size | PREV_INUSE);

            /*
               Note that the following assignments completely overwrite
               old_top when old_size was previously MINSIZE.  This is
               intentional. We need the fencepost, even if old_top otherwise
               gets lost.
             */
            set_head(chunk_at_offset(old_top, old_size),
                     (2 * SIZE_SZ) | PREV_INUSE);
            set_head(chunk_at_offset(old_top, old_size + 2 * SIZE_SZ),
                     (2 * SIZE_SZ) | PREV_INUSE);

            /* If possible, release the rest. */
            if (old_size >= MINSIZE) {
              _int_free(av, old_top, 1);
            }
          }
        }
      }
```

在这里需要注意的是，

这个程序将旧的 Top Chunk 进行了释放，那么其会根据其大小进入不同的 bin 亦或者是 tcache 中。

## 更新最大内存

```c
  if ((unsigned long)av->system_mem > (unsigned long)(av->max_system_mem))
    av->max_system_mem = av->system_mem;
  check_malloc_state(av);
```

## 分配内存块

### 获取大小

```c
  /* finally, do the allocation */
  p = av->top;
  size = chunksize(p);
```

### 切分 TOP

```c
  /* check that one of the above allocation paths succeeded */
  if ((unsigned long)(size) >= (unsigned long)(nb + MINSIZE)) {
    remainder_size = size - nb;
    remainder = chunk_at_offset(p, nb);
    av->top = remainder;
    set_head(p, nb | PREV_INUSE | (av != &main_arena ? NON_MAIN_ARENA : 0));
    set_head(remainder, remainder_size | PREV_INUSE);
    check_malloced_chunk(av, p, nb);
    return chunk2mem(p);
  }
```

## 在最后，捕捉所有错误

```c
  /* catch all failure paths */
  __set_errno(ENOMEM);
  return 0;
```

‍
