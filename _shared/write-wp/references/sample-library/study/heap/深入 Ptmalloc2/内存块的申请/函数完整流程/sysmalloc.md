---
title: sysmalloc
date: 2025-04-27T22:18:09+08:00
lastmod: 2025-04-27T22:18:28+08:00
---

# sysmalloc

# `sysmalloc` 函数完整流程

## 开始

- 入口假设：`av->top`​ 剩余空间不足以满足 `nb` 字节的申请，需要向系统请求更多内存。

---

## ① 检查是否考虑 `mmap`

- 条件：

  - ​`av == NULL`
  - 或者 `(nb >= mp_.mmap_threshold && mp_.n_mmaps < mp_.n_mmaps_max)`
- **是**：尝试用 `mmap` 分配

  - 对 `nb + overhead`​ 进行页对齐，得到申请的 `size`
  - 调用 `mmap`

    - **成功**：

      - 根据对齐需求调整返回的 chunk
      - 设置 `prev_size`​ 和 `head`
      - 更新 mmap 相关的统计信息
      - 返回新分配的 chunk
    - **失败**：

      - 继续往下执行（意味着 mmap 失败，回到 normal heap 扩展流程）

---

## ② 再次检查 `av == NULL`

- 如果 `av == NULL`​，而且 `mmap` 也失败了

  - **返回 NULL**

---

## ③ 保存旧堆顶信息

- 保存：

  - ​`old_top = av->top`
  - ​`old_size = chunksize(old_top)`
  - ​`old_end = old_top + old_size`

---

## ④ 验证旧堆顶的正确性

- 要么是第一次使用（`old_top == initial_top(av) && old_size == 0`）
- 要么必须满足：

  - ​`old_size >= MINSIZE`
  - ​`prev_inuse(old_top) == true`
  - ​`old_end`​ 地址页对齐 (`old_end & (pagesize - 1) == 0`)

---

## ⑤ 调用 `MORECORE`

- 尝试向系统申请新的空间（即 `sbrk` 系列接口）
- 保存返回的 `brk`​ 和 `snd_brk`（第二次尝试时用）

---

## ⑥ 检查 `MORECORE` 的返回值

- **brk !=**  **MORECORE_FAILURE**

  - 如果 `mp_.sbrk_base == 0`

    - 初始化 `mp_.sbrk_base = brk`
  - ​`av->system_mem += size`

### 分情况处理：

#### ⑥.1 正常连续扩展堆顶

- 条件：

  - ​`brk == old_end`
  - 并且 `snd_brk == MORECORE_FAILURE`
- 行动：

  - 直接扩大 `old_top` 的 size
  - ​`set_head(old_top, (size + old_size) | PREV_INUSE)`

#### ⑥.2 堆顶被外部占用了（严重错误）

- 条件：

  - ​`contiguous(av) == true`
  - ​`old_size != 0`
  - ​`brk < old_end`
- 行动：

  - 打印错误信息 `malloc_printerr("break adjusted to free malloc space")`
  - 通常会导致程序崩溃

#### ⑥.3 其他情况（如堆非连续、或者存在 foreign sbrk）

- 行动：

  - 计算 front misalignment（前面对齐偏差）
  - 计算 end misalignment（末尾对齐偏差）
  - 可能再次调用 `MORECORE` 进行对齐修正

    - 如果成功，再重新整理 top chunk
    - 如果失败，返回 NULL
  - 设置新的 `top` chunk，并对齐

---

## ⑦ 如果 `MORECORE` 失败

- 尝试第二次 `MORECORE`（带 correction）
- 如果第二次也失败

  - **返回 NULL**

---

# 小总结

- **优先使用 mmap** 分配大块内存
- **其次扩展 top chunk**
- **如果堆不连续或混乱，会特殊处理**
- **如果一切失败，返回 NULL**
