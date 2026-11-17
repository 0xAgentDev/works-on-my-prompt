"""Run Hank's offline eval, then replay the questions from this week's complaints."""
from pathlib import Path

from app import rag
from harness.evaluate import evaluate
from harness.llm import Model, load_items

DATA = Path(__file__).resolve().parent / "data"


def main():
    eval_items = load_items(DATA / "eval_questions.jsonl")
    reports = load_items(DATA / "user_reports.jsonl")
    model = Model(eval_items + reports)
    scores = evaluate(rag, eval_items, model)
    print("Offline eval: %d questions, accuracy %.2f, made-up answers %d" % (len(scores.rows), scores.accuracy, len(scores.wrong)))
    print("\nThis week's complaints:")
    replayed = evaluate(rag, reports, model)
    for row in replayed.rows:
        print("  Q: %s" % row.item.question)
        print("     Hank:      %s" % row.reply)
        print("     Handbook:  %s" % (row.item.fact or "does not cover this"))
    handled = sum(row.outcome == ("correct" if row.item.fact else "declined") for row in replayed.rows)
    print("\n%d of %d handled the way the handbook says" % (handled, len(replayed.rows)))


if __name__ == "__main__":
    main()
