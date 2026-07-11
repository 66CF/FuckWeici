import unittest

from database import Database


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database()

    def test_listen_answer_order_independent(self):
        listen = self.db._questions.get("听音识词", {})
        self.assertTrue(listen.get("options_list"), "听音识词题库为空")
        choices = listen["options_list"][0]
        expected = listen["answers"][0]
        self.assertEqual(self.db.get_listen_answer(list(reversed(choices))), expected)

    def test_english_to_chinese_index_available(self):
        self.assertTrue(self.db._answer_maps.get("英译汉"), "英译汉索引为空")

    def test_note_search_returns_words(self):
        self.assertTrue(self.db._notes and self.db._words)
        result = self.db.search_by_note(self.db._notes[0])
        self.assertTrue(result)

    def test_get_meanings_caches(self):
        word = self.db._words[0]
        first = self.db.get_meanings(word)
        second = self.db.get_meanings(word)
        self.assertIs(first, second)

    def test_resolve_spelling_expands_optional(self):
        result = self.db.resolve_spelling("afterward(s)")
        self.assertTrue(result)

    def test_word_build_answers_returns_list(self):
        bucket = self.db._questions.get("构词法", {})
        questions = bucket.get("questions", [])
        if questions:
            answers = self.db.get_word_build_answers(questions[0], ["test", "abc"])
            self.assertIsInstance(answers, list)


if __name__ == "__main__":
    unittest.main()
