---
title: Example
date: 2024-12-19T22:16:01+08:00
lastmod: 2024-12-19T22:57:39+08:00
---

# Example

```c
char *buffer = (char *)malloc(10);

strcpy(buffer, "hello");
printf("%s\n", buffer);

free(buffer);
```

这里第一行分配了十个字节的空间给 buffer

> 注意！
>
> 	这里的类型转换是必须的，如若没有，malloc创建的内存块将会是void类型，即无法对应地将其地址赋值给buffer

第三、四行是对其进行部分操作

在第六行对buffer指向的堆空间进行了释放

这里我们给出 free 以及 malloc 的注释:

> ## **malloc指令**
>
> ### 原文
>
> ```
> /*
>   malloc(size_t n)
>   Returns a pointer to a newly allocated chunk of at least n
>   bytes, or null if no space is available. Additionally, on 
>   failure, errno is set to ENOMEM on ANSI C systems.
>
>   If n is zero, malloc returns a minimum-sized chunk. (The
>   minimum size is 16 bytes on most 32bit systems, and 24 or 32
>   bytes on 64bit systems.)  On most systems, size_t is an unsigned
>   type, so calls with negative arguments are interpreted as
>   requests for huge amounts of space, which will often fail. The
>   maximum supported value of n differs across systems, but is in
>   all cases less than the maximum representable value of a
>   size_t.
> */
> ```
>
> ### [malloc 注释翻译](../Resources/Glibc中相关指令/Translation%20翻译.md#20241219223331-rr7dq3c)

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
> ### [free 注释翻译](../Resources/Glibc中相关指令/Translation%20翻译.md#20241219223859-7d93hfm)
