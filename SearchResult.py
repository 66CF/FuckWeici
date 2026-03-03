import json
import os
import re
import sqlite3
import time
from collections import defaultdict


class SearchResult:
    def __init__(self):
        self.verbose = os.getenv("FW_VERBOSE", "1").strip().lower() in {"1", "true", "yes", "on"}
        self.db_path = os.getenv("FW_DB_PATH", os.path.join("db", "weici_ext459.db"))
        init_start_time = time.time()
        self._log("--- SearchResult 初始化 ---")

        self.WordCorresponding = {}
        self.newDATA = {}
        if not self._load_from_db():
            raise RuntimeError(
                f"题库数据库加载失败，请检查文件: {self.db_path}（可用 FW_DB_PATH 指定路径）"
            )

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

    def _normalize_question_text(self, text):
        return "".join(re.findall(r"[a-zA-Z\u4e00-\u9fa5]+", str(text or "")))

    def _format_answer(self, answer):
        normalized = str(answer or "").strip().strip("'\"")
        return f"'{normalized}'" if normalized else ""

    def _strip_choice_prefix(self, choice):
        return re.sub(r"^[A-D]\.\s*", "", str(choice or "").strip())

    def _split_build_parts(self, value):
        if value is None:
            return []
        return [part.strip() for part in re.split(r"[,\s，]+", str(value)) if part.strip()]

    def _append_qa(self, qa_section, question, answer):
        if not question or not answer:
            return
        qa_section[0].append(question)
        qa_section[1].append(answer)

    def _build_new_data_from_db(self, conn):
        new_data = {
            "听音识词": [[], []],
            "语境题": [[], []],
            "构词法": [[], [], []],
            "汉译英": [[], []],
            "英译汉": [[], []],
        }
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT questions, subject, answer, answer_a, answer_b, answer_c, spell_word
            FROM fb_word_test
            WHERE "delete" = 0
            """
        ).fetchall()
        for questions, subject, answer, answer_a, answer_b, answer_c, spell_word in rows:
            q_type = int(questions or 0)
            normalized_answer = self._format_answer(answer)
            if q_type == 6:
                options = [
                    self._strip_choice_prefix(answer_a),
                    self._strip_choice_prefix(answer_b),
                    self._strip_choice_prefix(answer_c),
                ]
                if all(options) and normalized_answer:
                    new_data["听音识词"][0].append(options)
                    new_data["听音识词"][1].append(normalized_answer)
            elif q_type in (4, 5):
                question = self._normalize_question_text(subject)
                self._append_qa(new_data["语境题"], question, normalized_answer)
            elif q_type == 3:
                question = self._normalize_question_text(subject)
                self._append_qa(new_data["汉译英"], question, normalized_answer)
            elif q_type == 2:
                question = str(subject or "").strip()
                self._append_qa(new_data["英译汉"], question, normalized_answer)
            elif q_type == 7:
                question = self._normalize_question_text(subject)
                full_parts = self._split_build_parts(answer)
                select_parts = self._split_build_parts(spell_word)
                if question and full_parts:
                    new_data["构词法"][0].append(question)
                    new_data["构词法"][1].append(select_parts)
                    new_data["构词法"][2].append(full_parts)
        return new_data

    def _build_word_corresponding_from_db(self, conn):
        details = []
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT detail_json
            FROM fb_word_detail
            WHERE "delete" = 0 AND detail_json IS NOT NULL AND TRIM(detail_json) <> ''
            """
        ).fetchall()
        for (detail_json,) in rows:
            try:
                details.append(json.loads(detail_json))
            except json.JSONDecodeError:
                continue
        return self.generateWordCorresponding(details)

    def _load_from_db(self):
        if not os.path.exists(self.db_path):
            self._log(f"  - [DB] 未找到数据库: {self.db_path}")
            return False
        db_start_time = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                self.WordCorresponding = self._build_word_corresponding_from_db(conn)
                self.newDATA = self._build_new_data_from_db(conn)
            if not self.WordCorresponding.get("words") or not self.newDATA.get("语境题", [[], []])[0]:
                self._log("  - [DB] 数据为空或结构异常")
                return False
            self._log(f"  - [DB] 题库加载完毕 ({time.time() - db_start_time:.4f}s) -> {self.db_path}")
            return True
        except (sqlite3.Error, OSError) as exc:
            self._log(f"  - [DB] 加载失败: {exc}")
            return False

    def _build_question_answer_map(self, key):
        section = self.newDATA.get(key, [])
        if not isinstance(section, list) or len(section) < 2:
            return {}

        questions = section[0] if isinstance(section[0], list) else []
        answers = section[1] if isinstance(section[1], list) else []
        result = defaultdict(list)
        for q, a in zip(questions, answers):
            q_raw = str(q or "").strip()
            if not q_raw:
                continue
            result[q_raw].append(a)
            q_norm = self._normalize_question_text(q_raw)
            if q_norm and q_norm != q_raw:
                result[q_norm].append(a)
            q_lower = q_raw.lower()
            if q_lower != q_raw:
                result[q_lower].append(a)
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

    def generateWordCorresponding(self, data):
        """创建单词 音标 词性 意思列表"""
        words = []
        word_notes = []
        word_parts = []
        word_means = []
        for word_detail in data:
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
        return self._query_answers(self._long_answer_map, question)

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
        return self._query_answers(self._chinese_to_english_map, question)

    def getEnglishtoChinese(self, question):
        return self._query_answers(self._english_to_chinese_map, question)

    def _query_answers(self, answer_map, question):
        if not answer_map:
            return []
        candidates = []
        query = str(question or "").strip()
        if query:
            candidates.append(query)
            lower_query = query.lower()
            if lower_query != query:
                candidates.append(lower_query)
            norm_query = self._normalize_question_text(query)
            if norm_query and norm_query not in candidates:
                candidates.append(norm_query)
            norm_lower_query = norm_query.lower() if norm_query else ""
            if norm_lower_query and norm_lower_query not in candidates:
                candidates.append(norm_lower_query)
        for key in candidates:
            result = answer_map.get(key, [])
            if result:
                return result
        return []
