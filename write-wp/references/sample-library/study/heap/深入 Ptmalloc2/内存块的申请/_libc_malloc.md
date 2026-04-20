---
title: _libc_malloc
date: 2025-04-23T02:39:32+08:00
lastmod: 2025-04-23T02:52:52+08:00
---

# _libc_malloc

在程序中，我们一般会使用 malloc 函数来申请内存块。

可是当我们仔细浏览 glibc的源码实现时，其实是没有malloc函数的，因为该函数实际调用的是 __libc_malloc 函数。

为什么不直接创建一个 malloc函数呢？

	因为我们有时可能需要不同的名称，并且 __libc_malloc 函数实际上是对 _int_malloc函数的简单封装，实际上 _int_malloc 才是申请内存块的核心。

下面我们对于其具体的实现进行分析。

‍

该函数首先会检查是否存在内存分配函数的 钩子函数(，一般记为 __malloc_hook)，这个函数主要用于用户自定义的堆分配函数，以此方便用户快速修改堆分配函数并且进行测试。

这里需要我们注意的是，**用户所申请的字节一旦进入申请内存的函数中，便会变成一个无符号整数。**

```c
// wapper for int_malloc
void *__libc_malloc(size_t bytes) {
    mstate ar_ptr;
    void * victim;
    // 检查是否有内存分配钩子，如果有，调用钩子并返回.
    void *(*hook)(size_t, const void *) = atomic_forced_read(__malloc_hook);
    if (__builtin_expect(hook != NULL, 0))
        return (*hook)(bytes, RETURN_ADDRESS(0));
```

接着便会获取一个 Arena ，试图分配内存

```c
    arena_get(ar_ptr, bytes);
```

随后调用 `_int_malloc`函数，申请对应大小的内存

```c
    victim = _int_malloc(ar_ptr, bytes);
```

如果分配失败，ptmalloc会再次尝试寻找一个可用的 Arena 并再次分配内存

```c
    /* Retry with another arena only if we were able to find a usable arena
       before.  */
    if (!victim && ar_ptr != NULL) {
        LIBC_PROBE(memory_malloc_retry, 1, bytes);
        ar_ptr = arena_get_retry(ar_ptr, bytes);
        victim = _int_malloc(ar_ptr, bytes);
    }
```

如果申请到 Arena，那么在退出程序前，会对其进行解锁🔓

```c
    if (ar_ptr != NULL) __libc_lock_unlock(ar_ptr->mutex);
```

‍

随后对当前的状态进行判断 (这里使用 断言 Assert)

- 是否申请到内存
- 是否是 mmap的内存
- 申请的内存是否在分配的Arena中

```c
    assert(!victim || chunk_is_mmapped(mem2chunk(victim)) ||
           ar_ptr == arena_for_chunk(mem2chunk(victim)));
```

在最后返回内存地址。

```c
    return victim;
}
```
