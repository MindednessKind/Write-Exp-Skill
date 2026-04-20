---
title: Free chunk
date: 2024-12-22T22:58:13+08:00
lastmod: 2025-01-10T19:45:25+08:00
---

# Free chunk

‍

![Free Chunk](assets/Free%20Chunk-20250110181549-2twc3wm.png)

‍

Free chunk中，`prev_size`中必定存储着上一个块的用户数据。

若上个块以及该块 同为Free chunk，两个块会进行合并。

因此，Free chunk的上一个块必定是Allocated chunk。

‍

‍

fd 是指向 同一个bin中的 Free chunk， bk 指向 同一个bin中的 Free chunk。

‍

特别地，Large bins 中的Free chunk会有`fd_nextsize`​ 以及`bk_nextsize`。

其分别指向Large bins 中 前一个(更大的) 以及 后一个(更小的) 空闲块。
