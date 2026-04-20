---
title: Unlink操作
date: 2024-12-13T23:27:56+08:00
lastmod: 2025-06-18T20:49:58+08:00
tags:
  - 'heap'
  - 'knowledge'
---

# Unlink操作

‍

# 施工中......

## Unlink的触发条件

|Chunk 类型|​`free()`行为|是否触发`unlink`|
| ------------| -------------------------------------------------------------------| -------------|
|**fastbin**(`< 0x80`)|不会合并相邻空闲 chunk（no consolidate）只是将 chunk 丢入`fastbinsY[]`单链表|❌ 不会触发|
|**smallbin**(`>= 0x80`)|会尝试合并前后空闲 chunk（coalesce）触发`unlink()`从双向链表中移除|✅ 会触发|
|**largebin**(`>= 0x400`)|同样支持合并，必然触发 unlink|✅ 会触发|

# 简介

Unlink操作实际作用是 **将两个物理相邻的堆块合并**，生成一个较大的新的堆块。

但因为Bin是使用双向链表连接的，所以会产生多步操作，我们可以简化为以下操作

A   <-   Mid   ->   B

> Tip
>
> 这里执行的操作是将Mid与B堆块合并
>
> **Mid -&gt; fd = &amp;B   |   Mid -&gt; bk = &amp;A**

# 旧版本Unlink

```c
B = Mid -> fd  
  
A = Mid -> bk
  
B -> bk = A
  
A -> fd = B
```

# 新版本Unlink

新版本较于旧版本实际知识多了一个检测的过程，检测 `FD->bk`​, `BK->fd`​, `Mid的地址` 这三个值是否相等

```c
B = Mid -> fd  
  
A = Mid -> bk
  
B -> bk = A
  
A -> fd = B
  
if (__builtin_expect (A->bk != Mid || B->fd != Mid, 0 )){
	malloc_printerr( check_action, "corrupted double-linked list", P, AV);
	rn go(f, seed, []);
}
```

‍
