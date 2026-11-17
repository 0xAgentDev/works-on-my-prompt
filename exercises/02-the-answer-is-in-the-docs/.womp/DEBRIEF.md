# Debrief · The answer is in the docs

## What was wrong

Four things, and the last one hid the other three.

1. **Chunks cut sentences in half.** Fixed 220-character chunks split 15 of the handbook's 50 sentences. A fact that straddles a cut can never be retrieved whole.
2. **Matching was on raw words.** `"vpn"` did not match `"VPN"`, `"laptops?"` did not match `"Laptops"`, and "the" counted as much as "parental". Typed the way staff type, most questions pulled in chunks that shared only filler words.
3. **The prompt had no way out.** With the answer missing, the model was never told what to do, so it answered anyway: with a nearby number when one was in the excerpts, otherwise with an invention.
4. **The eval was written from the handbook.** Its questions reuse the handbook's exact words, so they retrieved perfectly and scored 100% while real questions failed.

On the held-out questions the original system answers 3 of 16 correctly and makes something up 17 times in 20. The reference fix answers 16 of 16 and makes nothing up.

## Why the tests were green

The only quality test was the offline eval, and it measured how well the system finds sentences when you quote them back to it. It contained no question a user had typed and none that the handbook cannot answer.

## How you know it stays fixed

- An eval built from real questions, split into answerable ones, near-misses (two similar facts with different numbers) and ones the handbook does not cover. The last group is the only way to see made-up answers.
- Retrieval measured separately from answers. "Was the right sentence retrieved?" tells you which half to fix.
- In production: how often Hank declines, and a weekly sample of answers read against the handbook by a person.

## What a reviewer asks next

**Word matching was enough here. When does it stop being enough?**
When the user's words and the document's words differ: "food" for "meals", "PTO" for "paid time off", a question in another language. That is where embeddings, hybrid search or rewriting the query earn their cost. Measure recall first; without that number you cannot tell whether the extra machinery helped.

**Why not bigger chunks, or more of them?**
Every extra token costs money and latency, and near-duplicate facts in the same prompt ("16 weeks" next to "6 weeks") are how the model picks the wrong one. The useful curve is recall against prompt size.

**Does "say you don't know" stop made-up answers?**
It lowers them; it does not prove anything. Unanswerable questions in the eval measure it. For higher stakes, have the model quote the sentence it relied on and check that the quote exists in the retrieved text.

**Who should write the eval set?**
Not the person who built the retriever, and not from the documents. Start from logs and complaints, keep a part of it held out, and add every new failure to it.
