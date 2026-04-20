---
title: Free操作
date: 2024-12-15T22:48:59+08:00
lastmod: 2024-12-20T18:09:47+08:00
tags:
  - 'heap'
  - 'knowledge'
---

# Free操作

## 操作细则

通过分析((20241215230834-7gmwtmh 'Glibc-free指令'))可以得到其实际实现的操作:

释放传入指针指向的内存块。

如果传给`free`​的参数是一个空指针，`free`​不会做任何事，而如果传入的是已经`free`​过的指<span data-type="text" style="background-color: var(--b3-card-info-background); color: var(--b3-card-info-color);">针，那么后果将是</span>**不可估计的**<span data-type="text" style="background-color: var(--b3-card-info-background); color: var(--b3-card-info-color);">。</span>[Double Free漏洞](Double%20Free漏洞.md)

> 但是特别地，free只是释放了malloc所申请的内存，并没有改变指针的值。
>
> 而且，由于指针所指向的内存空间已经被释放，所以其他代码是有机会改写其指向的内存空间之中的内容的，相当于此时该指针指向了一个可以使用，但容易引起程式安全漏洞的内存区域，这个又被称为**野指针。**
>
> 野指针是一个指向已删除的对象，或是 指向一个未申请访问的、受限内存区域下的指针。它与空指针不同，野指针无法通过简单的判断是否为空来避免。

它的作用实际只是告诉**操作系统**这一部分内存不处于正在使用状态，可以进行收回操作，于是操作系统会将该内存链接在链接表上。但是用户仍能够通过之前曾经指向该内存的指针访问该段内存空间，只是该段内存空间上的值可能会发生变化。

这也就引出了所谓的[UAF漏洞](UAF漏洞.md)

## 链接

> ## **free指令**
>
> ### 原文
>
> ```
> /*
>   free(void* p)
>   Releases the chunk of memory pointed to by p, that had been
>   previously allocated using malloc or a related routine such as
>   realloc. It has no effect if p is null. It can have arbitrary
>   (i.e., bad!) effects if p has already been freed.
>
>   Unless disabled (using mallopt), freeing very large spaces will
>   when possible, automatically trigger operations that give
>   back unused memory to the system, thus reducing program
>   footprint.
> */
> ```
>
> ### [free 注释翻译](../Resources/Glibc中相关指令/Translation%20翻译.md#20241219223859-7d93hfm)
>
> }}}

> ```bash
> The  free() function frees the memory space pointed to by ptr,
> which must have been returned by a previous call to malloc(), calloc(), or realloc().  
> Otherwise, or if free(ptr) has already been called before, 
> undefined  behavior  occurs.
> If ptr is NULL, no operation is performed.
> ```

‍
