---
title: Malloc_Printerr
date: 2025-04-02T20:28:43+08:00
lastmod: 2025-04-03T22:28:53+08:00
---

# Malloc_Printerr

Glibc Malloc 检测到错误时，会调用 `malloc_printerr` 函数

```c
static void malloc_printerr(const char *str) {
  __libc_message(do_abort, "%s\n", str);
  __builtin_unreachable();
}
```

主要会调用 `__libc_nessage`​ 来执行 `abort` 函数，如下

```c
  if ((action & do_abort)) {
    if ((action & do_backtrace))
      BEFORE_ABORT(do_abort, written, fd);

    /* Kill the application.  */
    abort();
  }
```

在 `abort` 函数里，glibc版本低于2.23时，会 fflush stream

```c
  /* Flush all streams.  We cannot close them now because the user
     might have registered a handler for SIGABRT.  */
  if (stage == 1)
    {
      ++stage;
      fflush (NULL);
    }
```

‍
