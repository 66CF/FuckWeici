import unittest

from SearchResult import SearchResult


class SearchResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.search = SearchResult()

    def test_listen_answer_order_independent(self):
        listen_section = self.search.newDATA.get("听音识词", [])
        self.assertTrue(isinstance(listen_section, list) and len(listen_section) >= 2)
        self.assertTrue(listen_section[0], "听音识词题库为空")

        choices = listen_section[0][0]
        expected = listen_section[1][0]
        reversed_choices = list(reversed(choices))
        self.assertEqual(self.search.getListenAnswer(reversed_choices), expected)

    def test_english_to_chinese_index_available(self):
        qa_map = self.search._english_to_chinese_map
        self.assertTrue(qa_map, "英译汉索引为空")

    def test_note_search_returns_words(self):
        notes = self.search.WordCorresponding.get("notes", [])
        words = self.search.WordCorresponding.get("words", [])
        self.assertTrue(notes and words)
        result = self.search.noteSearchWord(notes[0])
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
