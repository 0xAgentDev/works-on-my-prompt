"""Print the quality dashboard for the hand-labelled answers, next to what people said."""
from pathlib import Path

from app.judge import judge
from app.metrics import agreement, pass_rate
from harness.llm import JudgeModel, load_examples

DATA = Path(__file__).resolve().parent / "data"


def main():
    examples = load_examples(DATA / "labeled.jsonl")
    model = JudgeModel(examples)
    verdicts = [judge(example, model) for example in examples]
    humans = [example["human_label"] == "pass" for example in examples]
    print("Quality dashboard: %d answers from last week" % len(examples))
    print("  the judge passed  %3.0f%%" % (100 * pass_rate(verdicts)))
    print("  people passed     %3.0f%%" % (100 * pass_rate(humans)))
    try:
        report = agreement(verdicts, humans)
    except NotImplementedError as exc:
        print("  judge compared with people: %s" % exc)
        return
    print("  of the answers people passed, the judge passed  %.2f  (TPR)" % report["tpr"])
    print("  of the answers people failed, the judge failed  %.2f  (TNR)" % report["tnr"])
    print("  Cohen's kappa                                   %.2f" % report["kappa"])


if __name__ == "__main__":
    main()
