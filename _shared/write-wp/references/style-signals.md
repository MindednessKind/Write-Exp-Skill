# Source Style Signals

This revision uses a two-layer corpus:

- primary writing-style corpus:
  - `待发表 Blog`
  - `Blogs`
  - `DailyNote`
- expanded concept corpus:
  - `Study -> Heap`
  - `Study -> Stack`
  - `Study -> Kernel` from `Study.md.zip` (the source export spells this subtree as `Kenel`)

Earlier non-sample references remain removed.

## Effective Corpus In Practice

From the checked local workspace, these trees contribute the following article-bearing material:

### `待发表 Blog`

- `O2优化下的栈迁移`
- `简单堆利用`
- `为Ubuntu系统设置静态IP`
- conflict copies of the same drafts

### `Blogs`

- `RC4`
- `Unlink`
- `CTF动态flag构建`
- homepage pages such as `主页`

### `DailyNote`

- `15日`
- `20日`
- conflict copies of `20日`

When duplicate conflict copies exist, treat them as low-signal repetitions, not independent style evidence.

## What Each Tree Contributes

### `待发表 Blog`

This tree provides the most publishable article shapes.

- `O2优化下的栈迁移`
  - long exploit blog
  - uses `前言`, setup or reproduction, exploit code, question-driven clarification, and `结语`
  - explains offsets and odd constants carefully
- `简单堆利用`
  - pwn knowledge note with article polish
  - opens with `前言`, then background sections, then `利用思路`
  - cites learning references inline
- `为Ubuntu系统设置静态IP`
  - operational technical article
  - uses `前言 -> 确定IP -> 更改配置`

### `Blogs`

This tree provides knowledge-note structure.

- `Unlink`
  - concept-first explanation
  - mixes definition, source macro, tips, and exploit significance
- `RC4`
  - algorithm note
  - decomposes the topic into named stages and then gives final encapsulated code
- `CTF动态flag构建`
  - compact technical note
  - useful for how the user records a short engineering idea without over-expanding it
- `主页`
  - index or framing page
  - useful only for understanding navigation tone, not as the main article voice

### `DailyNote`

This tree provides scratch reasoning and proof style.

- `15日`
  - daily proof note
  - explains `Why it can UAF?` with concrete malloc examples and direct conclusions
- `20日`
  - sparse seed note
  - shows that some source material is only a title plus one line, and should not be over-polished into a fake full article

### `Study`

This imported tree is large and concept-heavy. It is better for terminology, section naming, and topic decomposition than for final article voice.

- `Heap`
  - a large corpus of heap internals, ptmalloc2, IO FILE, bins, house-of series, unlink, and source analysis
- `Stack`
  - a compact corpus focused on ROP, SROP, ret2syscall, ret2dlresolve, canary, and stack-distributed exploit topics
- `Kernel`
  - currently small in volume, but useful as a reserved topic bucket for future kernel-style writing

## Structural Archetypes

### 1. Finished exploit blog

Best represented by `O2优化下的栈迁移`.

Common shape:

- `前言`
- setup, reproduction, or problem restatement
- exploit reasoning
- exploit code
- one or more question-driven clarification sections
- `结语`

### 2. Article-grade knowledge note

Best represented by `简单堆利用`.

Common shape:

- `前言`
- background sections
- concept sections
- `利用思路`

This is more article-like than a raw study memo.

### 3. Concept note

Best represented by `Unlink` and `RC4`.

Common shape:

- direct technical heading
- staged explanation
- supporting code or pseudo-code
- optional tips or caveats

The note can skip `前言` if the concept heading is already doing enough work.

The imported `Study` corpus strengthens this archetype, especially for Heap and Stack topics.

### 4. Scratch proof

Best represented by `15日`.

Common shape:

- one concrete question
- very small examples
- direct address or code snippets
- one crisp local conclusion such as `这就是初步的UAF漏洞`

### 5. Operational article

Best represented by `为Ubuntu系统设置静态IP`.

Common shape:

- `前言`
- information gathering
- step-by-step action
- verification

### 6. Seed note

Best represented by `20日`.

Common shape:

- one short context line
- one heading or target topic

Use this as a seed for future drafting, not as proof that every output should stay tiny.

## Shared Structural Moves

- Observe something concrete first, then draw a conclusion.
- Explain at least one "why is this exact number chosen" question when the exploit needs it.
- Use small examples and exact addresses when they teach the mechanism.
- Drop the final exploit only after the primitive is understandable.
- End local reasoning blocks with a crisp takeaway sentence.
- Keep paragraphs short.

## Preferred Heading Lexicon

- `前言`
- `信息搜集`
- `漏洞`
- `利用思路`
- `利用代码`
- `对利用代码的疑问`
- `结语`

Also natural in this sample pool:

- `确定IP`
- `更改配置`
- `RC4算法`
- `初始化S表 KSA`
- `生成密钥流 PRGA`

## Tone Signals

- conversational Chinese, not stiff formal prose
- frequent `我们首先 / 我们可以看到 / 接下来 / 这里 / 因而 / 那么 / 这时`
- short paragraphs
- question-led explanation is natural
- a little casual phrasing is acceptable after the technical point lands
- likes closing a section with a local answer instead of a broad abstract summary

## Weighting Rules

- Weight `待发表 Blog` highest for polished article shape.
- Weight `Blogs` highest for concept-note structure.
- Weight `DailyNote` highest for scratch reasoning and proof cadence.
- Weight `Study` highest for topic vocabulary, concept granularity, and section decomposition inside Heap and Stack writing.
- Weight homepage and conflict copies low.

## What To Carry Into Writeups

- question-led subheadings are good, especially for offsets and exploit details
- concrete addresses and small examples are part of the teaching style, not noise
- references can be thanked or cited inline without becoming a bibliography wall
- sparse source notes should stay honest about how much is known
- imported Study pages can provide technical scaffolding even when they are not ideal tone references

## Anti-Patterns

- sterile competition-report tone
- unexplained magic constants
- dropping a final payload with no reasoning chain
- generic AI summaries detached from the exploit process
- forcing every note into one fixed blog template
