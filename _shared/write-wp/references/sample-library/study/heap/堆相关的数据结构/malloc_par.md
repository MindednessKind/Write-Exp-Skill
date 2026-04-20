---
title: malloc_par
date: 2025-04-23T00:54:12+08:00
lastmod: 2026-03-24T17:09:06+08:00
---

# malloc_par

# 概述

​`malloc_par`​ 是 `glibc`​ 中与内存分配器相关的另一个结构体，全称通常是 `malloc_par`​（即 *malloc parameters*），用于**配置内存分配器的一些全局参数**，控制行为如 fastbin 的最大值、是否启用 mmap 等。

我们又在利用时将其叫做 mp_ 结构，具体实例的定义存在于malloc.c中

```c
static struct malloc_par mp_ =
{
  .top_pad = DEFAULT_TOP_PAD,
  .n_mmaps_max = DEFAULT_MMAP_MAX,
  .mmap_threshold = DEFAULT_MMAP_THRESHOLD,
  .trim_threshold = DEFAULT_TRIM_THRESHOLD,
#define NARENAS_FROM_NCORES(n) ((n) * (sizeof (long) == 4 ? 2 : 8))
  .arena_test = NARENAS_FROM_NCORES (1)
};
```

‍

# 🧩 `struct malloc_par` 是什么？

这是一个结构体，定义了一组与整个堆分配器相关的参数，这些参数影响 **所有 arena** 的行为。

```c
struct malloc_par {
    INTERNAL_SIZE_T trim_threshold;      // 触发 trim（释放回系统）的阈值
    INTERNAL_SIZE_T top_pad;             // 分配额外内存的 padding
    INTERNAL_SIZE_T mmap_threshold;      // 超过这个大小就用 mmap 分配
    INTERNAL_SIZE_T arena_test;          // 创建新 arena 的条件参数
    INTERNAL_SIZE_T arena_max;           // 最大 arena 数量
    int n_mmaps;                         // 当前 mmap 分配的数量
    int n_mmaps_max;                     // mmap 分配的最大数量
    int max_n_mmaps;                     // mmap 分配总数限制
    int no_dyn_threshold;               // 是否禁用动态调整 mmap_threshold
    int pagesize;                        // 系统页大小（Page Size）
    int malloc_debug;                   // debug 开关
    // 还有其他字段...
};
```

---

## 📌 主要字段解释

|字段名|含义|示例解释|
| --------| ------------------------------------------------------| ----------------------------|
|​`trim_threshold`|控制当空闲内存超过这个阈值时是否释放回系统（调用`sbrk(-x)`）|控制堆收缩|
|​`top_pad`|每次向系统申请内存时额外保留的字节数|提高性能，减少系统调用频率|
|​`mmap_threshold`|当请求内存大于此值时，使用`mmap`​而不是`sbrk`|避免大块内存碎片|
|​`arena_max`|允许的最大 arena 数量（多线程时用）|限制多线程下内存池的数量|
|​`pagesize`|系统页面大小|通常是 4KB 或 2MB|

---

## 🔍 它在哪被使用？

- 在 `glibc`​ 的 `malloc`​ 实现中，例如 `malloc.c`​，这个结构体叫 `mp_`（即：malloc parameters）。
- **全局唯一实例**：`static struct malloc_par mp_;`
- 所有线程共享这个配置，它影响所有的分配策略。

---

## 🛠️ 举个应用场景

如果你调用：

```c
mallopt(M_TRIM_THRESHOLD, 128 * 1024);
```

就会影响 `mp_.trim_threshold`，让 malloc 在释放空闲 chunk 时更积极地归还内存给系统。

---

## 🚨 和 `malloc_state` 的区别

|对比项|​`malloc_state`|​`malloc_par`|
| ------------| ---------------------------------| ------------------------|
|粒度|每个 arena 一份|全局一份|
|作用|保存每个 arena 的状态和结构|控制整个分配器的行为|
|包含内容|fastbins、bins、top、系统内存等|阈值、开关、调试参数等|
|与线程关系|每个线程可能使用不同的`malloc_state`|所有线程共用一个`malloc_par`|
