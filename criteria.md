# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** I set this at 4 of 5, not 5, because `chunker.py::fallback_split`'s fixed 800-character window has no sentence awareness and could split an answer across a chunk boundary in one of `irs_tax`'s larger publications (up to 1.2MB). I didn't go lower because each question targets a narrow, distinctively-worded figure that embedding search should still surface reliably.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** `build_prompt` labels every retrieved chunk `[from {source}]`, and the grounding instruction only asks the model to copy that label back, not compute anything — the easiest instruction-following task in this pipeline. Nothing validates it in code, so I'm holding it to 5 of 5: a miss would be a prompt bug, not an acceptable failure rate.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** My Milestone 4 distance measurements showed an overlapping, fuzzy boundary rather than a clean gap, so wherever I set the threshold, some borderline questions will land on the wrong side — that's why it's 4 of 5, not 5. I still expect 4 because the overlap is narrow; most out-of-scope questions (capital of Mongolia, changing motor oil) sit far outside it.

---

## 4. Chunks don't cut sentences in half

In a random sample of 10 chunks from `irs_tax`, at least 8 end in `.`, `?`,
`!`, or a heading's closing colon, not mid-sentence.

**Why this target:** `chunker.py::fallback_split` cuts on a fixed 800-character window with 120 characters of overlap and no sentence awareness. That worked fine on the shorter, flatter corpora it was built for, but `irs_tax` docs run up to 1.2MB with deep nested headings, so I expect more mid-sentence cuts here. I set 8 of 10 instead of 10 of 10 because some cutting is inevitable with this splitter. Zero cuts would mean I got lucky, not that it works.

---

## 5. Numbers in answers match the source

For all 5 questions in `QUESTIONS` (questions.py), the number in the system's answer (dollar amount, percentage, mileage rate) exactly matches the source document. 5 of 5, not 4 of 5.

**Why this target:** A chunk boundary can separate a figure from the context that qualifies it, or pull in a different number from elsewhere in the same publication. Stating a wrong tax figure with confidence is worse than refusing to answer, and it's the failure that would embarrass me most in a demo. I'm holding this to 5 of 5 because a wrong number has no partial credit. 4 of 5 here is one confident lie.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
