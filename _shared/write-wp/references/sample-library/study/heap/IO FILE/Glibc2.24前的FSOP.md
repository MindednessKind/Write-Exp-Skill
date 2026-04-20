---
title: Glibc2.24前的FSOP
date: 2025-12-11T19:44:42+08:00
lastmod: 2025-12-11T20:17:45+08:00
---

# Glibc2.24前的FSOP

在_IO_FILE攻击刚出现的一段时间里，Glibc是不会对 vtable 进行检查的，也就是在 **Glibc2.24前，是没有Vtable Check机制的**。

在这段时间里，我们有一种玩法
