---
name: write-wp
description: Write Chinese CTF and pwn writeups in the user's personal SiYuan-derived style. Use when Codex needs to turn exploit notes, GDB or IDA observations, screenshots, challenge artifacts, or solved题思路 into a polished writeup, WP, or blog post that sounds like the user. Especially appropriate for pwn, heap, stack-pivot, exploit-reasoning, technique blog, and challenge复盘 tasks, including requests like "写成 WP", "按我的风格整理题解", or "根据笔记写博客".
---

# Write-WP

## Overview

Write like the user's SiYuan notes and exported markdown:

- explain why the exploit works, not only what the final payload is
- keep the article in natural Chinese blog tone instead of contest-report jargon
- make magic numbers, offsets, pivots, and heap shapes explainable
- use section names that feel handwritten and technical, not corporate

Read [references/style-signals.md](references/style-signals.md) before drafting when tone matching or section choice matters.
Read [references/sample-library/index.md](references/sample-library/index.md) first when you need the full corpus map, then open only the sample markdown files that are closest to the current writing task.
Treat the source notes as belonging to one of four maturity levels: scratch proof, challenge note, knowledge note, or finished blog. Match the output to the source maturity instead of forcing everything into one template.
This skill uses two layers of corpus:

- primary writing-style corpus: `待发表 Blog`, `Blogs`, and `DailyNote`
- expanded concept corpus: `Study -> Heap / Stack / Kernel` imported from `Study.md.zip`

## Workflow

1. Classify the source material.
2. Choose the article mode.
3. Gather the observable evidence.
4. Build the narrative around the key questions.
5. Place code after the reader can follow it.
6. Polish into the user's tone.

## 0. Classify The Source Material

Use the lightest useful abstraction.

- `scratch proof`: daily-note fragments, local reasoning, or headings like `Why it can UAF?`
- `article draft`: already organized article drafts from `待发表 Blog`
- `knowledge note`: topic-oriented pages such as `Unlink`, `简单堆利用`, `RC4`
- `finished blog`: near-publishable drafts such as `O2优化下的栈迁移`

When the source is still a scratch proof, preserve the local reasoning chain before you polish it. Do not delete the exploratory feeling if it is what makes the logic convincing.

## 1. Choose The Article Mode

Default to the lightest structure that still teaches the core idea.

### `challenge-mini`

Use for short solved题, quick复盘, or notes where the exploit is the main value.

Suggested shape:

~~~md
# 题目名

## 信息搜集
...

## 漏洞
...

## Exp.py
```python
...
```
~~~

### `challenge-blog`

Use for richer pwn writeups with debugger reasoning, screenshots, exploit evolution, or reader-facing teaching value. This is the default mode.

Suggested shape:

~~~md
# 题目/主题名

## 前言
...

## 对其代码的简单复现
...

## 信息搜集
...

## 利用代码
...

## 对利用代码的疑问
### Q1
...
### Q2
...

## 结语
...
~~~

Section names can drift when useful. Names like `类似构造题目`, `对偏移错误显示的理解`, `利用思路`, `TGCTF 2025 Overflow` all fit this house style if they serve the narrative.

### `knowledge-note`

Use for technique summaries or study notes rather than one exact challenge.

Suggested shape:

~~~md
# 知识点名

## 前言
...

## 背景/结构
...

## 关键技术点
...

## 利用思路
...

## 例题
...
~~~

`结语` is optional here.

### `scratch-proof`

Use when the source looks like a daily learning note or a local proof of one question, especially notes shaped like `Why it can ...`.

Suggested shape:

~~~md
# 题目/问题名

## 现象
...

## 为什么会这样
...

## 关键例子
```c
...
```

## 结论 / 利用点
...
~~~

This mode can also stay close to the original headings if those headings are already good. For example, keeping `145 Why it can UAF?` is better than replacing it with an overly polished title.

### `operation-guide`

Use when the target output is adjacent to a writeup but is really a step-by-step technical article, environment note, or deployment walkthrough.

Suggested shape:

~~~md
# 主题名

