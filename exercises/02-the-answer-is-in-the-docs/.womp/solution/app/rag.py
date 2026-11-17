"""Hank: answers staff questions from the Northwind Robotics handbook."""
import math
import re

TOP_K = 4
WINDOW = 2  # sentences per chunk; neighbouring chunks share one sentence
STOPWORDS = frozenset(
    "a an and are as at be before by can do does for from get has have how i if in into is it many me much my "
    "of on or our per so than that the their there they this to up we what when where which who will with you your".split()
)
_SUFFIXES = ("ing", "ly", "ed", "es", "s")


def stem(word):
    """A crude stemmer: enough to match 'passwords' with 'password' and 'rotated' with 'rotate'."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            break
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def terms(text):
    """Lowercase, strip punctuation, drop stopwords, stem. Applied to questions and chunks alike."""
    return [stem(word) for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


def sections(handbook):
    """Yield (heading, sentences) for each section of the handbook."""
    heading, found = "", []
    for line in handbook.splitlines():
        if line.startswith("#"):
            if found:
                yield heading, found
            heading, found = line.lstrip("# ").strip(), []
        elif line.strip():
            found.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", line.strip()) if part.strip())
    if found:
        yield heading, found


def build_index(handbook):
    """Chunks are whole sentences, never cut, each carrying its section heading."""
    chunks = []
    for heading, sentences in sections(handbook):
        for start in range(max(1, len(sentences) - WINDOW + 1)):
            chunks.append("%s: %s" % (heading, " ".join(sentences[start:start + WINDOW])))
    return chunks


def retrieve(question, index):
    """Rank chunks by the rare words they share with the question (a small BM25)."""
    docs = [terms(chunk) for chunk in index]
    seen_in = {}
    for doc in docs:
        for term in set(doc):
            seen_in[term] = seen_in.get(term, 0) + 1
    query = set(terms(question))

    def score(doc):
        total = 0.0
        for term in query:
            count = doc.count(term)
            if count:
                total += math.log(1 + len(docs) / seen_in[term]) * count / (count + 1.0)
        return total

    ranked = sorted(range(len(docs)), key=lambda position: score(docs[position]), reverse=True)
    return [index[position] for position in ranked[:TOP_K]]


def build_prompt(question, chunks):
    excerpts = "\n".join("- " + chunk for chunk in chunks)
    return (
        "You are Hank, the Northwind Robotics helpdesk assistant. Answer only from the handbook "
        "excerpts below. If they do not contain the answer, say you don't know.\n\n"
        "Handbook excerpts:\n%s\n\n"
        "Question: %s\nAnswer:" % (excerpts, question)
    )


def answer(question, index, model):
    """Answer one question. `model.complete(prompt)` returns the model's reply as text."""
    return model.complete(build_prompt(question, retrieve(question, index)))
