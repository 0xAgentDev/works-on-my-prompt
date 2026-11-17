# Debrief · Is B better?

## What was wrong

1. **The decision was made on one sample per question.** At 60 questions, the gap between two single passes moves by about 13 points either way from sampling alone. A five-point lead is well inside that.
2. **There was no statement of uncertainty.** The rule compared two percentages and reported the difference as if it were exact.
3. **Only the average was looked at.** A prompt can gain on four slices and collapse on the fifth.

In this week's experiment B is exactly as good as A. On simulated experiments the original rule ships a prompt that is no better 39% of the time, ships one that is 8 points worse 11% of the time, and ships one that loses 30 points on returns 64% of the time. The reference fix: 3%, 0% and 0%, while still shipping a prompt that is 8 points better 99% of the time.

## Why the tests were green

They used differences of 30 points. Any rule gets those right. A decision rule has to be tested where it is hard: no difference, a small difference, a difference hidden in a slice.

## How you know it stays fixed

- The rule is tested on many simulated experiments with a known truth, counting false alarms, misses and how often the interval holds the true value.
- Every prompt comparison reports an estimate, an interval and a per-slice breakdown. A bare percentage is not accepted as a result.

## What a reviewer asks next

**The interval includes zero. What do you tell the product manager?**
That the eval cannot tell B from A, and what the range is: somewhere between four points worse and five better. That is different from "B is the same". The options are a larger eval set, shipping behind a flag and measuring in production, or deciding on cost and latency.

**How many questions would you need to detect a two-point improvement?**
The standard error has to come down to well under one point. With ten trials per question it is about 2.4 points at 60 questions, and it shrinks with the square root of the number of questions, so you would need several hundred. More trials on the same 60 questions stop helping once sampling noise is gone, because the questions themselves are a sample of what users ask.

**Why take the difference per question, and not compare two overall scores?**
Questions differ in difficulty, and both prompts face the same ones. Differencing per question removes that shared difficulty from the noise. It matters most when answers are deterministic and both prompts tend to fail the same hard questions.

**Five slices, each tested on its own. What is the catch?**
The more slices you test, the more often one looks bad by chance. Here a false alarm only delays a launch, which is the cheap mistake. With dozens of slices, tighten the per-slice threshold or the rule will never ship anything.

**Would temperature zero make this problem go away?**
It removes sampling noise within a question. It does not change the fact that 60 questions are a small sample of production traffic, so the interval across questions stays.
