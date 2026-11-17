import datetime
import unittest

from app.prompting import SYSTEM_PROMPT, build_prompt
from harness.traffic import TOOLS

NOW = datetime.datetime(2026, 3, 3, 9, 30, 0)
QUESTION = "How do I rotate an API key?"


def prompt(history=()):
    return build_prompt(QUESTION, list(history), NOW, "req-00beef", list(TOOLS))


class BuildPromptTest(unittest.TestCase):
    def test_system_prompt_is_included(self):
        self.assertIn(SYSTEM_PROMPT, "\n".join(prompt()))

    def test_every_tool_is_listed(self):
        text = "\n".join(prompt())
        for tool in TOOLS:
            self.assertIn(tool["name"], text)

    def test_time_and_request_id_are_included(self):
        text = "\n".join(prompt())
        self.assertIn(NOW.isoformat(), text)
        self.assertIn("req-00beef", text)

    def test_history_is_included_before_the_question(self):
        history = [{"role": "user", "text": "first message"}, {"role": "assistant", "text": "second message"}]
        text = "\n".join(prompt(history))
        self.assertLess(text.index("second message"), text.rindex(QUESTION))

    def test_question_is_the_last_block(self):
        self.assertTrue(prompt()[-1].endswith(QUESTION))


if __name__ == "__main__":
    unittest.main()
