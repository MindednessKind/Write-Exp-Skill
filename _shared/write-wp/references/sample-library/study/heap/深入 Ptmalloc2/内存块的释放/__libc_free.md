---
title: __libc_free
date: 2025-04-27T21:23:44+08:00
lastmod: 2025-04-27T21:26:11+08:00
---

# __libc_free

与 malloc 类似， free 函数同样也有一层封装，命名格式也与 malloc 基本类似。

```c
void __libc_free(void *mem) {
    mstate    ar_ptr;
    mchunkptr p; /* chunk corresponding to mem */
    // 判断是否有钩子函数 __free_hook
    void (*hook)(void *, const void *) = atomic_forced_read(__free_hook);
    if (__builtin_expect(hook != NULL, 0)) {
        (*hook)(mem, RETURN_ADDRESS(0));
        return;
    }
    // free NULL没有作用
    if (mem == 0) /* free(0) has no effect */
        return;
    // 将mem转换为chunk状态
    p = mem2chunk(mem);
    // 如果该块内存是mmap得到的
    if (chunk_is_mmapped(p)) /* release mmapped memory. */
    {
        /* See if the dynamic brk/mmap threshold needs adjusting.
       Dumped fake mmapped chunks do not affect the threshold.  */
        if (!mp_.no_dyn_threshold && chunksize_nomask(p) > mp_.mmap_threshold &&
            chunksize_nomask(p) <= DEFAULT_MMAP_THRESHOLD_MAX &&
            !DUMPED_MAIN_ARENA_CHUNK(p)) {
            mp_.mmap_threshold = chunksize(p);
            mp_.trim_threshold = 2 * mp_.mmap_threshold;
            LIBC_PROBE(memory_mallopt_free_dyn_thresholds, 2,
                       mp_.mmap_threshold, mp_.trim_threshold);
        }
        munmap_chunk(p);
        return;
    }
    // 根据chunk获得分配区的指针
    ar_ptr = arena_for_chunk(p);
    // 执行释放
    _int_free(ar_ptr, p, 0);
}
```
