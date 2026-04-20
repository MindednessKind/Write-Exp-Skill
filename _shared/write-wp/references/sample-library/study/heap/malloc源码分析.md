---
title: malloc源码分析
date: 2026-03-26T21:29:12+08:00
lastmod: 2026-03-26T21:31:12+08:00
---

# malloc源码分析

# __libc_malloc()

```c
void *
__libc_malloc(size_t bytes) {
    mstate ar_ptr;
    // 保存指向分配区(arena)的指针 arena_ptr
    void *victim;
    // 保存获得的mem指针: chunk_addr+0x10, 即data的位置

    void *(*hook)(size_t, const void *)
    = atomic_forced_read(__malloc_hook);
    // malloc_hook -> 为程序如果需要自实现 malloc 留下的 hook
    if (__builtin_expect(hook != NULL, 0))
        return (*hook)(bytes, RETURN_ADDRESS (0));
    //若 malloc_hook 不为空，则直接执行 malloc_hook 函数，退出后面的malloc过程

    arena_get (ar_ptr, bytes);
    //获得当前线程对应的 thread_arena (malloc_state 结构体)

    victim = _int_malloc(ar_ptr, bytes);
    //将当前获得的 thread_arena 和要申请的大小一起传进 _int_malloc()

    /* Retry with another arena only if we were able to find a usable arena
       before.  */

    if (!victim && ar_ptr != NULL)
        //如果 没有成功申请到 chunk, 或当前 ar_ptr 为空
    {
        LIBC_PROBE(memory_malloc_retry, 1, bytes);
        ar_ptr = arena_get_retry(ar_ptr, bytes);
        // 重新尝试获取 arena 给 ar_ptr
        victim = _int_malloc(ar_ptr, bytes);
        // 重新设置 ar_ptr 后再试一次
    }

    // 只要当前 ar_ptr 不为空
    if (ar_ptr != NULL)
        //对当前ar_ptr解锁
        (void) mutex_unlock(&ar_ptr->mutex);

    /*
     * 如果申请 Chunk 为空
     * 如果申请的 Chunk 是 mmap 申请的
     * 如果用 arena 申请的 chunk 与当前 arena 不匹配
     *
     * 则报错
     * */
    assert (!victim || chunk_is_mmapped(mem2chunk(victim)) ||
            ar_ptr == arena_for_chunk(mem2chunk(victim)));
    return victim;
}
```

‍

# _int_malloc()

