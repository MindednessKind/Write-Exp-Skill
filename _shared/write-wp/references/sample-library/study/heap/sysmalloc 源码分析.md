---
title: sysmalloc 源码分析
date: 2026-03-26T21:31:15+08:00
lastmod: 2026-03-30T18:03:00+08:00
---

# sysmalloc 源码分析

# new_heap

```c
static heap_info *
internal_function
new_heap (size_t size, size_t top_pad)
{
  size_t pagesize = GLRO (dl_pagesize);
  char *p1, *p2;
  unsigned long ul;
  heap_info *h;

  //先对大小进行判断
  //如果两者大小相加小于 HEAP 的最小大小, 就割 HEAP的最小大小的 HEAP
  if (size + top_pad < HEAP_MIN_SIZE)
    size = HEAP_MIN_SIZE;
  // 如果两者相加没有超过 HEAP的最大大小, 就割下来所需size+top_pad大小的 HEAP
  else if (size + top_pad <= HEAP_MAX_SIZE)
    size += top_pad;
  //否则就是申请的大小过大，直接退出 new_heap
  else if (size > HEAP_MAX_SIZE)
    return 0;
  // 否则就是size <= HEAP_MAX_SIZE, 但加上 top_pad 就超了, 此时把最大能申请下来的大小全设为size
  else
    size = HEAP_MAX_SIZE;
  //对大小进行页对齐
  size = ALIGN_UP (size, pagesize);

  /* A memory region aligned to a multiple of HEAP_MAX_SIZE is needed.
     No swap space needs to be reserved for the following large
     mapping (on Linux, this is the case for all non-writable mappings
     anyway). */
  //首先对 p2进行初始化
  p2 = MAP_FAILED;
  //如果上一次留下了已经对齐的heap_area, 我们就会尝试走 MMAP来获得这块 HEAP 内存
  if (aligned_heap_area)
    {
      // mmap 一块 HEAP_MAX_SIZE 大小的内存
      p2 = (char *) MMAP (aligned_heap_area, HEAP_MAX_SIZE, PROT_NONE,
                          MAP_NORESERVE);
      //将当前对齐的area置空
      aligned_heap_area = NULL;
      //如果 MMAP 得到的内存没有对齐
      if (p2 != MAP_FAILED && ((unsigned long) p2 & (HEAP_MAX_SIZE - 1)))
        {
          //将其释放
          __munmap (p2, HEAP_MAX_SIZE);
          //将其记为 MMAP 失败
          p2 = MAP_FAILED;
        }
    }
  //如果 MMAP 失败, 或者没有可能对齐的area
  if (p2 == MAP_FAILED)
    {
      //尝试 MMAP一块 HEAP最大大小两倍的内存
      p1 = (char *) MMAP (0, HEAP_MAX_SIZE << 1, PROT_NONE, MAP_NORESERVE);

      //如果申请成功了
      if (p1 != MAP_FAILED)
        {
          //将 p2记为 p1进行内存对齐后的地址
          p2 = (char *) (((unsigned long) p1 + (HEAP_MAX_SIZE - 1))
                         & ~(HEAP_MAX_SIZE - 1));

          //将没有对齐的那部分内存还给系统
          ul = p2 - p1;
          if (ul)
              //归还p1到p2部分的内存
            __munmap (p1, ul);

          //这里就是没有非对齐的内存页,本来就是对齐的。那就将后面的一整块内存标记为 aligned_heap_arena
          else
            aligned_heap_area = p2 + HEAP_MAX_SIZE;
          //归还尾部的内存
          __munmap (p2 + HEAP_MAX_SIZE, HEAP_MAX_SIZE - ul);
        }
      //mmap 失败了
      else
        {
          /* Try to take the chance that an allocation of only HEAP_MAX_SIZE
             is already aligned. */
          //我们尝试只 mmap 一块 HEAP 大小的内存
          p2 = (char *) MMAP (0, HEAP_MAX_SIZE, PROT_NONE, MAP_NORESERVE);
          // 如果还是失败，就直接退出
          if (p2 == MAP_FAILED)
            return 0;
          //如果当前申请的内存不对齐，也直接归还内存并退出
          if ((unsigned long) p2 & (HEAP_MAX_SIZE - 1))
            {
              __munmap (p2, HEAP_MAX_SIZE);
              return 0;
            }
        }
    }
  //在这里将申请的内存加上 rw 权限, 如果 mprotect执行失败，则这块内存用不了，直接释放，退出
  if (__mprotect (p2, size, PROT_READ | PROT_WRITE) != 0)
    {
      __munmap (p2, HEAP_MAX_SIZE);
      return 0;
    }

  //准备返回申请出的 heap
  
  //拿地址
  h = (heap_info *) p2;
  
  //设置当前大小
  h->size = size;
  
  //设置 mprotect的大小
  h->mprotect_size = size;
  
  //一个探针，供调试使用
  LIBC_PROBE (memory_heap_new, 2, h, h->size);
  
  return h;
}
```

‍

# grow_heap

```c
static int
grow_heap (heap_info *h, long diff)
{
  // 首先拿到当前的页大小
  size_t pagesize = GLRO (dl_pagesize);
  long new_size;
  // 需要扩容的大小向上对齐到页大小的整数倍
  diff = ALIGN_UP (diff, pagesize);
  //将新大小设置为 原本大小加上 diff
  new_size = (long) h->size + diff;
  // 如果需要生成的大小大于 HEAP 的最大大小了，就返回 -1(错误)
  if ((unsigned long) new_size > (unsigned long) HEAP_MAX_SIZE)
    return -1;
  // 如果需要生成的大小大于当前设置了 rw 权限的内存大小, 就对没有设置权限的那一块内存进行设置
  if ((unsigned long) new_size > h->mprotect_size)
    {
      if (__mprotect ((char *) h + h->mprotect_size,
                      (unsigned long) new_size - h->mprotect_size,
                      PROT_READ | PROT_WRITE) != 0)
          // 如果mprotect失败，则返回 -2 (error)
        return -2;
      //将 mprotect_size 更新
      h->mprotect_size = new_size;
    }
  // 到这里说明 grow 成功，将size更新
  h->size = new_size;
  // 一个debug用的探针
  LIBC_PROBE (memory_heap_more, 2, h, h->size);
  // 返回 0 (success)
  return 0;
}
```

‍
