---
title: IO库函数实际运作原理及调用
date: 2025-08-13T19:45:23+08:00
lastmod: 2025-08-14T17:50:50+08:00
---

# IO库函数实际运作原理及调用

这里讲解了IO库函数实际运作的原理及调用

# fread

其函数原型如下

```c
size_t fread ( void *buffer, size_t size, size_t count, FILE *stream) ;
```

- buffer 缓冲区地址
- size 读入的大小
- count 读入的次数
- stream 目标文件流
- return -> 读入读取缓冲区的 实际"count"

其代码位于 `/libio/iofread.c`​ ，函数名为 `_IO_fread`​，但真正功能实现位于子函数 `_IO_sgetn`

```c
_IO_size_t
_IO_fread (buf, size, count, fp)
     void *buf;
     _IO_size_t size;
     _IO_size_t count;
     _IO_FILE *fp;
{
  ...
  bytes_read = _IO_sgetn (fp, (char *) buf, bytes_requested);
  ...
}
```

 **_IO_sgetn会调用 _IO_XSGETN 函数，而 _IO_XSGETN 实际是 _IO_FILE_plus 中 vtable 中的函数指针**

在调用这个函数之前，会首先取出vtable中的函数指针再调用

```c
_IO_size_t
_IO_sgetn (fp, data, n)
     _IO_FILE *fp;
     void *data;
     _IO_size_t n;
{
  return _IO_XSGETN (fp, data, n);
}

```

在默认情况下，其是指向 _IO_file_xsgetn 函数的 

```c
  if (fp->_IO_buf_base
          && want < (size_t) (fp->_IO_buf_end - fp->_IO_buf_base))
        {
          if (__underflow (fp) == EOF)
        break;

          continue;
        }

```

‍

---

# fwrite

其函数原型如下

```c
size_t fwrite(const void* buffer, size_t size, size_t count, FILE* stream);
```

与fread基本一致

- buffer: 是一个指针，对 fwrite 来说，是要写入数据的地址;
- size: 要写入内容的单字节数;
- count: 要进行写入 size 字节的数据项的个数;
- stream: 目标文件指针;
- 返回值：实际写入的数据项个数 count。

‍

其代码位于 `/libio/iofwrite.c`，函数名 _IO_fwrite

其主要是调用了 _IO_sputn 来实现其功能

与前面一致，_IO_sputn 会调用 _IO_XSPUTN

与前面一致，_IO_XSPUTN也是位于vtable中的函数指针，会在调用前先在vtable中取出再调用

```c
written = _IO_sputn (fp, (const char *) buf, request);
```

_IO_XSPUTN 对应的默认函数为 _IO_new_file_xsputn，其会调用同样位于 vtable中的 _IO_OVERFLOW

```c
 /* Next flush the (full) buffer. */
      if (_IO_OVERFLOW (f, EOF) == EOF)
```

_IO_OVERFLOW对应的默认函数为 _IO_new_file_overflow

```c
if (ch == EOF)
    return _IO_do_write (f, f->_IO_write_base,
             f->_IO_write_ptr - f->_IO_write_base);
  if (f->_IO_write_ptr == f->_IO_buf_end ) /* Buffer is really full */
    if (_IO_do_flush (f) == EOF)
      return EOF;
```

在其内部最终会调用系统的write接口

‍

---

# fopen

其函数原型如下

```c
‍FILE *fopen(char *filename, *type);
```

- filename 目标文件路径
- type 打开类型(通常为 const char*，存储一个或多个字符)
- return-> 一个文件指针

‍

fopen函数主要进行几个操作

1. 使用 malloc 分配 FILE 结构
2. 设置 FILE 结构的 vtable
3. 初始化新分配的FILE结构
4. 将初始化的FILE结构链入链表中
5. 系统调用打开文件

这里就不展开讲了，想要了解的可以自己去了解一下

‍

---

# fclose

函数声明如下

```c
int fclose(FILE *stream)
```

关闭一个文件流，其会将缓冲区剩余的数据输出到磁盘文件，并释放文件指针及有关缓冲区

‍

其首先会调用 _IO_unlink_it ，让指定的 FILE 从链表中脱出

```c
if (fp->_IO_file_flags & _IO_IS_FILEBUF)
    _IO_un_link ((struct _IO_FILE_plus *) fp);

```

之后调用 _IO_file_close_it ，它会调用系统调用关闭文件

```c
if (fp->_IO_file_flags & _IO_IS_FILEBUF)
    status = _IO_file_close_it (fp);
```

最后会调用 _IO_FINISH(在vtable中)，对应的是 _IO_file_finish函数，其会调用free函数释放前分配的 FILE结构

```c
_IO_FINISH (fp);
```

‍

---

# printf/puts

在 printf 的参数是以'\\n'结束的纯字符串时，printf 会被优化为 puts 函数并去除换行符。

puts的源码实现函数为 _IO_puts，其流程参考friwte (_IO_sputn)

printf的调用栈如下，同样会调用到_IO_sputn

```c
vfprintf+11
_IO_file_xsputn
_IO_file_overflow
funlockfile
_IO_file_write
write
```

‍
