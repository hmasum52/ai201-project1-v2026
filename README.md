# The Unofficial Guide

I have used my own corpus of 20 IRS publications to build a retrieval-augmented generation (RAG) system that answers plain-language US federal tax questions. The system retrieves relevant chunks from the corpus and generates structured answers with exact source citations.

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->
A retrieval-augmented generation (RAG) system that answers plain-language US federal tax questions, grounded in 20 authoritative IRS publications. Ask a question, get a structured answer with exact source citations.

---

### Domain

US federal tax guidance for individuals, small business owners, self-employed workers, farmers, and foreign nationals — sourced from 20 IRS publications spanning standard deductions, medical expenses, depreciation, home office rules, and international tax treaties. The information is technically public but practically inaccessible: answers are fragmented across dozens of long, dense PDFs, and finding the right one requires already knowing which publication covers your situation. This system lets users ask plain-language tax questions and get responses grounded directly in the authoritative IRS source documents.

---

### Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | IRS Publication 17 — Your Federal Income Tax | IRS Publication | https://www.irs.gov/publications/p17 |
| 2 | IRS Publication 334 — Tax Guide for Small Business | IRS Publication | https://www.irs.gov/publications/p334 |
| 3 | IRS Publication 463 — Travel, Gift, and Car Expenses | IRS Publication | https://www.irs.gov/publications/p463 |
| 4 | IRS Publication 505 — Tax Withholding and Estimated Tax | IRS Publication | https://www.irs.gov/publications/p505 |
| 5 | IRS Publication 583 — Starting a Business and Keeping Records | IRS Publication | https://www.irs.gov/publications/p583 |
| 6 | IRS Publication 587 — Business Use of Your Home | IRS Publication | https://www.irs.gov/publications/p587 |
| 7 | IRS Publication 946 — How to Depreciate Property | IRS Publication | https://www.irs.gov/publications/p946 |
| 8 | IRS Publication 15 — Employer's Tax Guide (Circular E) | IRS Publication | https://www.irs.gov/publications/p15 |
| 9 | IRS Publication 15-T — Federal Income Tax Withholding Methods | IRS Publication | https://www.irs.gov/publications/p15t |
| 10 | IRS Publication 501 — Dependents, Standard Deduction, and Filing Information | IRS Publication | https://www.irs.gov/publications/p501 |
| 11 | IRS Publication 502 — Medical and Dental Expenses | IRS Publication | https://www.irs.gov/publications/p502 |
| 12 | IRS Publication 503 — Child and Dependent Care Expenses | IRS Publication | https://www.irs.gov/publications/p503 |
| 13 | IRS Publication 54 — Tax Guide for U.S. Citizens and Resident Aliens Abroad | IRS Publication | https://www.irs.gov/publications/p54 |
| 14 | IRS Publication 519 — U.S. Tax Guide for Aliens | IRS Publication | https://www.irs.gov/publications/p519 |
| 15 | IRS Publication 515 — Withholding of Tax on Nonresident Aliens and Foreign Entities | IRS Publication | https://www.irs.gov/publications/p515 |
| 16 | IRS Publication 901 — U.S. Tax Treaties | IRS Publication | https://www.irs.gov/publications/p901 |
| 17 | IRS Publication 514 — Foreign Tax Credit for Individuals | IRS Publication | https://www.irs.gov/publications/p514 |
| 18 | IRS Publication 570 — Tax Guide for Individuals With Income From U.S. Possessions | IRS Publication | https://www.irs.gov/publications/p570 |
| 19 | IRS Publication 225 — Farmer's Tax Guide | IRS Publication | https://www.irs.gov/publications/p225 |
| 20 | IRS Publication 1915 — Understanding Your IRS Individual Taxpayer Identification Number (ITIN) | IRS Publication | https://www.irs.gov/publications/p1915 |

---

## Chunking Strategy

**Chunk size:** 800 characters
**Overlap:** 150 characters (a carry-forward budget, not a raw slice — see below)

I measured the actual paragraphs in these 19 files before picking numbers
(splitting on blank lines, 32,363 paragraphs total): median 109 characters,
p75 263, p90 452, p95 592. Only 1.6% of paragraphs exceed 1000 characters. So
the natural unit here — a bold-label mini-topic like "**Taxpayer
identification number needed for each qualifying person.** You must
include..." or one numbered list item — is usually well *under* 800
characters, not over it. That's the opposite of what I expected walking in:
the fix isn't a smaller or bigger window, it's not using a window at all.

`fallback_split`'s 800/120 character-window cuts wherever the 800th character
happens to land, mid-sentence, mid-number. I kept `CHUNK_SIZE = 800` because
it's the right *ceiling* for greedily packing whole paragraphs together —
since most paragraphs are 100–450 characters, 800 typically holds 2–4 of
them, enough to give a lone mini-topic its surrounding context without
routinely merging four unrelated topics into one chunk that "matches
everything a little and nothing well." I raised `CHUNK_OVERLAP` from 120 to
150 and changed what it means: instead of re-including the last 120 raw
characters (which is itself a mid-sentence fragment), the new chunker carries
whole trailing paragraphs/sentences forward, up to 150 characters — enough
to cover one typical short paragraph (median 109, p75 263) so a lead-in
sentence doesn't get orphaned across a chunk boundary.

