---
title: _libc_calloc
date: 2025-04-23T02:40:29+08:00
lastmod: 2025-04-27T19:54:03+08:00
---

# _libc_calloc

calloc 也是 libc 中的一种申请内存块的函数。

在 `libc`​ 中的封装为 `_libc_calloc`，具体介绍如下

```c
/*
  calloc(size_t n_elements, size_t element_size);
  Returns a pointer to n_elements * element_size bytes, with all locations
  set to zero.
*/
void*  __libc_calloc(size_t, size_t);
```

‍
