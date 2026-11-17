"""Hank: answers staff questions from the Northwind Robotics handbook."""

CHUNK_SIZE = 220  # characters
TOP_K = 3


def build_index(handbook):
    """Split the handbook into chunks."""
    return [handbook[start:start + CHUNK_SIZE] for start in range(0, len(handbook), CHUNK_SIZE)]


def score(question, chunk):
    """How many words the question and the chunk have in common."""
    return len(set(question.split()) & set(chunk.split()))


def retrieve(question, index):
    """Return the chunks most relevant to the question, best first."""
    ranked = sorted(index, key=lambda chunk: score(question, chunk), reverse=True)
    return ranked[:TOP_K]


def build_prompt(question, chunks):
    excerpts = "\n\n".join(chunks)
    return (
        "You are Hank, the Northwind Robotics helpdesk assistant.\n\n"
        "Handbook excerpts:\n%s\n\n"
        "Question: %s\nAnswer:" % (excerpts, question)
    )


def answer(question, index, model):
    """Answer one question. `model.complete(prompt)` returns the model's reply as text."""
    return model.complete(build_prompt(question, retrieve(question, index)))
