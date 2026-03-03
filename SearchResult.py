import json
import os
import time
from collections import defaultdict


class SearchResult:
    def __init__(self):
        self.verbose = os.getenv("FW_VERBOSE", "1").strip().lower() in {"1", "true", "yes", "on"}
        init_start_time = time.time()
        self._log("--- SearchResult 初始化 ---")

        load_start_time = time.time()
        with open("Data/fb_word_detail.json", "r", encoding="utf-8") as f:
            self.DATA = json.load(f)
        self._log(f"  - [IO] 'fb_word_detail.json' 加载完毕 ({time.time() - load_start_time:.4f}s)")

        word_corr_start_time = time.time()
        if not os.path.exists("Data/WordCorresponding.json"):
            self._log("  - [!] 'WordCorresponding.json' 不存在, 开始生成...")
            self.WordCorresponding = self.generateWordCorresponding()
            with open("Data/WordCorresponding.json", "w", encoding="utf-8") as f:
                json.dump(self.WordCorresponding, f, ensure_ascii=False, indent=4)
            self._log(f"  - [CPU] 'WordCorresponding.json' 生成完毕 ({time.time() - word_corr_start_time:.4f}s)")
        else:
            with open("Data/WordCorresponding.json", "r", encoding="utf-8") as f:
                self.WordCorresponding = json.load(f)
            self._log(f"  - [IO] 'WordCorresponding.json' 加载完毕 ({time.time() - word_corr_start_time:.4f}s)")

        load_start_time = time.time()
        with open("Data/newAnswer.json", "r", encoding="utf-8") as f:
            self.newDATA = json.load(f)
        self._log(f"  - [IO] 'newAnswer.json' 加载完毕 ({time.time() - load_start_time:.4f}s)")

        self._build_indexes()
        self._log(f"--- 初始化完成 (总耗时: {time.time() - init_start_time:.4f}s) ---")

    def _log(self, message):
        if self.verbose:
            print(message)

    def _build_indexes(self):
        self._word_to_indexes = defaultdict(list)
        self._note_to_indexes = defaultdict(list)
        words = self.WordCorresponding.get("words", [])
        notes = self.WordCorresponding.get("notes", [])
        for idx, word in enumerate(words):
            self._word_to_indexes[word].append(idx)
            if idx < len(notes):
                self._note_to_indexes[notes[idx]].append(idx)

        self._mean_cache = {}
        self._long_answer_map = self._build_question_answer_map("语境题")
        self._chinese_to_english_map = self._build_question_answer_map("汉译英")
        self._english_to_chinese_map = self._build_question_answer_map("英译汉")
        self._build_word_indexes = self._build_question_indexes("构词法")
        self._listen_answer_map = self._build_listen_answer_map()

    def _build_question_answer_map(self, key):
        section = self.newDATA.get(key, [])
        if not isinstance(section, list) or len(section) < 2:
            return {}

        questions = section[0] if isinstance(section[0], list) else []
        answers = section[1] if isinstance(section[1], list) else []
        result = defaultdict(list)
        for q, a in zip(questions, answers):
            result[q].append(a)
        return result

    def _build_question_indexes(self, key):
        section = self.newDATA.get(key, [])
        if not isinstance(section, list) or not section:
            return {}
        questions = section[0] if isinstance(section[0], list) else []
        result = defaultdict(list)
        for idx, question in enumerate(questions):
            result[question].append(idx)
        return result

    def _normalize_choice(self, value):
        return str(value or "").strip().strip("'\"")

    def _normalize_choice_key(self, choices):
        normalized = [self._normalize_choice(c) for c in choices]
        return tuple(sorted(normalized))

    def _build_listen_answer_map(self):
        section = self.newDATA.get("听音识词", [])
        if not isinstance(section, list) or len(section) < 2:
            return {}

        questions = section[0] if isinstance(section[0], list) else []
        answers = section[1] if isinstance(section[1], list) else []
        answer_map = {}
        for options, answer in zip(questions, answers):
            if not isinstance(options, list):
                continue
            key = self._normalize_choice_key(options)
            if key and key not in answer_map:
                answer_map[key] = answer
        return answer_map

    def generateWordCorresponding(self):
        """创建单词 音标 词性 意思列表"""
        words = []
        word_notes = []
        word_parts = []
        word_means = []
        for word_detail in self.DATA:
            word_word = word_detail["word"]
            word_note_usa = word_detail["usa_phonetic_symbols"]
            word_part = word_detail["part_of_speech"]
            if word_part in ["vt", "vi"]:
                word_part = "v"

            word_mean = [mean["chinese"] for mean in word_detail.get("gy_paraphrase", [])]

            words.append(word_word)
            word_notes.append(word_note_usa)
            word_parts.append(word_part)
            word_means.append(word_mean)

            for word_derivative in word_detail.get("gy_derivative", []):
                derivative_word = word_derivative.get("derivative_word")
                if not derivative_word:
                    continue

                derivative_note = word_derivative.get("phonogram", "")
                derivative_part = word_derivative.get("part_of_speech", "")
                if derivative_part in ["vt", "vi"]:
                    derivative_part = "v"
                derivative_mean = [word_derivative.get("description", "")]

                words.append(derivative_word)
                word_notes.append(derivative_note)
                word_parts.append(derivative_part)
                word_means.append(derivative_mean)
        return {"words": words, "notes": word_notes, "parts": word_parts, "means": word_means}

    def noteSearchWord(self, note):
        """ 从音标搜找单词 """
        return [self.WordCorresponding["words"][i] for i in self._note_to_indexes.get(note, [])]

    def partSearchWord(self, wholeWord, part):
        """ 从整个单词和词性找单词 """
        for word in wholeWord:
            for idx in self._word_to_indexes.get(word, []):
                if part == self.WordCorresponding["parts"][idx]:
                    return word
        return None

    def getMeanFromWord(self, word):
        """ 找单词意思 """
        if word in self._mean_cache:
            return self._mean_cache[word]

        mean_list = []
        for idx in self._word_to_indexes.get(word, []):
            for mean in self.WordCorresponding["means"][idx]:
                normalized_mean = mean.replace("：", "")
                if "；" in normalized_mean:
                    mean_list.extend(normalized_mean.split("；"))
                else:
                    mean_list.append(normalized_mean)

        self._mean_cache[word] = mean_list
        return mean_list

    def indexListMore(self, input_list, element):
        """ 返回 下标 """
        return [i for i, x in enumerate(input_list) if x == element]

    def getLongAnswer(self, question):
        return self._long_answer_map.get(question, [])

    def getListenAnswer(self, choices):
        key = self._normalize_choice_key(choices)
        return self._listen_answer_map.get(key)

    def find_indexes(self, input_list, element):
        return [i for i, value in enumerate(input_list) if value == element]

    def getPutAnswer(self, question, parts, position):
        func_start_time = time.time()
        found_answers = []
        indices = self._build_word_indexes.get(question, [])
        if not indices:
            self._log(f"    - [getPutAnswer] 未找到答案 (总耗时: {time.time() - func_start_time:.4f}s)")
            return []

        build_word_section = self.newDATA.get("构词法", [])
        all_full_word_parts = build_word_section[2] if len(build_word_section) > 2 and isinstance(build_word_section[2], list) else []
        for idx in indices:
            if idx >= len(all_full_word_parts):
                continue

            full_word_parts = all_full_word_parts[idx]
            if not isinstance(full_word_parts, list):
                continue

            derived_parts_to_click = [p for p in full_word_parts if p != question]
            if all(p in parts for p in derived_parts_to_click):
                candidate = {"word": "".join(full_word_parts), "parts_to_click": derived_parts_to_click}
                found_answers.append(candidate)
                self._log(f"    - [getPutAnswer] 找到候选答案: {candidate['word']}")

        if found_answers:
            self._log(f"    - [getPutAnswer] 查找完毕，共找到 {len(found_answers)} 个候选 (总耗时: {time.time() - func_start_time:.4f}s)")
            return found_answers

        self._log(f"    - [getPutAnswer] 未找到答案 (总耗时: {time.time() - func_start_time:.4f}s)")
        return []

    def getChinesetoEnglish(self, question):
        return self._chinese_to_english_map.get(question, [])

    def getEnglishtoChinese(self, question):
        return self._english_to_chinese_map.get(question, [])
