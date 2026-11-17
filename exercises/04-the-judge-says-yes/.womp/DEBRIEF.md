# Debrief · The judge says yes

## What was wrong

1. **The reference never reached the judge.** The code read `example.get("reference_answer", "")`, and the field is called `reference`. The default hid the mismatch, so the judge graded how each answer sounded. Fluent wrong answers passed.
2. **A 1 to 10 scale with a threshold of 5.** The judge avoids low scores: an answer it thinks is bad gets 4, 5 or 6, and two of those three clear the bar.
3. **Unreadable replies counted as a pass.** "No number in the reply: do not punish the answer for it."
4. **Nobody had measured the judge.** A pass rate says how often the judge says yes. It says nothing about how often the judge is right.

On the 60 labelled answers the original judge failed 2 of the 21 that people marked wrong (TNR 0.10). The reference fix fails 20 of 21 (TNR 0.95) and passes 37 of the 39 that people marked right (TPR 0.95). On the 80 held-out answers it scores TPR 0.94 and TNR 0.96.

## Why the tests were green

There was a test that a correct answer passes. There was no test that a wrong answer fails, which is the only thing a judge is for.

## How you know it stays fixed

- Agreement with human labels is a tracked number, TPR and TNR separately, on a labelled set that is kept apart from the one used to tune the prompt.
- A sample is re-labelled whenever the judge prompt or the judge model changes. A judge is a model too, and it drifts.
- The share of unreadable replies is a metric with an alert on it.

## What a reviewer asks next

**Why TPR and TNR, and not accuracy?**
Because most answers are fine. Here a judge that passes everything is 65% "accurate". The two kinds of error also cost different things: a false pass hides a bad answer from you, a false fail wastes a reviewer's time. Kappa puts both into one number that is zero for a judge that ignores the answer.

**The fixed judge is still wrong about one time in twenty. What do you do with that?**
Report it. With measured TPR and TNR you can correct the dashboard figure: true pass rate = (observed + TNR - 1) / (TPR + TNR - 1). Send borderline or high-stakes cases to people, and never present the judge's pass rate as ground truth.

**Sixty labels. Is that enough?**
Enough to see that a judge is broken. With 21 negative examples, the uncertainty on TNR is roughly plus or minus 0.1, so not enough to tune to the second decimal. Label more of what matters most, which is usually the failures.

**When should you not use an LLM judge at all?**
When code can check it: a number, a field, a format, a citation that has to exist. That is cheaper and repeatable. It does not work here because right answers come in many wordings: checking whether the reference text appears in the answer passes only 72% of the answers people marked right.

**Why PASS or FAIL and not a score?**
Scores bunch up in the middle and the threshold becomes a guess. Human labels here are binary, so a binary verdict can be compared with them directly. If you do need grades, define what each one means and measure each boundary.
