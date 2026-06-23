import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from random import randint

import uiautomator2 as u2
from SearchResult import SearchResult

GUM = shutil.which("gum")

GUM_COLORS = {
    "accent": "#7DD3FC",
    "muted": "#94A3B8",
}

QUESTION_TITLES = {
    1: "拼写",
    2: "英译汉",
    345: "大杂烩",
    6: "听音识词",
    7: "构词法拼词",
}

STATUS = {
    "ok":    ("命中", "info"),
    "warn":  ("兜底", "warn"),
    "error": ("失败", "error"),
    "info":  ("提示", "info"),
}
RELAX_TIME_CHOICES = ("0.5 秒", "1 秒", "2 秒", "3 秒", "5 秒", "自定义")


def _run_gum(args, input_text=None, capture_output=False):
    if not GUM:
        return None
    try:
        return subprocess.run(
            [GUM, *args],
            input=input_text,
            stdout=subprocess.PIPE if capture_output else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (OSError, ValueError):
        return None


def _gum_interactive():
    return bool(GUM and sys.stdin.isatty())


def _gum_log(level, message, *, prefix=None):
    message = re.sub(r"\s+", " ", str(message or "")).strip()
    args = ["log", "--level", level]
    if prefix:
        args.extend(["--prefix", prefix])

    completed = _run_gum(args + [message])
    if completed is None or completed.returncode != 0:
        label = level.upper()
        prefix_text = f" {prefix}:" if prefix else ""
        print(f"{label}{prefix_text} {message}")


def _run_with_spinner(title, func):
    if not _gum_interactive():
        return func()

    fd, marker_name = tempfile.mkstemp(prefix="fw-gum-spin-", suffix=".done")
    os.close(fd)
    marker = Path(marker_name)
    marker.unlink(missing_ok=True)
    result = {}

    def runner():
        try:
            result["value"] = func()
        except BaseException as exc:
            result["error"] = exc
        finally:
            try:
                marker.touch(exist_ok=True)
            except OSError:
                pass

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    wait_script = (
        "import pathlib,time\n"
        f"marker = pathlib.Path({str(marker)!r})\n"
        "while not marker.exists():\n"
        "    time.sleep(0.1)\n"
    )
    _run_gum([
        "spin",
        "--spinner",
        "dot",
        "--title",
        title,
        "--spinner.foreground",
        GUM_COLORS["accent"],
        "--title.foreground",
        GUM_COLORS["muted"],
        "--",
        sys.executable,
        "-c",
        wait_script,
    ])
    thread.join()
    marker.unlink(missing_ok=True)

    if "error" in result:
        raise result["error"]
    return result.get("value")


def _gum_confirm(message, *, affirmative="继续", negative="退出", default=True):
    if _gum_interactive():
        args = [
            "confirm",
            message,
            "--affirmative",
            affirmative,
            "--negative",
            negative,
            "--prompt.foreground",
            GUM_COLORS["accent"],
            "--selected.background",
            GUM_COLORS["accent"],
            "--selected.foreground",
            "#0F172A",
            "--unselected.foreground",
            "#CBD5E1",
        ]
        if default:
            args.append("--default")
        completed = _run_gum(args)
        if completed is not None:
            return completed.returncode == 0

    raw = prompt_input(f"{message}（回车={affirmative}，q={negative}）").strip().lower()
    return raw != "q"


def prompt_input(message, placeholder=""):
    if _gum_interactive():
        args = [
            "input",
            "--prompt",
            f"{message}: ",
            "--placeholder",
            placeholder,
            "--prompt.foreground",
            GUM_COLORS["accent"],
            "--cursor.foreground",
            GUM_COLORS["accent"],
        ]
        completed = _run_gum(args, capture_output=True)
        if completed is not None and completed.returncode == 0:
            return completed.stdout.rstrip("\r\n")
        if completed is not None:
            return ""

    try:
        return input(f"{message}: ")
    except EOFError:
        return ""


def ask_relax_time(default_value=2.0):
    selected_choice = "2 秒"
    if default_value == 0.5:
        selected_choice = "0.5 秒"
    elif default_value in (1, 2, 3, 5):
        selected_choice = f"{int(default_value)} 秒"

    if _gum_interactive():
        completed = _run_gum(
            [
                "choose",
                *RELAX_TIME_CHOICES,
                "--header",
                "每题操作间隔",
                "--height",
                str(len(RELAX_TIME_CHOICES)),
                "--selected",
                selected_choice,
                "--cursor.foreground",
                GUM_COLORS["accent"],
                "--selected.foreground",
                GUM_COLORS["accent"],
                "--header.foreground",
                GUM_COLORS["muted"],
            ],
            capture_output=True,
        )
        if completed is not None and completed.returncode == 0:
            choice = completed.stdout.strip()
            if choice != "自定义":
                match = re.search(r"\d+(?:\.\d+)?", choice)
                if match:
                    return float(match.group())

    if not sys.stdin.isatty():
        return default_value

    while True:
        raw = (
            prompt_input(f"自定义每题操作间隔（秒，默认 {default_value}）", str(default_value)).strip()
            or str(default_value)
        )
        try:
            value = float(raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            label, level = STATUS.get("warn", ("兜底", "warn"))
            _gum_log(level, "输入无效 · 请输入大于等于 0 的数字", prefix=label)


def wait_for_start(_total_hint_text):
    while True:
        if not _gum_confirm("准备好开始了吗？", affirmative="开始", negative="退出"):
            raise SystemExit(0)
        return


def wait_until_quiz_ready(app):
    while True:
        _gum_log("warn", "请把设备停留在答题界面。准备好后回到这里按回车，我会先尝试读取题号。", prefix="等待")
        wait_for_start(True)
        try:
            _gum_log("info", "正在读取当前题目状态...", prefix="状态")
            return app.getTotal()
        except Exception as exc:
            label, level = STATUS.get("warn", ("兜底", "warn"))
            _gum_log(level, f"还没识别到答题页 · {exc}", prefix=label)


def wait_for_manual_resume(reason):
    _gum_log("warn", f"{reason}\n\n请你在手机上手动完成这一题，然后回到这里按回车继续。", prefix="等待")
    if not _gum_confirm("手动处理完成了吗？", affirmative="继续", negative="退出"):
        raise SystemExit(0)


def ask_continue_next_round():
    return _gum_confirm("继续下一轮？", affirmative="继续", negative="结束")


class U2VictorApp:
    def __init__(self, device, relax_time=2.0):
        self.d = device
        self.pkg_name = "com.android.weici.senior.student"
        
        self.ID_KEYBOARD = f"{self.pkg_name}:id/keyboard"
        self.ID_PART_WORD = f"{self.pkg_name}:id/part_word"
        self.ID_ENGLISH = f"{self.pkg_name}:id/english"
        self.ID_QUESTION = f"{self.pkg_name}:id/question"
        self.ID_SOUND = f"{self.pkg_name}:id/sound"
        self.ID_POSITION = f"{self.pkg_name}:id/position"
        self.ID_YINBIAO = f"{self.pkg_name}:id/yinbiao"
        self.ID_CHINESE = f"{self.pkg_name}:id/chinese"
        self.ID_KEY_CONFIRM = f"{self.pkg_name}:id/key_to_confirm"

        self.TITLES = {
            1: self.__spellTitle,
            2: self.__englishToChinese,
            345: self.__question,
            6: self.__listen,
            7: self.__buildWord,
        }
        self.searcher = SearchResult()

        self.lastType = ''
        self.is_king_mode = False
        self.position = 1
        self.runTime = 0
        self.relaxTime = relax_time if relax_time >= 0 else 2.0

    def report(self, status, summary, detail=None):
        label, level = STATUS.get(status, (status.upper(), "info"))
        line = str(summary)
        if detail:
            line += f" · {detail}"
        _gum_log(level, line, prefix=label)

    def _get_title_counts(self):
        return {
            1: self.d(resourceId=self.ID_KEYBOARD).count,
            7: self.d(resourceId=self.ID_PART_WORD).count,
            2: self.d(resourceId=self.ID_ENGLISH).count,
            345: self.d(resourceId=self.ID_QUESTION).count,
            6: self.d(resourceId=self.ID_SOUND).count,
        }

    def _get_title_exists(self):
        return {
            1: self.d(resourceId=self.ID_KEYBOARD).exists,
            7: self.d(resourceId=self.ID_PART_WORD).exists,
            2: self.d(resourceId=self.ID_ENGLISH).exists,
            345: self.d(resourceId=self.ID_QUESTION).exists,
            6: self.d(resourceId=self.ID_SOUND).exists,
        }

    def tellTitle(self):
        """ 辨别题型 """
        self.position = self.getPosition()

        counts = self._get_title_counts()

        if counts[1] == (2 if self.lastType == '拼写' else 1):
            return 1

        if counts[7] == (2 if self.lastType == '构词法拼词' else 1):
            return 7

        if counts[2] == (2 if self.lastType == '英译汉' else 1):
            return 2

        if counts[345] == (2 if self.lastType == '大杂烩' else 1):
            return 345

        if counts[6] == (2 if self.lastType == '听音识词' else 1):
            return 6
        
        # 增加重试机制，防止因页面加载延迟无法识别
        for _ in range(5):
            time.sleep(0.5)
            exists = self._get_title_exists()
            for mode in (1, 7, 2, 345, 6):
                if exists[mode]:
                    return mode
            
        raise Exception("无法识别题型，请检查界面。")

    def getPosition(self):
        """ 返回该从前面选 还是从后面 现用于构词法"""
        position_elements = self.d.xpath(f'//*[@resource-id="{self.ID_POSITION}"]').all()
        if not position_elements or len(position_elements) < 2: return 1
        
        pos1_text = position_elements[0].text
        pos2_text = position_elements[1].text
        if not pos1_text or not pos2_text: return 1 
        
        try:
            # 尝试提取得分或关卡的纯数字 (兼容 "第x关" 和 "x/y")
            match1 = re.search(r'\d+', pos1_text)
            match2 = re.search(r'\d+', pos2_text)
            if match1 and match2:
                pos1 = int(match1.group())
                pos2 = int(match2.group())
                return 1 if pos1 > pos2 else -1
            else:
                return 1
        except Exception:
            return 1

    def solveTitle(self, mode):
        if mode in self.TITLES:
            self.TITLES[mode]()

    def getTotal(self):
        """ 获得总题数 """
        title = self.d(resourceId=self.ID_POSITION).get_text()
        if not title:
            raise ValueError("未读取到题号文本")

        title = title.strip()
        
        match_king = re.search(r"第\s*\d+\s*关", title)
        if match_king:
            self.is_king_mode = True
            return 100
            
        self.is_king_mode = False
        match = re.search(r"(\d+)\s*/\s*(\d+)", title)
        if not match:
            raise ValueError(f"无法解析题号文本: {title!r}")

        current = int(match.group(1))
        total = int(match.group(2))
        if total < current:
            raise ValueError(f"题号异常: 当前题号({current})大于总题数({total})")

        return total - current + 1

    def __spellTitle(self):
        """ 解决拼写题型 """
        self.lastType = '拼写'
        
        all_yinbiao = self.d.xpath(f'//*[@resource-id="{self.ID_YINBIAO}"]').all()
        all_chinese = self.d.xpath(f'//*[@resource-id="{self.ID_CHINESE}"]').all()
        noteText = all_yinbiao[0].text if self.position == 1 else all_yinbiao[-1].text
        mean = self.reSaveChinese(all_chinese[0].text if self.position == 1 else all_chinese[-1].text)

        match = re.search(r"美\[(.+)\]", noteText)
        if not match:
            if self.is_king_mode:
                raise Exception("万词王模式人工介入: 拼写无法提取美式音标")
            self.report("warn", "无法提取美式音标", "已改为试错点击")
            self.d(resourceId=f"{self.pkg_name}:id/key_A").click()
            self.d(resourceId=self.ID_KEY_CONFIRM).click()
            time.sleep(3)
            return

        note_USA = match.group(1)
        words = self.searcher.noteSearchWord(note_USA)
        if not words: # 如果题库没找到
            if self.is_king_mode:
                raise Exception("万词王模式人工介入: 拼写未找到答案")
            self.report("warn", "题库未命中", "已改为试错点击")
            self.d(resourceId=f"{self.pkg_name}:id/key_A").click()
            self.d(resourceId=self.ID_KEY_CONFIRM).click()
            time.sleep(3)
            return
        
        word = words[0]
        if len(words) > 1:
            rates = []
            for w in words:
                answerList = self.searcher.getMeanFromWord(w)
                answerMean = self.reSaveChinese(''.join(answerList))
                rates.append(self.compareWordsMean(answerMean, mean))
            word = words[rates.index(max(rates))]

        # 与 fb_word_test 的拼写标准答案对齐（如 afterward(s) -> afterwards）
        word = self.searcher.resolveSpellingWord(word)

        for char in word:
            self.d(resourceId=f"{self.pkg_name}:id/key_{char.upper()}", clickable=True).click()
        self.d(resourceId=self.ID_KEY_CONFIRM).click()
        self.report("ok", word, "拼写")
        time.sleep(self.relaxTime)

    def __buildWord(self):
        """ 解决构词法拼词 """
        self.lastType = '构词法拼词'

        part_words = self.d.xpath(f'//*[@resource-id="{self.ID_PART_WORD}"]').all()
        part_word = part_words[0].text if self.position == 1 else part_words[-1].text
        
        all_chinese = self.d.xpath(f'//*[@resource-id="{self.ID_CHINESE}"]').all()
        question_mean = self.reSaveChinese(all_chinese[0].text if self.position == 1 else all_chinese[-1].text)

        clickable_text_views = self.d.xpath('//android.widget.TextView[@clickable="true"]').all()
        parts_on_screen = [elem.text for elem in clickable_text_views]
        
        # candidates 现在是这样的列表: [{'word': 'organise', 'parts_to_click': ['ise']}, ...]
        candidates = self.searcher.getPutAnswer(part_word, parts_on_screen)
        
        best_candidate_parts = []

        if not candidates:
            if self.is_king_mode:
                raise Exception("万词王模式人工介入: 构词法无答案")
            self.report("warn", "题库未命中", "构词法已随机点击")
            if clickable_text_views:
                clickable_text_views[randint(0, len(clickable_text_views)-1)].click()
            time.sleep(3)
            return

        elif len(candidates) == 1:
            best_candidate_parts = candidates[0]['parts_to_click']
            self.report("ok", candidates[0]['word'], "唯一候选")
        else:
            rates = []
            for cand in candidates:
                answer_means = self.searcher.getMeanFromWord(cand['word'])
                answer_mean_str = self.reSaveChinese(''.join(answer_means))
                rate = self.compareWordsMean(answer_mean_str, question_mean)
                rates.append(rate)
            
            best_choice_index = rates.index(max(rates))
            best_candidate_parts = candidates[best_choice_index]['parts_to_click']
            self.report("ok", candidates[best_choice_index]['word'], "多候选比对后命中")

        # 点击逻辑现在使用 'parts_to_click' 的值
        for part_to_click in best_candidate_parts:
            for elem in clickable_text_views:
                if elem.text == part_to_click:
                    elem.click()
                    break
        
        time.sleep(self.relaxTime)

    def __get_choice_elements(self):
        """ 封装获取选项A,B,C元素的操作 """
        choices = self.d.xpath('//android.widget.TextView[@clickable="true"]').all()
        option_choices = [c for c in choices if c.text and re.match(r'^[A-C]\.', c.text)]

        if len(option_choices) < 3:
            option_choices = [c for c in choices if c.text]
            if len(option_choices) < 3:
                 return None, None, None

        if self.position == 1:
            return option_choices[0], option_choices[1], option_choices[2]
        else:
            return option_choices[-3], option_choices[-2], option_choices[-1]

    def __englishToChinese(self):
        """ 解决英译汉 """
        self.lastType = '英译汉'
        
        english_words = self.d.xpath(f'//*[@resource-id="{self.ID_ENGLISH}"]').all()
        raw_word = english_words[0].text if self.position == 1 else english_words[-1].text
        # 如果 UI 包含了英标/换行，只取第一行的单词部分
        word = raw_word.split('\n')[0].strip() if raw_word else ''
        # 如果还在同一行包含英标等，则使用正则仅提取前面的纯英文、空格或连字符部分
        match = re.match(r"^[a-zA-Z\s\-\(\)\.\']+", word)
        if match:
            word = match.group(0).strip()
        
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            self.report("error", "选项获取失败", "已跳过")
            return

        resultList = self.searcher.getEnglishtoChinese(word)
        
        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                # 双向 in 匹配：题库答案可能比选项短（如 '决定；决心' vs '决定；决心；果断'）
                buttons_list = [choice_A, choice_B, choice_C]
                prefixes = ['A. ', 'B. ', 'C. ']
                for btn, prefix in zip(buttons_list, prefixes):
                    choice_text = btn.text.replace(prefix, '')
                    if choice_text in clean_result or clean_result in choice_text:
                        btn.click(); self.report("ok", choice_text, word)
                        time.sleep(self.relaxTime)
                        return
                # 兜底: 脱水到纯汉字后再比对（兼容全角/半角括号等符号差异）
                clean_result_cn = self.reSaveChinese(clean_result)
                for btn, prefix in zip(buttons_list, prefixes):
                    choice_cn = self.reSaveChinese(btn.text.replace(prefix, ''))
                    if choice_cn in clean_result_cn or clean_result_cn in choice_cn:
                        btn.click(); self.report("ok", btn.text.replace(prefix, ''), f"{word} · 汉字兜底")
                        time.sleep(self.relaxTime)
                        return

        answer_means = self.searcher.getMeanFromWord(word)
        
        buttons = [choice_A, choice_B, choice_C]
        choices_text = [c.text.replace(f'{chr(65+i)}. ', '') for i, c in enumerate(buttons)]
        rates = [0, 0, 0]
        for i, choice in enumerate(choices_text):
            cleaned_choice = self.reSaveChinese(choice.replace('；', ''))
            for answer_word in answer_means:
                cleaned_answer = self.reSaveChinese(answer_word)
                rate = self.compareWordsMean(cleaned_answer, cleaned_choice)
                if rate > rates[i]:
                    rates[i] = rate

        if max(rates) >= 0.5:
            best_choice_index = rates.index(max(rates))
            buttons[best_choice_index].click()
            self.report("info", choices_text[best_choice_index], f"{word} · 相似度匹配")
            time.sleep(self.relaxTime)
            return
        
        if self.is_king_mode:
            raise Exception("万词王模式人工介入: 英译汉无答案")
        buttons[randint(0, 2)].click()
        self.report("warn", "题库未命中", f"{word} · 已随机选择")
        time.sleep(3)
            
    def __question(self):
        """ 解决大杂烩 """
        self.lastType = '大杂烩'
        
        questions = self.d.xpath(f'//*[@resource-id="{self.ID_QUESTION}"]').all()
        text = questions[0].text if self.position == 1 else questions[-1].text
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            self.report("error", "选项获取失败", "已跳过")
            return

        clean_text = self.filter_chinese_and_english(text)
        
        if self.is_chinese(text):
            resultList = self.searcher.getChinesetoEnglish(clean_text) or self.searcher.getLongAnswer(clean_text)
        else:
            resultList = self.searcher.getLongAnswer(clean_text)

        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                if clean_result == choice_A.text.replace('A. ', ''):
                    choice_A.click(); self.report("ok", clean_result, "题库直出"); time.sleep(self.relaxTime); return
                elif clean_result == choice_B.text.replace('B. ', ''):
                    choice_B.click(); self.report("ok", clean_result, "题库直出"); time.sleep(self.relaxTime); return
                elif clean_result == choice_C.text.replace('C. ', ''):
                    choice_C.click(); self.report("ok", clean_result, "题库直出"); time.sleep(self.relaxTime); return
        
        if self.is_chinese(text):
            buttons = [choice_A, choice_B, choice_C]
            choices_text = [c.text.replace(f'{chr(65+i)}. ', '') for i, c in enumerate(buttons)]
            rates = [0, 0, 0]
            question_means = re.split(r'[;；,，、\(\)（）\s]+', text)
            question_means = [q for q in question_means if q]
            clean_question_tokens = [self.reSaveChinese(q) for q in question_means if self.reSaveChinese(q)]
            clean_question_full = self.reSaveChinese(text)
            if clean_question_full and clean_question_full not in clean_question_tokens:
                clean_question_tokens.append(clean_question_full)

            for i, choice_word in enumerate(choices_text):
                choice_means_list = self.searcher.getMeanFromWord(choice_word)
                for choice_mean in choice_means_list:
                    clean_choice_mean = self.reSaveChinese(choice_mean)
                    if not clean_choice_mean:
                        continue
                    for clean_q_mean in clean_question_tokens:
                        if not clean_q_mean:
                            continue
                        # 优先命中包含关系，例如“情节”可以命中“故事戏剧等中的情节”
                        if clean_choice_mean in clean_q_mean or clean_q_mean in clean_choice_mean:
                            rates[i] = max(rates[i], 1.0)
                            continue
                        rate = self.compareWordsMean(clean_q_mean, clean_choice_mean)
                        if rate > rates[i]:
                            rates[i] = rate
            
            if max(rates) >= 0.5:
                buttons[rates.index(max(rates))].click()
                self.report("info", choices_text[rates.index(max(rates))], "语义相似度匹配")
                time.sleep(self.relaxTime)
                return
        
        if self.is_king_mode:
            raise Exception("万词王模式人工介入: 大杂烩无答案")
        self.report("warn", "题库未命中", "已随机选择")
        choices = [choice_A, choice_B, choice_C]
        choices[randint(0, 2)].click()
        time.sleep(3)

    def __listen(self):
        self.lastType = '听音识词'
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            self.report("error", "选项获取失败", "已跳过")
            return
        
        choices_text_list = [
            choice_A.text.replace('A. ', '').strip(),
            choice_B.text.replace('B. ', '').strip(),
            choice_C.text.replace('C. ', '').strip()
        ]
        
        raw_answer_from_db = self.searcher.getListenAnswer(choices_text_list)
        
        if raw_answer_from_db:
            answer_from_db = raw_answer_from_db.strip().strip("'\"")
            choice_candidates = [
                (choice_A, {choice_A.text.strip(), choices_text_list[0]}),
                (choice_B, {choice_B.text.strip(), choices_text_list[1]}),
                (choice_C, {choice_C.text.strip(), choices_text_list[2]}),
            ]
            for button, valid_texts in choice_candidates:
                if answer_from_db in valid_texts:
                    button.click()
                    self.report("ok", answer_from_db, "题库直出")
                    time.sleep(self.relaxTime)
                    return

        if self.is_king_mode:
            raise Exception("万词王模式人工介入: 听音识词无答案")
        self.report("warn", "题库未命中", "已随机选择")
        choices = [choice_A, choice_B, choice_C]
        choices[randint(0, 2)].click()
        time.sleep(3)

    def reSaveChinese(self, mean):
        return ''.join(re.findall("[\u4e00-\u9fa5]+", mean))

    def filter_chinese_and_english(self, input_str):
        return ''.join(re.findall(r'[a-zA-Z\u4e00-\u9fa5]+', input_str))

    def compareWordsMean(self, word1, word2):
        return difflib.SequenceMatcher(None, word1, word2).quick_ratio()

    def is_chinese(self, string):
        return any('\u4e00' <= char <= '\u9fff' for char in string)

if __name__ == "__main__":
    try:
        relax_time = ask_relax_time(2.0)

        def connect_device():
            try:
                return u2.connect()
            except Exception as connect_e:
                if "Can't find any android device" in str(connect_e) or "emulator" in str(connect_e):
                    subprocess.run(["adb", "kill-server"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    time.sleep(1)
                    subprocess.run(["adb", "start-server"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    time.sleep(3)
                    return u2.connect()
                raise connect_e

        d = _run_with_spinner("初始化：连接 Android 设备", connect_device)
        app = _run_with_spinner(
            "初始化：加载题库与索引",
            lambda: U2VictorApp(d, relax_time=relax_time),
        )
        _gum_log("info", "FuckWeici 已启动", prefix="启动")
        _gum_log("info", f"设备={getattr(app.d, 'serial', '已连接')}", prefix="环境")
        _gum_log("info", f"题库={Path(app.searcher.db_path).resolve()}", prefix="环境")
        _gum_log("info", f"答题间隔={app.relaxTime:.2f}s 包名={app.pkg_name}", prefix="环境")
        _gum_log("info", "进入维词答题界面后确认开始；无法处理的题会提示手动接管。", prefix="提示")
    except Exception as exc:
        _gum_log("error", f"启动失败: {exc}\n\n请先确认 adb 已连接设备，且题库文件可以正常读取。", prefix="错误")
        raise SystemExit(1)

    try:
        while True:
            total_questions = wait_until_quiz_ready(app)
            solved_question_count = 0
            manual_question_count = 0
            total_elapsed_seconds = 0.0

            for i in range(total_questions):
                question_start_time = time.time()
                try:
                    title_type = app.tellTitle()
                    progress_label = f"{i + 1}/{total_questions}" if total_questions else str(i + 1)
                    _gum_log("info", f"{progress_label} {QUESTION_TITLES.get(title_type, '识别成功')}", prefix="题目")
                    app.solveTitle(title_type)
                    question_elapsed = time.time() - question_start_time
                    solved_question_count += 1
                    total_elapsed_seconds += question_elapsed
                except Exception as exc:
                    manual_question_count += 1
                    if "万词王模式人工介入" in str(exc):
                        label, level = STATUS.get("warn", ("兜底", "warn"))
                        _gum_log(level, f"需要人工接管 · {exc}", prefix=label)
                    else:
                        label, level = STATUS.get("error", ("失败", "error"))
                        _gum_log(level, f"本题未能自动完成 · {exc}", prefix=label)
                    wait_for_manual_resume("这一题脚本没有顺利完成。")

            app.runTime += 1
            app.lastType = ''
            average_seconds = total_elapsed_seconds / solved_question_count if solved_question_count else 0.0
            auto_rate = f"{(solved_question_count / total_questions) * 100:.0f}%" if total_questions else "0%"
            _gum_log(
                "info",
                f"第 {app.runTime} 轮 总题数={total_questions} 完成={solved_question_count} "
                f"人工={manual_question_count} 自动完成率={auto_rate} "
                f"总耗时={total_elapsed_seconds:.2f}s 平均每题={average_seconds:.2f}s",
                prefix="总结",
            )
            if not ask_continue_next_round():
                break
    except Exception as exc:
        _gum_log("error", f"运行中断: {str(exc) or '出现未知错误'}", prefix="错误")
        raise SystemExit(1)
# --- END OF FILE VictorApp.py ---