```c
static void *
_int_malloc(mstate av, size_t bytes) {
    INTERNAL_SIZE_T nb;               /* normalized request size */
    unsigned int idx;                 /* associated bin index */
    mbinptr bin;                      /* associated bin */

    mchunkptr victim;                 /* inspected/selected chunk */
    INTERNAL_SIZE_T size;             /* its size */
    int victim_index;                 /* its bin index */

    mchunkptr remainder;              /* remainder from a split */
    unsigned long remainder_size;     /* its size */

    unsigned int block;               /* bit map traverser */
    unsigned int bit;                 /* bit map traverser */
    unsigned int map;                 /* current word of binmap */

    mchunkptr fwd;                    /* misc temp for linking */
    mchunkptr bck;                    /* misc temp for linking */

    const char *errstr = NULL;

    /*
       Convert request size to internal form by adding SIZE_SZ bytes
       overhead plus possibly more to obtain necessary alignment and/or
       to obtain a size of at least MINSIZE, the smallest allocatable
       size. Also, checked_request2size traps (returning 0) request sizes
       that are so large that they wrap around zero when padded and
       aligned.
     */

    checked_request2size (bytes, nb);
    // 计算当前的 chunk_size (prev_size复用)

    /* There are no usable arenas.  Fall back to sysmalloc to get a chunk from
       mmap.  */
    if (__glibc_unlikely(av == NULL)) // 若当前 arena 为空，则使用 sysmalloc 获得内存
    {
        void *p = sysmalloc(nb, av);
        if (p != NULL)
            alloc_perturb(p, bytes);
        //在这里对数据进行初始化 (memset)
        return p;
    }

    /*
       If the size qualifies as a fastbin, first check corresponding bin.
       This code is safe to execute even if av is not yet initialized, so we
       can try it without checking, which saves some time on this fast path.
     */

    // 如果申请的Chunk大小小于 fastbin最大大小
    if ((unsigned long) (nb) <= (unsigned long) (get_max_fast ())) {

        // get_max_fast() -> 从 global_max_fast处获取fastbin最大大小
        idx = fastbin_index (nb); // ((((unsigned int) (nb)) >> ((sizeof(size_t)) == 8 ? 4 : 3)) - 2)
        // 从当前size算出对应的 fastbin index

        mfastbinptr *fb = &fastbin (av, idx);
        mchunkptr pp = *fb;
        //把fastbinY[idx]对应的第一个chunk取出，记为pp

        do {
            victim = pp;
            //将 victim设为pp
            if (victim == NULL)
                //若为空，则
                break;
        } while (
                (pp = catomic_compare_and_exchange_val_acq(fb, victim->fd, victim)
                        // *fb = victim->fd 即将当前选中的 freed chunk 从 fastbin 中取出
                        )
                 != victim);
        // 只要当前选中的 chunk 不为空，则进行检查
        if (victim != 0) {
            //如果拿到的chunk size对应的idx与前面的不同，则 error
            if (__builtin_expect(fastbin_index (chunksize(victim)) != idx, 0)) {
                errstr = "malloc(): memory corruption (fast)";
                errout:
                malloc_printerr(check_action, errstr, chunk2mem (victim), av);
                return NULL;
            }
            check_remalloced_chunk (av, victim, nb); // 该宏为空

            void *p = chunk2mem (victim);
            // 指针从chunk头移至data处

            alloc_perturb(p, bytes); // 用处不大

            return p;
        }
    }

    /*
       If a small request, check regular bin.  Since these "smallbins"
       hold one size each, no searching within bins is necessary.
       (For a large request, we need to wait until unsorted chunks are
       processed to find best fit. But for small ones, fits are exact
       anyway, so we can check now, which is faster.)
     */
    // 如果申请的 chunk 大小在 smallbin 的范围内
    if (in_smallbin_range (nb)) {
        //拿到相应size的 smallbin index
        idx = smallbin_index (nb);
        // 拿到相应 bin 中的 chunk
        bin = bin_at (av, idx);

        //如果 bin->bk != bin, 即当前 smallbin 不为空
        if ((victim = last (bin)) != bin) {


            if (victim == 0) /* initialization check */
                //如果没有从smallbin中取出东西
                // 调用 malloc_consolidate()
                malloc_consolidate(av);
            else {
                //如果成功从 smallbin 中取出了 chunk
                bck = victim->bk; //取出当前 chunk 的 bk
                if (__glibc_unlikely(bck->fd != victim)) {
                    // 如果 bk->fd != chunk, 则证明发生了 double free
                    // 爆err
                    errstr = "malloc(): smallbin double linked list corrupted";
                    goto errout;
                }
                // 给申请的后面的 chunk 的 prev_inuse 位设为 1
                set_inuse_bit_at_offset (victim, nb);

                // 将下一个 chunk 弄成第一个 chunk, 放在 smallbin 相应 idx 的第一个
                bin->bk = bck;
                bck->fd = bin;

                // 如果当前线程不是主线程, 也就是当前 arena 不是 main_arena
                if (av != &main_arena)
                    // 标记上
                    victim->size |= NON_MAIN_ARENA;

                //空的 check 宏
                check_malloced_chunk (av, victim, nb);

                //指针从 head 移至 data
                void *p = chunk2mem (victim);

                //没什么用的初始化函数(正常运行，没有特殊设置实际不会初始化)
                alloc_perturb(p, bytes);

                //返回
                return p;
            }
        }
    }

        /*
           If this is a large request, consolidate fastbins before continuing.
           While it might look excessive to kill all fastbins before
           even seeing if there is space available, this avoids
           fragmentation problems normally associated with fastbins.
           Also, in practice, programs tend to have runs of either small or
           large requests, but less often mixtures, so consolidation is not
           invoked all that often in most programs. And the programs that
           it is called frequently in otherwise tend to fragment.
         */
    // 既不是 fastbin 也不是 smallbin 的大小
    else {
        //拿当前申请的 size 对应的 largebin index
        idx = largebin_index (nb);

        // 如果 fastbin 里有东西, 则触发 malloc_consolidate()
        // 将 fastbin 中的空闲 chunk 塞进 unsortedbin 中
        if (have_fastchunks (av))
            malloc_consolidate(av);

        // -> 去大循环
    }

    /*
       Process recently freed or remaindered chunks, taking one only if
       it is exact fit, or, if this a small request, the chunk is remainder from
       the most recent non-exact fit.  Place other traversed chunks in
       bins.  Note that this step is the only place in any routine where
       chunks are placed in bins.

       The outer loop here is needed because we might not realize until
       near the end of malloc that we should have consolidated, so must
       do so and retry. This happens at most once, and only when we would
       otherwise need to expand memory to service a "small" request.
     */

    // 大循环
    /* *
     * 触发条件:
     * 申请大小 既没在 fastbin, 也没在 smallbin 中
     *
     * 目的:
     *  先在 unsortedbin 找, 找到就直接从 unsortedbin 中拿出来
     *  没在 unsortedbin 里面找到
     *  就先通过大循环将 unsortedbin 中的 chunk 全部按大小塞到 smallbin 和 largebin 里面
     * */
    for (;;) {
        int iters = 0;

        /*
         * 从 unsortedbin 中取出一个 chunk
         * 只要 unsortedbin 满足 self->bk != self
         * 即 unsortedbin 不为空
         * 便持续遍历 unsortedbin
         * */
        while ((victim = unsorted_chunks (av)->bk) != unsorted_chunks (av))

        {
            // 拿当前 chunk 的 bk
            bck = victim->bk;

            // 如果当前 size 小于 0x10, 或 申请大小 大于 当前arena的内存大小, 就会报错
            if (__builtin_expect(victim->size <= 2 * SIZE_SZ, 0)
                || __builtin_expect(victim->size > av->system_mem, 0))
                malloc_printerr(check_action, "malloc(): memory corruption",
                                chunk2mem (victim), av);

            // 拿到当前 unsortedbin 的 chunk 的真实大小
            size = chunksize (victim);

            /*
               If a small request, try to use last remainder if it is the
               only chunk in unsorted bin.  This helps promote locality for
               runs of consecutive small requests. This is the only
               exception to best-fit, and applies only when there is
               no exact fit for a small chunk.
             */

            /*
             * 如果 当前申请的大小在 smallbin 的范围内，
             * 并且 unsorted chunk 的 bk 指向 unsortedbin, 也就是 unsortedbin 里只有一个 chunk
             * 且这个 chunk 就是当前 arena 中的 last_remainder
             * 并且 last_remainder 的大小大于需要的 size+MINSIZE
             * */
            if (
                    in_smallbin_range (nb) &&
                    bck == unsorted_chunks (av) &&
                    victim == av->last_remainder &&
                    (unsigned long) (size) > (unsigned long) (nb + MINSIZE)
            )
            {
                /* split and reattach remainder */

                // 从当前 last_remainder 上切下来需要的部分
                remainder_size = size - nb;
                remainder = chunk_at_offset (victim, nb);

                // 将缩小的 last_remainder 重新塞回 unsortedbin 里
                unsorted_chunks (av)->bk = unsorted_chunks (av)->fd = remainder;
                av->last_remainder = remainder;
                remainder->bk = remainder->fd = unsorted_chunks (av);

                // 如果当前 remainder 的大小太大, 即属于 largebin, 则对其 fd_nextsize 和 bk_nextsize 置空
                if (!in_smallbin_range (remainder_size)) {
                    remainder->fd_nextsize = NULL;
                    remainder->bk_nextsize = NULL;
                }

                // 对申请出来的 chunk 进行 head 设置
                set_head (victim, nb | PREV_INUSE |
                                  (av != &main_arena ? NON_MAIN_ARENA : 0));

                // last_remainder 设置
                set_head (remainder, remainder_size | PREV_INUSE);

                // 把 last_ramainder->next_chunk->prev_size 设置好
                set_foot (remainder, remainder_size);

                check_malloced_chunk (av, victim, nb); // Empty
                void *p = chunk2mem (victim); //指针移动到data
                alloc_perturb(p, bytes); // 没什么用的初始化函数(默认不生效)
                return p;
            }

            /* remove from unsorted list */

            // 将 victim 从 unsortedbin 中彻底掏出来
            unsorted_chunks (av)->bk = bck;
            bck->fd = unsorted_chunks (av);

            /* Take now instead of binning if exact fit */

            // 如果 size 恰好与 申请大小 相同
            if (size == nb) {
                // set nextchunk 的 prev_inuse
                set_inuse_bit_at_offset (victim, size);

                //设置当前 chunk 的标志位
                if (av != &main_arena)
                    victim->size |= NON_MAIN_ARENA;
                check_malloced_chunk (av, victim, nb); // Empty
                void *p = chunk2mem (victim); // 指针后移至data
                alloc_perturb(p, bytes); // 假初始化
                return p;
            }

            // 到这里, 就说明当前 size 与 nb 不相同

            /* place chunk in bin */

            // 如果 size 在 smallbin 的范围内
            if (in_smallbin_range (size)) {
                // 拿到相应的 smallbin 的 index
                victim_index = smallbin_index (size);
                // 拿到对应的 smallbin[idx]
                bck = bin_at (av, victim_index);
                // 拿对应 smallbin 的 fd ()
                fwd = bck->fd;
            }
            // 如果是 largebin 的大小的话
            else {
                // *** Largebin Attack ***

                // 拿对应 largebin 的 index
                victim_index = largebin_index (size);
                // 拿 largebin[idx]
                bck = bin_at (av, victim_index);
                // 拿 相应的 bin 的 chunk->fd
                fwd = bck->fd;

                /* maintain large bins in sorted order */
                // 如果 largebin 不为空
                if (fwd != bck) {
                    /* Or with inuse bit to speed comparisons */
                    // 将当前chunk prev_inuse 位 置1
                    size |= PREV_INUSE;
                    /* if smaller than smallest, bypass loop below */

                    // 对当前 largebin 中的最后一个 chunk 的 non_main_arena 位进行校验, 要求其为 0
                    assert ((bck->bk->size & NON_MAIN_ARENA) == 0);

                    //如果 当前 size 大于 largebin 的 最后一个 chunk 的 size
                    if ((unsigned long) (size) < (unsigned long) (bck->bk->size)) {
                        // 将 fwd 写为表头
                        fwd = bck;
                        // 将 bck 写为最后一个 chunk
                        bck = bck->bk;

                        // 向 victim->fd_nextsize 内写入 largebin 内的第一个 chunk
                        victim->fd_nextsize = fwd->fd;
                        // 向 vicctim->bk_nextsize 内写入 largebin 内的第一个 chunk 的 bk_nextsize 的地址
                        victim->bk_nextsize = fwd->fd->bk_nextsize;

                        // 这里向 largebin 的第一个 chunk 的bk_nextsize 的 fd_nextsize 写成victim
                        // 再向 largebin的最后一个chunk的 bk_nextsize 里写 victim 地址
                        fwd->fd->bk_nextsize = victim->bk_nextsize->fd_nextsize = victim;

                        //我们这里就可以用这一条链
                        /*
                         * 我们伪造 largebin 内最后一个 chunk 的 bk_nextsize 为攻击点
                         * 加入我们要向 _IO_list_all_ 内写入一个 chunk 地址
                         * 就可以先将一个 chunk 放入 largebin
                         * 再将其 bk_nextsize 写为 _IO_list_all-0x18
                         * 这样就可以通过 (fwd->fd->bk_nextsize)->fd_nextsize = victim
                         * 向 (_IO_list_all-0x18)+0x18, 即 _IO_list_all 内写入 victim 地址了
                         * */
                    }
                    // 如果小于 largebin 的最后一个 chunk 的 size
                    else { // 该路径高版本修复

                        // 断言 largebin 第一个 chunk 的 non_main_arena 位 为0
                        assert ((fwd->size & NON_MAIN_ARENA) == 0);

                        /*
                         * 一直在当前 largebin 中找到比当前申请 size 大的 freed_chunk
                         * 其中每个 freed_chunk 的 non_main_arena 都不能为0, 如果为0说明有问题
                         *
                         * 没找到就把当前 fwd 更新为前一个与当前chunk_size大小不同的块
                         * */
                        while ((unsigned long) size < fwd->size) {
                            fwd = fwd->fd_nextsize;
                            assert ((fwd->size & NON_MAIN_ARENA) == 0);
                        }

                        // 如果当前申请 size 正好和 当前拿到的 freed chunk 相同, 则直接将当前 chunk 插到 fwd 这条小链里
                        if ((unsigned long) size == (unsigned long) fwd->size)
                            /* Always insert in the second position.  */
                            fwd = fwd->fd;
                        // 否则就是 当前拿到的 chunk 比当前的 size 大一点
                        else {
                            //将当前申请的 chunk 塞到 fwd 和 fwd->bk_nextsize 中间
                            victim->fd_nextsize = fwd;
                            victim->bk_nextsize = fwd->bk_nextsize;
                            fwd->bk_nextsize = victim;
                            victim->bk_nextsize->fd_nextsize = victim;
                        }
                        // 将 fwd->bk 记为 bck
                        bck = fwd->bk;
                    }
                }
                // 如果 largebin 为空, 则将 victim 直接塞到 largebin 里
                else
                    victim->fd_nextsize = victim->bk_nextsize = victim;
            }
            // 将 victim 插入链表
            mark_bin (av, victim_index); // 将 victim 塞到 arena 的数组里
            victim->bk = bck;
            victim->fd = fwd;
            fwd->bk = victim;
            bck->fd = victim;

#define MAX_ITERS       10000
            // 如果循环次数大于 MAX_ITERS, 则直接跳出
            if (++iters >= MAX_ITERS)
                break;
        }

        /*
           If a large request, scan through the chunks of current bin in
           sorted order to find smallest that fits.  Use the skip list for this.
         */

        // 如果申请 size 属于 largebin, 就进 largebin 找
        if (!in_smallbin_range (nb)) {
            // 取出相应的 largebin
            bin = bin_at (av, idx);

            /* skip scan if empty or largest chunk is too small */
            /* *
             * 如果
             * 1. largebin 为空
             * 2. largebin 里最大的 chunk 比需要申请的 chunk 小
             *
             * 则直接跳过遍历
             *
             * 反之，则证明这个 largebin 里有想要的大小的 freed chunk
             * */
            if ((victim = first (bin)) != bin &&
                (unsigned long) (victim->size) >= (unsigned long) (nb)) {

                //拿到当前 largebin 中最小的 chunk
                victim = victim->bk_nextsize;

                //找到当前 largebin 中第一个 size >= 申请大小 的 chunk
                while (((unsigned long) (size = chunksize (victim)) <
                        (unsigned long) (nb)))
                    victim = victim->bk_nextsize;


                /* Avoid removing the first entry for a size so that the skip
                   list does not have to be rerouted.  */
                // 如果 选中的 chunk 不是 largebin 中的最后一个 chunk
                // 且 选中的大小的 chunk 不止一个,就取这条链上的 head->fd 的元素
                if (victim != last (bin) && victim->size == victim->fd->size)
                    victim = victim->fd;

                // 生成一个 remainder, size 为当前 freed_chunk - real_malloc_size
                remainder_size = size - nb;

                //进行 unlink 操作
                unlink (av, victim, bck, fwd);

                /* Exhaust */
                // 如果生成的 remainder 小于 MINSIZE了, 则会直接返回整个 victim+remainder
                if (remainder_size < MINSIZE)
                {
                    set_inuse_bit_at_offset (victim, size);
                    if (av != &main_arena)
                        victim->size |= NON_MAIN_ARENA;
                }
                /* Split */

                //如果生成的 remainder 能够用, 就给它割下来
                else
                {
                    // 抓出 remainder
                    remainder = chunk_at_offset (victim, nb);

                    /* We cannot assume the unsorted list is empty and therefore
                       have to perform a complete insert here.  */
                    // 拿出 unsortedbin
                    bck = unsorted_chunks (av);
                    // 准备把 remainder 插入到 unsortedbin 的第一个
                    fwd = bck->fd;

                    // 如果当前 unsortedbin 里的第一个 chunk 的 bk 没有指向 unsortedbin
                    // 说明有问题, 报错
                    if (__glibc_unlikely(fwd->bk != bck)) {
                        errstr = "malloc(): corrupted unsorted chunks";
                        goto errout;
                    }

                    // 把 remainder 插到 unsortedbin 的第一个
                    remainder->bk = bck;
                    remainder->fd = fwd;
                    bck->fd = remainder;
                    fwd->bk = remainder;

                    // 如果 remainder 的大小是 largebin 的大小，则将其 fd_nextsize 和 bk_nextsize 置空
                    if (!in_smallbin_range (remainder_size)) {
                        remainder->fd_nextsize = NULL;
                        remainder->bk_nextsize = NULL;
                    }

                    // 给申请的 chunk 设置 head
                    set_head (victim, nb | PREV_INUSE |
                                      (av != &main_arena ? NON_MAIN_ARENA : 0));
                    // 给 remainder 设置 head
                    set_head (remainder, remainder_size | PREV_INUSE);
                    // 把 remainder 后面的 chunk 的 prev_size 设置好
                    set_foot (remainder, remainder_size);
                }

                check_malloced_chunk (av, victim, nb); // Empty
                void *p = chunk2mem (victim); // 指针转到 data
                alloc_perturb(p, bytes); // 假初始化
                return p;
            }
        }

        /*
           Search for a chunk by scanning bins, starting with next largest
           bin. This search is strictly by best-fit; i.e., the smallest
           (with ties going to approximately the least recently used) chunk
           that fits is selected.

           The bitmap avoids needing to check that most blocks are nonempty.
           The particular case of skipping all bins during warm-up phases
           when no chunks have been returned yet is faster than it might look.
         */

        // 到这里, 说明在这个 size 对应的 bin 里找不到了，于是我们要去更高一级的地方找

        // idx升一段
        ++idx;
        //重新拿 bin, block, map, bit
        bin = bin_at (av, idx);
        block = idx2block (idx);
        map = av->binmap[block];
        bit = idx2bit (idx);

        //循环找足够大的 freed chunk
        for (;;) {
            /* Skip rest of block if there are no more set bits in this block.  */
            // 如果当前 map 没有, 就换到下一个 block
            if (bit > map || bit == 0) {

                // 一直找到有的 block, 如果没有就用 top_chunk 分配
                do {
                    if (++block >= BINMAPSIZE) /* out of bins */

                        goto use_top;
                } while ((map = av->binmap[block]) == 0);

                // 拿到相应的 bin
                bin = bin_at (av, (block << BINMAPSHIFT));

                // 对 bit 置位
                bit = 1;
            }

            /* Advance to bin with set bit. There must be one. */

            // 在当前 block 遍历对应的 bin,知道找到其 bit 为 1 的返回
            while ((bit & map) == 0) {
                bin = next_bin (bin);
                bit <<= 1;
                assert (bit != 0);
            }

            /* Inspect the bin. It is likely to be non-empty */
            // 找到对应的 bin 后, 从 bin 的 bk 取出一个 chunk
            victim = last (bin);

            /*  If a false alarm (empty bin), clear the bit. */
            // 如果当前 bin 是空的, 就将对应的 binmap 的 bit 位清空
            // 获取当前 bin 的下一个 bin, bit 也随之移到下一位
            if (victim == bin) {
                av->binmap[block] = map &= ~bit; /* Write through */
                bin = next_bin (bin);
                bit <<= 1;
            }
            // 如果 bin 不是空的, 就在里面拿到 chunk, 完成分割操作
            else {
                //拿当前 chunk 的 size
                size = chunksize (victim);

                //确认当前拿到的 chunk 的 size 位大于需要申请的大小
                /*  We know the first chunk in this bin is big enough to use. */
                assert ((unsigned long) (size) >= (unsigned long) (nb));

                // 计算remainder的大小
                remainder_size = size - nb;

                // 解链
                /* unlink */
                unlink (av, victim, bck, fwd);


                // 分割 remainder操作, 不再次注释

                /* Exhaust */
                if (remainder_size < MINSIZE)
                {
                    set_inuse_bit_at_offset (victim, size);
                    if (av != &main_arena)
                        victim->size |= NON_MAIN_ARENA;
                }
                /* Split */
                else
                {
                    remainder = chunk_at_offset (victim, nb);

                    /* We cannot assume the unsorted list is empty and therefore
                       have to perform a complete insert here.  */
                    bck = unsorted_chunks (av);
                    fwd = bck->fd;
                    if (__glibc_unlikely(fwd->bk != bck)) {
                        errstr = "malloc(): corrupted unsorted chunks 2";
                        goto errout;
                    }
                    remainder->bk = bck;
                    remainder->fd = fwd;
                    bck->fd = remainder;
                    fwd->bk = remainder;

                    /* advertise as last remainder */
                    if (in_smallbin_range (nb))
                        av->last_remainder = remainder;
                    if (!in_smallbin_range (remainder_size)) {
                        remainder->fd_nextsize = NULL;
                        remainder->bk_nextsize = NULL;
                    }
                    set_head (victim, nb | PREV_INUSE |
                                      (av != &main_arena ? NON_MAIN_ARENA : 0));
                    set_head (remainder, remainder_size | PREV_INUSE);
                    set_foot (remainder, remainder_size);
                }
                // 返回其 chunk
                check_malloced_chunk (av, victim, nb);
                void *p = chunk2mem (victim);
                alloc_perturb(p, bytes);
                return p;
            }
        }

        // 使用 top chunk 完成 malloc
        use_top:
        /*
           If large enough, split off the chunk bordering the end of memory
           (held in av->top). Note that this is in accord with the best-fit
           search rule.  In effect, av->top is treated as larger (and thus
           less well fitting) than any other available chunk since it can
           be extended to be as large as necessary (up to system
           limitations).

           We require that av->top always exists (i.e., has size >=
           MINSIZE) after initialization, so if it would otherwise be
           exhausted by current request, it is replenished. (The main
           reason for ensuring it exists is that we may need MINSIZE space
           to put in fenceposts in sysmalloc.)
         */

        //将 top_chunk 地址塞到 victim 里
        victim = av->top;
        //拿取当前 top_chunk 大小
        size = chunksize (victim);

        //如果 top_chunk 足够大
        if ((unsigned long) (size) >= (unsigned long) (nb + MINSIZE))
        {
            // top_chunk 变小, 切出来的 chunk 返回
            remainder_size = size - nb;
            remainder = chunk_at_offset (victim, nb);
            av->top = remainder;
            set_head (victim, nb | PREV_INUSE |
                              (av != &main_arena ? NON_MAIN_ARENA : 0));
            set_head (remainder, remainder_size | PREV_INUSE);

            check_malloced_chunk (av, victim, nb);
            void *p = chunk2mem (victim);
            alloc_perturb(p, bytes);
            return p;
        }

        /* When we are using atomic ops to free fast chunks we can get
           here for all block sizes.  */
        // 到了这里就说明不够大
        // 如果fastbin里有东西
        else if (have_fastchunks (av)) {
            // 进行 consolidate
            malloc_consolidate(av);

            // 根据大小拿对应bin里的chunk
            /* restore original bin index */
            if (in_smallbin_range (nb))
                idx = smallbin_index (nb);
            else
                idx = largebin_index (nb);
        }

            /*
               Otherwise, relay to handle system-dependent cases
             */
        //这里就是 top_chunk 不够大, 且fastbin里没东西了
        else {
            //进行 sysmalloc()
            void *p = sysmalloc(nb, av);
            if (p != NULL)
                alloc_perturb(p, bytes);
            return p;
        }

        // 如果到这里没有完成 malloc, 则直接回去继续循环
    }
}
```

