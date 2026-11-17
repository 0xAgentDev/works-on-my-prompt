# 02 · The answer is in the docs

**Channel:** #helpdesk-bot  **Severity:** SEV-2 (staff are acting on wrong answers)

> **People team:** Someone asked Hank how much parental leave a primary caregiver gets, and it answered with the notice period for booking holidays. It also told a colleague that we offer pet insurance. We do not. The handbook is right and Hank is wrong, and people are making plans based on what it says.

## What you know

- Hank answers staff questions from the handbook (`data/handbook.md`). It splits the handbook into chunks, retrieves a few for each question and asks the model to answer from them.
- The offline eval (`data/eval_questions.jsonl`) scores 100%, and the test suite passes.
- This week's complaints are in `data/user_reports.jsonl`, next to what the handbook actually says.
- The model is small. It rejects prompts over 240 tokens, so the whole handbook does not fit. How it behaves is described in `harness/llm.py`.

## See it

    python3 run.py

## Your job

Make Hank answer from the handbook, and say so when the handbook has no answer. Change `app/rag.py`.

Keep these three functions and their signatures:

- `build_index(handbook)` returns whatever your retriever needs
- `retrieve(question, index)` returns the chunks, as strings, that go into the prompt
- `answer(question, index, model)` returns Hank's reply

Put the user's question into the prompt exactly as it was asked. The simulated model needs that to know what it is being asked.

## How it is graded

| Points | Criterion |
|---|---|
| 35 | Held-out questions are answered correctly |
| 20 | Nothing is made up, even when the handbook is silent |
| 20 | Retrieval returns the passage that holds the answer |
| 15 | Every prompt fits the model's context |
| 10 | Your tests pass on the fix and fail on the original |

85 points fixes it. The held-out questions are typed the way staff type them, and several ask about things the handbook does not cover.
