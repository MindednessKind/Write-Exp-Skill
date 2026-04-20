---
title: tcache
date: 2025-04-27T22:03:44+08:00
lastmod: 2025-04-28T21:35:24+08:00
---

# tcache

tcache 是 glibc 2.26 (ubuntu 17.10) 后引入的一种技术（see [commit](https://sourceware.org/git/?p=glibc.git;a=commitdiff;h=d5c3fafc4307c9b7a4c7d5cb381fcdbfad340bcc)），其目的是 提升堆管理器的性能。

但提升新能的同时也舍弃了不少安全检查，因而有了更多种类的利用方式。

> 这里主要参考 glibc 的源码， angekboy 的 slide 及 tukan.farm 在最后有链接 ⚠️(记得看)

# 相关结构体

tcache 技术引入了两个新的结构体， `tcache_entry`​ 以及 `tcache_perthread_struct`

这其实与 Fast Bin 相似，但又不完全相似。

## tcache_entry

[source code](https://code.woboq.org/userspace/glibc/malloc/malloc.c.html#tcache_entry)

```c
/* We overlay this structure on the user-data portion of a chunk when
   the chunk is stored in the per-thread cache.  */
typedef struct tcache_entry
{
  struct tcache_entry *next;
} tcache_entry;
```

​`tcache_entry`​ 用于链接空闲的 chunk 结构体，其中的 `next` 指针会指向下一个大小相同的 chunk。

‍

需要注意的是，这里的 next 指向的是 chunk 的 user data处，而 Fast Bin 的 fd 是指向 chunk 开头的地址，也就是chunk头的位置。

而且， tcache_entry 会对 空闲chunk 的 user data部分进行复用。

## tcache_perthread_struct

[source code](https://code.woboq.org/userspace/glibc/malloc/malloc.c.html#tcache_perthread_struct)

```c
/* There is one of these for each thread, which contains the
   per-thread cache (hence "tcache_perthread_struct").  Keeping
   overall size low is mildly important.  Note that COUNTS and ENTRIES
   are redundant (we could have just counted the linked list each
   time), this is for performance reasons.  */
typedef struct tcache_perthread_struct
{
  char counts[TCACHE_MAX_BINS];
  tcache_entry *entries[TCACHE_MAX_BINS];
} tcache_perthread_struct;

# define TCACHE_MAX_BINS                64

static __thread tcache_perthread_struct *tcache = NULL;
```

每一个 thread(线程) 都会维护一个 `tcache_perthread_struct`​，它是整个 tcache 的管理结构，一共存在 `TCACHE_MAX_BINS`​ 个计数器 及 `TCACHE_MAX_BINS` 项 tcache_entry

-  `tcache_entry` 通过单向链表的方式链接了相同大小的处于空闲状态 ( free 后 ) 的 chunk，这一点与 Fast Bin 相似。
-  `counts`​ 记录了 `tcache_entry` 链上的 空闲的 chunk 的数目，每条链上最多可以存在 7个 chunk。

大抵可以这么理解：

> tcache_perthread_struct  
> ┌──────────────────────────────────────────────────────┐  
> │ counts[0]  →  3                                                                                                        │  
> │ entries[0] →  tcache_entry₁ → tcache_entry₂ → tcache_entry₃ → NULL		    │  
> │                                                                                             					    │  
> │ counts[1]  →  0                   									                    │  
> │ entries[1] →  NULL                								                    │  
> │                                                  										    │  
> │ counts[2]  →  2                               								            │  
> │ entries[2] →  tcache_entry₄ → tcache_entry₅ → NULL 					    │  
> │                                                     										    │  
> │ ...                                                  									    │  
> │ counts[63] →  1                                       								    │  
> │ entries[63] → tcache_entry₆ → NULL                   						    │  
> └──────────────────────────────────────────────────────┘
>
> 再展开说一下每一个小细节：
>
> - **counts[i]** ：第 i 个 bin 当前缓存了多少个 chunk（`char` 类型，最大值默认是 7）
> - **entries[i]** ：指向第一个空闲的 chunk（`tcache_entry` 类型）
> - **tcache_entry**：
>
>   - 是一个链表节点，指向下一个同大小 chunk。
> - 每一条 entries[i] 链表，保存**同一 size class**的 chunk。

# 基本工作方式

- 在第一次 malloc 时，会先 malloc 一块内存用来存放 `tcache_perthread_struct`。
- free 内存，且 size 小于 Small Bin size时
