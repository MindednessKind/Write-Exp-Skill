---
title: _libc_malloc
date: 2025-04-27T22:17:29+08:00
lastmod: 2025-04-27T22:17:38+08:00
---

# _libc_malloc

# `_libc_malloc` 函数完整流程

> 这是 glibc 中标准 `malloc` 函数的核心实现，负责用户申请内存时，选择合适的策略来分配内存块。

---

## 开始

- 入口参数：`size` —— 申请的字节数。

---

## ① 处理 size \= 0 的情况

- 如果 `size == 0`

  - 按照 glibc 规范，仍然会分配一小块内存，防止返回 NULL。
  - ​`size = MINSIZE`

---

## ② 转换用户申请的 size

- 计算 **真实需要申请的 chunk 大小** (`nb`)：

  - 包括：

    - 用户数据
    - 元数据（chunk header）
    - 对齐补齐
- 通过宏：`nb = request2size(size)`

---

## ③ 选择对应的 arena

- 在多线程环境下，malloc 使用 **多个 arena** 来避免竞争。
- ​`mstate av = arena_for_malloc(nb)`

  - 如果找不到合适的 arena，直接返回 NULL。

---

## ④ 检查 tcache

- 如果启用了 `tcache` 且对应 bin 非空：

  - 直接从 tcache bin 中取出一个块返回。
  - （tcache 是 glibc 2.26 引入的 per-thread 小缓存，非常快）

---

## ⑤ 检查 fastbins

- 如果 `nb <= av->max_fast`

  - 进入 fastbin 检查。
- 检查对应 fastbin 链表：

  - **非空**：取出链表头，更新链表，返回 chunk。
  - **空**：继续往下走。

---

## ⑥ 尝试从 smallbins/unsorted bin 分配

- 检查 unsorted bin：

  - 遍历 unsorted bin 中的 chunk

    - **找到适合的 chunk**：

      - 如果大小正好，直接使用。
      - 如果太大，可以切割，切出需要的块。
    - 找不到合适的，继续下一步。
- 检查 smallbin：

  - 如果有合适大小的 smallbin 非空，也可以从中取出。

---

## ⑦ top chunk 分配

- 如果以上步骤都找不到可用块

  - 尝试从 top chunk（堆顶）分配。
  - 如果 top chunk 空间足够：

    - 从 top 切下需要的大小 (`nb`)
    - 更新 av-\>top 指针
    - 返回切下来的 chunk。

---

## ⑧ 调用 `sysmalloc`

- 如果 top chunk 空间也不足：

  - 调用 `sysmalloc(nb, av)`  
    → 向系统申请更多内存（sbrk/mmap）。

---

## ⑨ 返回结果

- 申请成功：

  - 将分配好的 chunk 转换为用户态地址（chunk2mem）
  - 返回给用户。
- 申请失败：

  - 返回 NULL。

---

# 小结

|阶段|行动|
| ------------------------| ----------------------------------------|
|size\=0|标准处理，申请一小块内存|
|转换 nb|用户 size → 内部 nb（含对齐和头信息）|
|选择 arena|多线程支持，分配到合适 arena|
|tcache|优先从 tcache 取|
|fastbins|如果是 fastbin 大小，检查 fastbin|
|smallbins/unsorted bin|再检查 normal bin|
|top chunk|再不行从 top chunk 切一块|
|sysmalloc|top 不够大，调用 sysmalloc，系统分配|
|返回||
