# Hints · The judge says yes

## Measure before you fix
You cannot tell how wrong the judge is until you compare it with the labels. Write `agreement()` first; `run.py` prints it as soon as it exists. Then look at TNR: of the answers people failed, how many did the judge fail?

## What does the judge actually see?
Print the prompt for one answer that people marked wrong. Read the "Reference answer:" line, then look at the keys of the example.

## A score of 6 is not a pass
The model avoids low scores. An answer it thinks is bad gets 4 to 6, and `PASS_SCORE` is 5. Either choose the threshold from the labelled answers, or stop asking for a number and ask for PASS or FAIL.

## Read the verdict, not the whole reply
If you ask for PASS or FAIL, check in `harness/llm.py` how a FAIL is worded. Searching the reply for the word "pass" finds it in "does not pass".

## When the judge says nothing useful
Some replies contain no verdict at all. Today those count as a pass, with a comment about not punishing the answer. Decide what an unreadable verdict is worth, and make sure it can never be a pass.
