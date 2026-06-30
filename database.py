import json
import os
import re
import sqlite3
from collections import defaultdict


def _normalize_text(text):
    return "".join(re.findall(r"[a-zA-Z\u4e00-\u9fa5]+", str(text or "")))


def _strip_choice_prefix(choice):
    return re.sub(r"^[A-D]\.\s*", "", str(choice or "").strip())


def _split_parts(value):
    if value is None:
        return []
    return [p.strip() for p in re.split(r"[,\s，]+", str(value)) if p.strip()]


def _normalize_choice(value):
    return str(value or "").strip().strip("'\"")


def _normalize_choice_key(choices):
    return tuple(sorted(_normalize_choice(c) for c in choices))


def _normalize_spelling(word):
    return re.sub(r"\s+", "", str(word or "").strip()).lower()


def _expand_optional_spelling(word):
    raw = str(word or "").strip()
    if not raw:
        return []
    pattern = re.compile(r"\(([^()]+)\)")
    variants = []
    seen = set()

    def push(value):
        if value and value not in seen:
            seen.add(value)
            variants.append(value)
            return True
        return False

    queue = [raw]
    push(raw)
    while queue:
        current = queue.pop(0)
        match = pattern.search(current)
        if not match:
            continue
        without = current[:match.start()] + current[match.end():]
        with_opt = current[:match.start()] + match.group(1) + current[match.end():]
        if push(without):
            queue.append(without)
        if push(with_opt):
            queue.append(with_opt)
    return variants