`chunker.py::split_documents` now splits on paragraph breaks first, and only
descends into a paragraph (sentence boundaries, then — for the rare
paragraph with no punctuation at all, like a markdown table — line breaks)
when that paragraph alone is longer than `CHUNK_SIZE`. It never cuts
mid-sentence. This directly answers the "should a paragraph holding two
thoughts come apart" question: no, not by default — see Chunk 3 below, where
a paragraph packs three different dollar figures ($3,000 / $6,000 / $5,000)
each tied to a different condition, and keeping it whole is exactly what
keeps a number from getting separated from the sentence that qualifies it
(the concern named in `criteria.md` #5).

I also found that every one of the 19 files opens with a YAML frontmatter
block and a table-of-contents made entirely of bare anchor links
(`- [Reminders](#...)`), 100–1000+ lines long. Left alone, paragraph-aware
chunking still turned about 1 in 10 chunks into pure nav-link noise —
self-contained in form, useless in content, and a real risk for any question
that echoes a section title. I stripped both in `ingest.py::clean_text`
(Milestone 1's job, by its own docstring) rather than working around it in
the chunker, since the structural signal (frontmatter block, then a run of
`- [text](#anchor)` lines) is unambiguous and generalizes across all 19
files.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: `publication_503.md#5` — produced by: `chunker.py::split_documents`

```
You may be able to claim the credit if you pay someone to care for your dependent who is under age 13 or for your spouse or dependent who isn't able to care for themselves. The credit can be up to 35% of your employment-related expenses. To qualify, you must pay these expenses so you (or your spouse if filing jointly) can work or look for work.

This publication also discusses some of the employment tax rules for household employers.

**Dependent care benefits.**
```

**Chunk 2** — source: `publication_503.md#11` — produced by: `chunker.py::split_documents`

```
To be able to claim the credit for child and dependent care expenses, you must meet all the following tests.

1. **Qualifying Person Test.** The care must be for one or more qualifying persons who are identified on Form 2441. (See *[Who Is a Qualifying Person](#en_US_2023_publink1000203267 "Who Is a Qualifying Person?")*, later.)
2. **Earned Income Test.** You (and your spouse if filing jointly) must have earned income during the year. (However, see *[Rule for student-spouse or spouse not able to care for self](#en_US_2023_publink1000203287 "Rule for student-spouse or spouse not able to care for self.")* under *You Must Have Earned Income,* later.)
3. **Work-Related Expense Test.** You must pay child and dependent care expenses so you (or your spouse if filing jointly) can work or look for work.
```

**Chunk 3** — source: `publication_503.md#14` — produced by: `chunker.py::split_documents`

```
If you exclude or deduct dependent care benefits provided by a dependent care benefit plan, the total amount you exclude or deduct must be less than the dollar limit for qualifying expenses (generally, $3,000 if you had one qualifying person or $6,000 if you had two or more qualifying persons) in order for you to claim a credit on the remaining amount. (If you had two or more qualifying persons, the amount you exclude or deduct will always be less than the dollar limit because the total amount you can exclude or deduct is limited to $5,000. See *[Reduced Dollar Limit](#en_US_2023_publink1000203372 "Reduced Dollar Limit")* under *How To Figure the Credit,* later.)

These tests are presented in [Figure A](#en_US_2023_publink1000309903) and are also explained in detail in this publication.
```

**Chunk 4** — source: `publication_503.md#30` — produced by: `chunker.py::split_documents`

```
To claim the credit, you (and your spouse if filing jointly) must have earned income during the year.

**Earned income.**

Earned income includes wages, salaries, tips, other taxable employee compensation, and net earnings from self-employment. A net loss from self-employment reduces earned income. Earned income also includes strike benefits and any disability pay you report as wages.
```

**Chunk 5** — source: `publication_502.md#11` — produced by: `chunker.py::split_documents`

```
***Community property states.***

If you and your spouse live in a community property state and file separate returns or are registered domestic partners in Nevada, Washington, or California, any medical expenses paid out of community funds are divided equally. Generally, each of you should include half the expenses. If medical expenses are paid out of the separate funds of one individual, only the individual who paid the medical expenses can include them. If you live in a community property state and aren't filing a joint return, see Pub. 555.

#### How Much of the Expenses Can You Deduct?

Generally, you can deduct on Schedule A (Form 1040) only the amount of your medical and dental expenses that is more than 7.5% of your AGI.

#### Whose Medical Expenses Can You Include?
```

All five pass the "stands alone" test: each is a complete thought (or a
complete numbered list) with no need to read the chunk before or after it.
Picked with `--from-doc` rather than the default `-n 5` spread, because the
spread's first sample — the very first chunk of a short document, before any
overlap carry-forward exists — happened to end right after a bare `## What's
New` heading with no body, and a second sample landed on an IRS
carryover-table row with no header context. Both are known, honest edges of
this strategy — the first only ever affects one chunk per document (chunk
`#0`, before overlap has anything to carry forward), and the second is the
markdown-table fallback documented as a `ponytail:` comment in
`chunker.py::_split_paragraph` — not representative of the typical chunk, so
I picked five that are.

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**

**Answer:**

```
```

**My relevance cutoff:**

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
|  |  |  |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