‍

# malloc_consolidate()

```c
static void malloc_consolidate(mstate av) {
    mfastbinptr *fb;                 /* current fastbin being consolidated */
    mfastbinptr *maxfb;              /* last fastbin (for loop control) */
    mchunkptr p;                  /* current chunk being consolidated */
    mchunkptr nextp;              /* next chunk to consolidate */
    mchunkptr unsorted_bin;       /* bin header */
    mchunkptr first_unsorted;     /* chunk to link to */

    /* These have same use as in free() */
    mchunkptr nextchunk;
    INTERNAL_SIZE_T size;
    INTERNAL_SIZE_T nextsize;
    INTERNAL_SIZE_T prevsize;
    int nextinuse;
    mchunkptr bck;
    mchunkptr fwd;

    /*
      If max_fast is 0, we know that av hasn't
      yet been initialized, in which case do so below
    */

    if (get_max_fast () != 0) { // 检测是否已初始化
        //把当前 arena 的 fastbin 符号位设 0
        clear_fastchunks(av);

        //拿到当前 arena 的 unsortedbin
        unsorted_bin = unsorted_chunks(av);


        /*
          Remove each chunk from fast bin and consolidate it, placing it
          then in unsorted bin. Among other reasons for doing this,
          placing in unsorted bin avoids needing to calculate actual bins
          until malloc is sure that chunks aren't immediately going to be
          reused anyway.
        */

        //取出 fastbin 中的最大和最小，准备进行遍历
        maxfb = &fastbin (av, NFASTBINS - 1);
        fb = &fastbin (av, 0);

        do {
            // 拿到当前 fastbin 中的头指针
            p = atomic_exchange_acq(fb, 0);
            /*
             p = ({
                    __typeof(*(fb)) __atg5_oldval;
                    __typeof(fb) __atg5_memp = (fb);
                    __typeof(*(fb)) __atg5_value = (0);
                    do __atg5_oldval = *__atg5_memp;
                    while (__builtin_expect(({
                        __typeof(__atg5_oldval) __atg3_old = (__atg5_oldval);
                        atomic_compare_and_exchange_val_acq(__atg5_memp, __atg5_value, __atg3_old) != __atg3_old;
                    }), 0));
                    __atg5_oldval;
                })
             * */
            if (p != 0) {
                do {
                    check_inuse_chunk(av, p); // 空的一个检查宏

                    nextp = p->fd; // 对当前指定的 chunk 的 fd 进行保存
                    /* Slightly streamlined version of consolidation code in free() */
                    size = p->size & ~(PREV_INUSE | NON_MAIN_ARENA); // 拿到当前 chunk 的 size

                    // 拿到 nextchunk 并计算其 size
                    nextchunk = chunk_at_offset(p, size);
                    nextsize = chunksize(nextchunk);

                    // 如果 选中的堆块的上一个堆块是 free状态 (向前合并)
                    if (!prev_inuse(p)) {
                        //prev_size继承
                        prevsize = p->prev_size;
                        //size相加
                        size += prevsize;
                        //修改指针位置到前一个chunk头处
                        p = chunk_at_offset(p, -((long) prevsize));
                        //进行 unlink 操作
                        unlink(av, p, bck, fwd);
                        /*
                         * 要求 FD->bk = BK->fd = p
                         * */
                        /*
                         * {
                         *      fwd = p->fd;
                         *      bck = p->bk;
                         *      if (__builtin_expect(fwd->bk!=p||bck->fd!=p, 0))
                         *          malloc_printerr(check_action, "corrupted double-linked list", p, av);
                         *      else{
                         *          fwd->bk = bck;
                         *          bck->fd = fwd;
                         *          if (!(
                         *          (unsigned long) (p->size) <
                         *          (unsigned long) ((64 - ((2 * (sizeof(size_t))) > 2 * (sizeof(size_t)))) * (2 * (sizeof(size_t))))
                         *          )
                         *          && __builtin_expect(p->fd_nextsize != NULL, 0)
                         *          ) {
                         *              if (
                         *              __builtin_expect(p->fd_nextsize->bk_nextsize != p, 0) ||
                         *              __builtin_expect(p->bk_nextsize->fd_nextsize != p, 0)
                         *              )
                         *                  malloc_printerr(check_action, "corrupted double-linked list (not small)", p, av);
                         *              if (fwd->fd_nextsize == NULL) {
                         *                  if (p->fd_nextsize == p)
                         *                      fwd->fd_nextsize = fwd->bk_nextsize = fwd;
                         *                  else {
                         *                      fwd->fd_nextsize = p->fd_nextsize;
                         *                      fwd->bk_nextsize = p->bk_nextsize;
                         *                      p->fd_nextsize->bk_nextsize = fwd;
                         *                      p->bk_nextsize->fd_nextsize = fwd;
                         *                  }
                         *              }
                         *              else {
                         *                  p->fd_nextsize->bk_nextsize = p->bk_nextsize;
                         *                  p->bk_nextsize->fd_nextsize = p->fd_nextsize;
                         *              }
                         *          }
                         *      }
                         *  }
                         * */
                    }

                    // nextchunk 如果不是 top chunk
                    if (nextchunk != av->top) {
                        //获取 nextchunk 存储的 prev_inuse
                        nextinuse = inuse_bit_at_offset(nextchunk, nextsize);
                        // 如果确定没在用
                        if (!nextinuse) {
                            //将其合并进来,进行 unlink 操作
                            size += nextsize;
                            unlink(av, nextchunk, bck, fwd);
                        }
                        else
                        //如果 nextchunk 的 prev_inuse 不为 0 ,则将 nextchunk 的 prev_inuse 位设为 0
                            clear_inuse_bit_at_offset(nextchunk, 0);

                        //将 p 放到 unsortedbin 里
                        first_unsorted = unsorted_bin->fd;
                        unsorted_bin->fd = p;
                        first_unsorted->bk = p;

                        // 只要 p 不是 smallbin,就将 fd_nextsize 和 bk_nextsize 清空
                        if (!in_smallbin_range (size)) {
                            p->fd_nextsize = NULL;
                            p->bk_nextsize = NULL;
                        }

                        // 将当前 p chunk 的头设置好
                        set_head(p, size | PREV_INUSE);

                        //完全将 p 放到 unsortedbin 中
                        p->bk = unsorted_bin;
                        p->fd = first_unsorted;

                        //给 nextchunk 写 prev_size
                        set_foot(p, size);
                    }

                    // 如 nextchunk 是 top chunk
                    // 直接将当前chunk与 top chunk 合并
                    else {

                        size += nextsize;
                        set_head(p, size | PREV_INUSE);
                        av->top = p;
                    }
                //直到对当前idx对应的 fastbin 中的每一个 chunk 都进行完 consolidate 后跳出
                } while ((p = nextp) != 0);

            }
        //直到遍历完所有的 fastbin
        } while (fb++ != maxfb);
    }
    // 如果 fastbin 里没有东西 / ptmalloc 没有初始化
    else {
        //对 arena 进行初始化
        malloc_init_state(av);
        check_malloc_state(av); // Empty
    }
}
```
