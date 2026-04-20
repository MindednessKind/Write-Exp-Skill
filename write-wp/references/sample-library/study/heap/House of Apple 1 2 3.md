---
title: House of Apple 1 2 3
date: 2025-11-24T12:18:51+08:00
lastmod: 2025-11-24T12:23:34+08:00
---

# House of Apple 1 2 3

House of Apple 系列的漏洞的适用范围极广，能够覆盖 glibc2.23至今的所有版本，可以说是最强的一把梭方法了。

之前一直都没有特意去学习这个东西，所以今天来了解学习一下

# House of Apple 1

### 适用范围

1. 程序能够从main函数返回，或能调用一次exit函数
2. 能泄露heap地址及libc地址
3. 能使用一次 Largebin Attack

### 具体利用漏洞

_IO_wstr_overflow 会将任意地址存储的值修改为已知值

‍