class Database:
    def __init__(self):
        self.db_path = os.getenv("FW_DB_PATH", os.path.join("db", "weici_ext459.db"))
        self._words = []
        self._notes = []
        self._parts = []
        self._means = []
        self._questions = {
            "拼写": {"subjects": [], "answers": []},
            "听音识词": {"options_list": [], "answers": []},
            "语境题": {"questions": [], "answers": []},
            "构词法": {"questions": [], "select_parts": [], "full_parts": []},
            "汉译英": {"questions": [], "answers": []},
            "英译汉": {"questions": [], "answers": []},
        }
        if not self._load():
            raise RuntimeError(
                f"题库数据库加载失败，请检查文件: {self.db_path}（可用 FW_DB_PATH 指定路径）"
            )
        self._build_indexes()

    def _load(self):
        if not os.path.exists(self.db_path):
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                self._load_word_corpus(conn)
                self._load_questions(conn)
            if not self._words or not self._questions["语境题"]["questions"]:
                return False
            return True
        except (sqlite3.Error, OSError):
            return False

    def _load_word_corpus(self, conn):
        rows = conn.execute(
            "SELECT detail_json FROM fb_word_detail "
            'WHERE "delete" = 0 AND detail_json IS NOT NULL AND TRIM(detail_json) <> \'\''
        ).fetchall()
        for (detail_json,) in rows:
            try:
                detail = json.loads(detail_json)
            except json.JSONDecodeError:
                continue
            word = detail["word"]
            note = detail["usa_phonetic_symbols"]
            part = detail["part_of_speech"]
            if part in ("vt", "vi"):
                part = "v"
            mean = [m["chinese"] for m in detail.get("gy_paraphrase", [])]

            self._words.append(word)
            self._notes.append(note)
            self._parts.append(part)
            self._means.append(mean)

            for deriv in detail.get("gy_derivative", []):
                dw = deriv.get("derivative_word")
                if not dw:
                    continue
                dn = deriv.get("phonogram", "")
                dp = deriv.get("part_of_speech", "")
                if dp in ("vt", "vi"):
                    dp = "v"
                dm = [deriv.get("description", "")]
                self._words.append(dw)
                self._notes.append(dn)
                self._parts.append(dp)
                self._means.append(dm)

    def _load_questions(self, conn):
        TYPE_MAP = {
            1: "拼写", 2: "英译汉", 3: "汉译英",
            4: "语境题", 5: "语境题", 6: "听音识词", 7: "构词法",
        }
        rows = conn.execute(
            "SELECT questions, subject, answer, answer_a, answer_b, answer_c, spell_word "
            'FROM fb_word_test WHERE "delete" = 0'
        ).fetchall()
        for questions, subject, answer, aa, ab, ac, spell_word in rows:
            q_type = int(questions or 0)
            category = TYPE_MAP.get(q_type)
            if not category:
                continue
            norm_answer = _normalize_choice(answer)
            norm_answer = f"'{norm_answer}'" if norm_answer else ""

            bucket = self._questions[category]
            if q_type == 1:
                sw = str(subject or "").strip()
                aw = _normalize_choice(answer)
                bucket["subjects"].append(sw)
                bucket["answers"].append(aw or sw)
            elif q_type == 6:
                options = [_strip_choice_prefix(x) for x in (aa, ab, ac)]
                if all(options) and norm_answer:
                    bucket["options_list"].append(options)
                    bucket["answers"].append(norm_answer)
            elif q_type in (4, 5):
                q = _normalize_text(subject)
                if q and norm_answer:
                    bucket["questions"].append(q)
                    bucket["answers"].append(norm_answer)
            elif q_type == 3:
                q = _normalize_text(subject)
                if q and norm_answer:
                    bucket["questions"].append(q)
                    bucket["answers"].append(norm_answer)
            elif q_type == 2:
                q = str(subject or "").strip()
                if q and norm_answer:
                    bucket["questions"].append(q)
                    bucket["answers"].append(norm_answer)
            elif q_type == 7:
                q = _normalize_text(subject)
                full = _split_parts(answer)
                select = _split_parts(spell_word)
                if q and full:
                    bucket["questions"].append(q)
                    bucket["select_parts"].append(select)
                    bucket["full_parts"].append(full)

    def _build_indexes(self):
        self._word_to_idx = defaultdict(list)
        self._note_to_idx = defaultdict(list)
        for i, w in enumerate(self._words):
            self._word_to_idx[w].append(i)
            if i < len(self._notes):
                self._note_to_idx[self._notes[i]].append(i)

        self._mean_cache = {}
        self._answer_maps = {}
        for key in ("语境题", "汉译英", "英译汉"):
            self._answer_maps[key] = self._build_qa_map(key)
        self._build_word_indexes = self._build_q_index("构词法")
        self._listen_map = self._build_listen_map()
        self._spelling_map = self._build_spelling_map()

    def _build_qa_map(self, key):
        bucket = self._questions.get(key, {})
        qs = bucket.get("questions", [])
        ans = bucket.get("answers", [])
        result = defaultdict(list)
        for q, a in zip(qs, ans):
            q_raw = str(q or "").strip()
            if not q_raw:
                continue
            result[q_raw].append(a)
            q_norm = _normalize_text(q_raw)
            if q_norm and q_norm != q_raw:
                result[q_norm].append(a)
            q_lower = q_raw.lower()
            if q_lower != q_raw:
                result[q_lower].append(a)
        return result

    def _build_q_index(self, key):
        bucket = self._questions.get(key, {})
        qs = bucket.get("questions", [])
        result = defaultdict(list)
        for i, q in enumerate(qs):
            result[q].append(i)
        return result

    def _build_listen_map(self):
        bucket = self._questions.get("听音识词", {})
        opts = bucket.get("options_list", [])
        ans = bucket.get("answers", [])
        result = {}
        for options, answer in zip(opts, ans):
            key = _normalize_choice_key(options)
            if key and key not in result:
                result[key] = answer
        return result

    def _build_spelling_map(self):
        bucket = self._questions.get("拼写", {})
        subjects = bucket.get("subjects", [])
        answers = bucket.get("answers", [])
        result = {}

        def register(raw):
            norm = _normalize_spelling(raw)
            cleaned = re.sub(r"[^A-Za-z]", "", str(raw or "").strip())
            if norm and norm not in result:
                result[norm] = str(raw).strip()
            cn = _normalize_spelling(cleaned)
            if cn and cn not in result:
                result[cn] = cleaned

        for raw in answers:
            register(raw)
        for raw in subjects:
            register(raw)
        return result

    # ── Query API ──

    def search_by_note(self, note):
        return [self._words[i] for i in self._note_to_idx.get(note, [])]

    def get_meanings(self, word):
        if word in self._mean_cache:
            return self._mean_cache[word]
        result = []
        for idx in self._word_to_idx.get(word, []):
            for mean in self._means[idx]:
                normalized = mean.replace("：", "")
                if "；" in normalized:
                    result.extend(normalized.split("；"))
                else:
                    result.append(normalized)
        self._mean_cache[word] = result
        return result

    def get_listen_answer(self, choices):
        return self._listen_map.get(_normalize_choice_key(choices))

    def resolve_spelling(self, word):
        variants = _expand_optional_spelling(word)
        if not variants:
            return ""
        for v in variants:
            norm = _normalize_spelling(v)
            if norm in self._spelling_map:
                return self._spelling_map[norm]
            cleaned = re.sub(r"[^A-Za-z]", "", v)
            cn = _normalize_spelling(cleaned)
            if cn in self._spelling_map:
                return self._spelling_map[cn]
        for v in variants:
            cleaned = re.sub(r"[^A-Za-z]", "", v)
            if cleaned:
                return cleaned
        return str(word or "").strip()

    def get_word_build_answers(self, question, available_parts):
        indices = self._build_word_indexes.get(question, [])
        if not indices:
            return []
        fp = self._questions.get("构词法", {}).get("full_parts", [])
        result = []
        for idx in indices:
            if idx >= len(fp):
                continue
            parts = fp[idx]
            if not isinstance(parts, list):
                continue
            to_click = [p for p in parts if p != question]
            if all(p in available_parts for p in to_click):
                result.append({"word": "".join(parts), "parts_to_click": to_click})
        return result

    def get_chinese_to_english(self, question):
        return self._query_answers("汉译英", question)

    def get_english_to_chinese(self, question):
        return self._query_answers("英译汉", question)

    def get_context_answer(self, question):
        return self._query_answers("语境题", question)

    def _query_answers(self, key, question):
        amap = self._answer_maps.get(key)
        if not amap:
            return []
        query = str(question or "").strip()
        if not query:
            return []
        candidates = [query]
        lq = query.lower()
        if lq != query:
            candidates.append(lq)
        nq = _normalize_text(query)
        if nq and nq not in candidates:
            candidates.append(nq)
        nlq = nq.lower() if nq else ""
        if nlq and nlq not in candidates:
            candidates.append(nlq)
        for k in candidates:
            result = amap.get(k, [])
            if result:
                return result
        return []
