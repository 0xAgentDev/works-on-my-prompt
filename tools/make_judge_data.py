"""Generates the labelled answers for exercise 04. Seeded, so the files can be rebuilt exactly.

    python3 tools/make_judge_data.py

Each row is a support question, the assistant's answer, the reference answer and the label
a person gave it. Answers are built from 24 policy facts in nine styles: five that state
the fact, one of them in different words, and four that get it wrong, hedge, or avoid
the question.
"""
import json
import random
from pathlib import Path

EXERCISE = Path(__file__).resolve().parent.parent / "exercises" / "04-the-judge-says-yes"

# (question, what the policy says, the same sentence with the fact wrong, the policy in other words)
FACTS = [
    ("How long do I have to return an item?",
     "You can return an item within 30 days of delivery.",
     "You can return an item within 60 days of delivery.",
     "Returns are accepted for 30 days after your item is delivered."),
    ("How long does standard shipping take?",
     "Standard shipping takes 3 to 5 business days.",
     "Standard shipping takes 1 to 2 business days.",
     "Expect standard delivery to take between 3 and 5 business days."),
    ("When will I get my refund after a return?",
     "Refunds are paid within 7 days of the return reaching our warehouse.",
     "Refunds are paid within 24 hours of the return reaching our warehouse.",
     "Once the return reaches our warehouse, your money is back within 7 days."),
    ("How long is the warranty on electronics?",
     "Electronics come with a 2-year warranty.",
     "Electronics come with a 5-year warranty.",
     "All electronics are covered by a warranty of 2 years."),
    ("What order value gets free shipping?",
     "Shipping is free on orders over 50 dollars.",
     "Shipping is free on orders over 20 dollars.",
     "Orders above 50 dollars ship for free."),
    ("Can I cancel an order after placing it?",
     "An order can be cancelled within 1 hour of being placed.",
     "An order can be cancelled within 24 hours of being placed.",
     "You have 1 hour after placing an order to cancel it."),
    ("Do gift cards expire?",
     "Gift cards do not expire.",
     "Gift cards expire after 12 months.",
     "There is no expiry date on gift cards."),
    ("Do you match lower prices from other shops?",
     "We match a lower price that you find within 14 days of your purchase.",
     "We match a lower price that you find within 90 days of your purchase.",
     "If you find a lower price within 14 days of buying, we match it."),
    ("Which countries do you ship to?",
     "We ship to 28 countries in Europe and North America.",
     "We ship to every country in the world.",
     "We deliver to 28 countries across Europe and North America."),
    ("When is customer support available?",
     "Support is available from 8:00 to 20:00, Monday to Saturday.",
     "Support is available around the clock, every day of the year.",
     "Our support team works Monday to Saturday, 8:00 to 20:00."),
    ("Do loyalty points expire?",
     "Loyalty points expire 12 months after they are earned.",
     "Loyalty points never expire.",
     "Points from the loyalty programme are valid for 12 months after you earn them."),
    ("Is there a student discount?",
     "Students get a 10 percent discount with a valid student ID.",
     "Students get a 25 percent discount with a valid student ID.",
     "With a valid student ID you get 10 percent off."),
    ("How much does express shipping cost?",
     "Express shipping costs 12 dollars per order.",
     "Express shipping is free on every order.",
     "Express delivery adds 12 dollars to an order."),
    ("Can I change the delivery address after ordering?",
     "The delivery address can be changed until the order has shipped.",
     "The delivery address can be changed at any time, even after delivery.",
     "Until the order ships, you can still change where it is delivered."),
    ("Which payment methods do you accept?",
     "We accept credit cards, debit cards and bank transfer.",
     "We accept cash on delivery only.",
     "You can pay by credit card, debit card or bank transfer."),
    ("Who pays for return shipping?",
     "Return shipping is free when you use the prepaid label in the parcel.",
     "Return shipping is always paid by the customer.",
     "Use the prepaid label in the parcel and the return costs you nothing."),
    ("How do I track my order?",
     "A tracking link is emailed to you as soon as the order ships.",
     "Orders cannot be tracked once they have shipped.",
     "We email you a tracking link when the order ships."),
    ("Can I return an item I have opened?",
     "Opened items can be returned unless they are hygiene products.",
     "Opened items can never be returned.",
     "Yes, unless it is a hygiene product, an opened item can be returned."),
    ("How long are items held for store pickup?",
     "Items are held for store pickup for 7 days.",
     "Items are held for store pickup for 30 days.",
     "We keep items for store pickup for 7 days."),
    ("Is gift wrapping available?",
     "Gift wrapping is available for 4 dollars per item.",
     "Gift wrapping is free on every order.",
     "We can gift wrap any item for 4 dollars."),
    ("What if my parcel arrives damaged?",
     "Report a damaged parcel within 48 hours and we send a replacement.",
     "Report a damaged parcel within 30 days and we send a replacement.",
     "Tell us within 48 hours if a parcel arrives damaged and a replacement is sent."),
    ("Can I pay in installments?",
     "Installments are available on orders over 200 dollars.",
     "Installments are available on every order.",
     "Orders above 200 dollars can be paid in installments."),
    ("How do I delete my account?",
     "You can delete your account under Settings, Privacy.",
     "Accounts cannot be deleted once they are created.",
     "Go to Settings, then Privacy, to delete your account."),
    ("Do you sell refurbished products?",
     "Refurbished products are sold with a 1-year warranty.",
     "Refurbished products are sold without any warranty.",
     "Refurbished products come with a warranty of 1 year."),
]

POLITE = "Thanks for reaching out! %s If anything is unclear, our team is happy to help."
RIGHT_STYLES = [("%s", 20), ("Good question. %s", 18), ("%s Is there anything else I can help with?", 16), (POLITE, 15)]
REWORDED = 22  # right answers that share no sentence with the reference
WRONG_STYLES = [("%s", 20), (POLITE, 12), ("I am not completely sure, but I believe this is right: %s", 9)]
EVASIVE = ("That depends on a few things. Please check the help pages for the latest details.", 8)
DEV_SIZE = 60


def build():
    rng = random.Random(404)
    rows = []
    for style, count in RIGHT_STYLES:
        for question, right, _, _ in rng.sample(FACTS, count):
            rows.append({"question": question, "answer": style % right, "reference": right, "human_label": "pass"})
    for question, right, _, reworded in rng.sample(FACTS, REWORDED):
        rows.append({"question": question, "answer": reworded, "reference": right, "human_label": "pass"})
    for style, count in WRONG_STYLES:
        for question, right, wrong, _ in rng.sample(FACTS, count):
            rows.append({"question": question, "answer": style % wrong, "reference": right, "human_label": "fail"})
    for question, right, _, _ in rng.sample(FACTS, EVASIVE[1]):
        rows.append({"question": question, "answer": EVASIVE[0], "reference": right, "human_label": "fail"})
    rng.shuffle(rows)
    return [dict(id="a%03d" % number, **row) for number, row in enumerate(rows, 1)]


def write(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    rows = build()
    write(EXERCISE / "data" / "labeled.jsonl", rows[:DEV_SIZE])
    write(EXERCISE / ".womp" / "heldout.jsonl", rows[DEV_SIZE:])
    for name, part in (("labeled", rows[:DEV_SIZE]), ("held out", rows[DEV_SIZE:])):
        print("%s: %d rows, %d marked fail" % (name, len(part), sum(row["human_label"] == "fail" for row in part)))
