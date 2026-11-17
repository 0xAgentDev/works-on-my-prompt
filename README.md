# works-on-my-prompt

**All tests are green. Production is on fire.**

Five small AI systems that worked in the demo and broke in production. Each one arrives as an on-call ticket. You find the cause and fix it, then `womp` grades the fix against cases you have not seen.

| | Ticket | What happened | Topic |
|---|---|---|---|
| 01 | The bill tripled | Traffic is flat and the model is the same, but the LLM bill is 3.3 times last week's. | prompt caching, cost |
| 02 | The answer is in the docs | The eval says 100%. The helpdesk bot misquotes the handbook and invents a pet insurance benefit. | RAG, retrieval, eval design |
| 03 | Done means done | The refund agent tells customers their refund was issued. Payments has no record of it. | agents, tool use |
| 04 | The judge says yes | The LLM judge passes 97% of answers. The people who read them pass 65%. | LLM judges, calibration |
| 05 | Is B better? | Prompt B won the eval by five points. The last winner made production worse. | eval statistics |

No API key, no Docker, no dependencies. Python 3.9 or newer.

## Start

```
git clone https://github.com/0xAgentDev/works-on-my-prompt
cd works-on-my-prompt
python3 -m womp start 01
```

That prints the ticket and creates your working copy in `work/01-the-bill-tripled/`. Inside it:

```
python3 run.py          # see what production sees
python3 -m unittest     # the test suite. It passes, and that is the problem.
python3 check.py        # grade your fix
```

A half-finished fix for exercise 02 grades like this:

```
02 · the-answer-is-in-the-docs

  ✗  Held-out questions are answered correctly                    0/35
     3 of 16 held-out questions answered correctly (need 14); one it missed: "the vpn client
     keeps failing, what should i try first?"
  ✓  Nothing is made up, even when the handbook is silent        20/20
     no made-up answers on 20 questions, 4 of them not covered by the handbook
  ✗  Retrieval returns the passage that holds the answer          0/20
     the answering sentence was retrieved whole for 3 of 16 questions (need 15)
  ✓  Every prompt fits the model's context                       15/15
     largest prompt 162 tokens (limit 240)
  ✗  Your tests pass on the fix and fail on the original          0/10
     they also pass on the original code: add one that would have caught this

  Score 35/100   still broken  (85 passes)   womp womp
```

Stuck? `python3 -m womp hint 02`. Fixed? `python3 -m womp debrief 02` explains the root cause, why the tests were green, and what a reviewer would ask you next.

| Command | What it does |
|---|---|
| `python3 -m womp` | list the exercises and your progress |
| `python3 -m womp start [n]` | open an exercise: prints the ticket, creates the working copy |
| `python3 -m womp check [n]` | grade your working copy |
| `python3 -m womp hint [n]` | show the next hint |
| `python3 -m womp debrief [n]` | the write-up, once the exercise is fixed |
| `python3 -m womp solution n --spoil` | the reference fix, as a diff |
| `python3 -m womp reset n` | start over; your attempt is kept in `work/.trash` |
| `python3 -m womp bench --cmd ...` | run a coding agent against the exercises |

`pip install -e .` gives you a plain `womp` command.

## How a fix is graded

- **Against a rubric you can read.** It is in the ticket, with the points for each line.
- **On cases you have not seen.** `run.py` shows one day of traffic, eight complaints or five conversations. The grader uses different ones, so a fix shaped to the visible symptoms does not pass.
- **Your tests have to fail on the original code.** Every exercise ships with a green test suite. The grader runs your tests against the unfixed app and expects a failure, because a fix without a test that would have caught the bug is half a fix.
- **In a sandbox.** Your `app/` and `tests/` are copied next to a clean copy of everything else, so editing the simulated model or the fixtures changes nothing.

## The model is simulated. The failures are real ones.

Every exercise has a small scripted stand-in for the model or the provider in `harness/`, and the top of that file says exactly how it behaves. It bills a cached prefix at a tenth of the price. It answers from the context when the evidence is there and guesses when it is not. It reads `null` as "nothing went wrong". It avoids low scores. It samples.

That is a deliberate trade. A simulated model is free, runs offline and gives the same result on every machine, which is what makes fair grading and a two-second feedback loop possible. What you lose is practice at wording prompts for a real model. These exercises are about the engineering around the model: the order of a prompt, how text is chunked and matched, what a tool loop does with an error, how a verdict is parsed, how sure a number is.

## Benchmark a coding agent

The same exercises work as a small benchmark: can an agent find a bug when the tests are green?

```
python3 -m womp bench --label "Claude Code" \
  --cmd 'claude -p {prompt} --permission-mode acceptEdits --allowedTools "Read,Edit,Write,Bash"'
```

`--cmd` is any shell command. It runs once per exercise, inside a fresh copy that contains no grader files. `{prompt}` is replaced with a short instruction and `{ticket}` with the path to `TICKET.md`. When the command exits, the copy is graded like a human attempt and the scores are written to `womp-bench.json`.

No results are published here yet. If you run it, open a pull request with your row.

| Agent and model | 01 | 02 | 03 | 04 | 05 | Fixed | Mean |
|---|---|---|---|---|---|---|---|

## Who this is for

- Engineers moving into AI engineering who want to meet these failures here before they meet them in production.
- Anyone preparing for the debugging round of an AI engineering interview. The tickets are original and are not taken from any company's assignment.
- Teams that want a shared set of drills for new joiners.

## How the exercises are kept honest

`tests/test_exercises.py` holds every exercise to a contract: it ships broken, its own tests pass on the broken code, its reference fix scores 100, and the rubric printed in the ticket is the rubric the grader uses. CI runs that on every push.

Design notes are in [docs/DESIGN.md](docs/DESIGN.md). To add an exercise, read [docs/WRITING_AN_EXERCISE.md](docs/WRITING_AN_EXERCISE.md).

## Roadmap

Five exercises is a start. Planned next: structured output that fails on a small share of inputs, a context window that drops the one message that mattered, instructions that arrive inside retrieved text, rate limits under parallel load, and an optional mode that swaps the simulated model for a real one.

## License

MIT