## 前言
...

## 确定信息 / 信息搜集
...

## 更改配置 / 操作步骤
...

## 验证结果
...
~~~

Borrow this shape only when the material is operational. Do not let it flatten a pwn writeup into a generic tutorial.

## 2. Gather The Observable Evidence

Prefer concrete material:

- binary behavior
- source or decompiled code
- GDB or IDA observations
- heap or stack layout notes
- screenshots and memory maps
- failed payloads
- final exploit script
- external references worth crediting

Do not invent screenshots, debugger output, or source code that you do not have. If something is inferred, say so plainly and keep the reasoning close to the claim.

## 3. Build The Narrative Around Questions

The user's stronger writeups revolve around answering non-obvious questions. For each critical step, try to answer one of these:

- why this bug exists
- why this primitive is enough
- why this exact offset, size, or gadget is chosen
- why a naive attempt fails
- why the debugger view differs from the static view

If a magic constant matters, explain it in prose near the code. Good examples are questions like:

- why is the offset `0x80` instead of what IDA shows
- why is it `bss_addr + 4`
- why add `0x700`
- why allocate twice

If the notes already contain one strong question, let that question drive the section. A local daily note like `Why it can UAF?` can later become either:

- a standalone mini-article
- one subsection inside `对利用代码的疑问`
- one proof block inside a longer challenge blog

## 4. Place Code After The Reader Can Follow It

- Prefer to establish the bug and primitive before dropping the full exploit.
- If there is both a bare-minimum script and a personal full template, show the short one first.
- Use `Exp.py` as the heading when the script is central to the article.
- Keep comments in the exploit where they teach the attack chain or important stack or heap layout.

## 5. Polish Into The User's Tone

Write in concise, natural Chinese. Common transitions in this style include:

- `我们首先`
- `我们可以看到`
- `接下来`
- `这里就能`
- `因而`
- `那么`
- `这时`
- `但明显发现`
- `简单地`

Useful local-closing sentences include:

- `这就是初步的...`
- `那么我们就得到了...`
- `因而我们就有这样的解决方法`

Allow some casual tone, but keep the technical chain tight. Avoid generic AI phrasing like mechanically stacking `首先/其次/最后` without real need.
Light playful phrasing is acceptable when it sounds like the user, but use it sparingly and only after the technical point lands.

## House Rules

- Prefer headings such as `前言`, `信息搜集`, `漏洞`, `利用思路`, `利用代码`, `对利用代码的疑问`, `结语`.
- Keep paragraphs short and let images or code blocks break the pace.
- When a failed path teaches something, keep it instead of erasing it.
- Introduce screenshots by telling the reader what to notice before or after the image.
- Credit sources inline when you used ctf-wiki, Bilibili, GitHub, or another blog.
- If the source is a knowledge note, allow direct explanatory headings like `RC4算法`, `初始化S表 KSA`, `生成密钥流 PRGA`.
- If the source is a homepage or index page, borrow its navigation intent only when the user actually wants an index-like output.
- Do not over-standardize into `Abstract`, `Methodology`, `Results`, `Conclusion` unless the user explicitly asks.
- Do not flatten the whole article into bullet points if paragraphs teach better.

## When Material Is Incomplete

- If you only have exploit code and a few notes, choose `challenge-mini`.
- If you have daily-note style reasoning, choose `scratch-proof` first and only upgrade to `challenge-blog` if there is enough context.
- If you have screenshots and exploit notes but no full source, focus on observable behavior and mark inferences clearly.
- If there are unresolved uncertainties, surface them as `疑问` or `还需要确认的点` instead of pretending certainty.

## Optional Blog Metadata

If the user explicitly asks for a blog-ready export, add simple metadata such as title, created time, updated time, slug, and tags. Otherwise focus on the article body first.

## Output Checklist

- the title is direct and topic-led
- the chosen section names fit the amount of material
- the bug mechanism is stated clearly
- the exploit appears in a runnable-looking block
- every teaching-critical magic number is explained
- the final tone reads like a real Chinese technical blog written by the user
