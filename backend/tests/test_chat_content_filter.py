"""User-input-only prohibited-language filter tests."""

import unittest

from app.chat.domain.content_filter import contains_prohibited_language


class ChatContentFilterTest(unittest.TestCase):
    def test_spacing_zero_width_punctuation_and_initials_do_not_bypass_filter(self) -> None:
        blocked = ("씨 발", "씨\u200b발", "f.u.c.k", "ㅅㅂ")
        for value in blocked:
            with self.subTest(value=value):
                self.assertTrue(contains_prohibited_language(value))

    def test_legitimate_starting_point_word_is_not_blocked(self) -> None:
        self.assertFalse(contains_prohibited_language("데이트의 시발점에서 만나자"))


if __name__ == "__main__":
    unittest.main()
