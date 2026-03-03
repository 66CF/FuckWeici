# --- START OF FILE VictorApp.py ---

import uiautomator2 as u2
import re
import time
import difflib
from random import randint
from SearchResult import SearchResult

# --- 导入LLM相关模块 ---
try:
    from config_loader import load_llm_settings
    from LLMHelper import LLMHelper
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
# --- 结束导入 ---


# --- Simple console styling (ANSI). Set VERBOSE=True to show timings ---
RESET = "\033[0m"
COLORS = {
    # New color palette based on the provided image
    # VISTA BLUE: RGB(124, 147, 206) - Used for 'blue' and 'cyan' (info)
    'blue': "\033[38;2;124;147;206m",
    'cyan': "\033[38;2;124;147;206m",

    # MYRTLE GREEN: RGB(52, 122, 115) - Used for 'green' (ok)
    'green': "\033[38;2;52;122;115m",
    
    # THISTLE: RGB(199, 182, 220) - Used for 'yellow' (warn) and 'magenta'
    'yellow': "\033[38;2;199;182;220m",
    'magenta': "\033[38;2;199;182;220m",

    # TEA ROSE (RED): RGB(252, 204, 201) - Used for 'red' (error)
    'red': "\033[38;2;252;204;201m",
    
    # BRUNSWICK GREEN: RGB(1, 73, 68) - Used for 'gray' (verbose)
    'gray': "\033[38;2;1;73;68m",
    
    'bold': "\033[1m",
}

VERBOSE = True

def _c(text, color=None, bold=False):
    prefix = COLORS['bold'] if bold else ''
    if color and color in COLORS:
        prefix += COLORS[color]
    return f"{prefix}{text}{RESET}" if prefix else text

def log_info(msg):
    print(f"{_c('[i]', 'cyan', True)} {msg}")

def log_ok(msg):
    print(f"{_c('[✓]', 'green', True)} {msg}")

def log_warn(msg):
    print(f"{_c('[!]', 'yellow', True)} {msg}")

def log_err(msg):
    print(f"{_c('[x]', 'red', True)} {msg}")

def vlog(msg):
    if VERBOSE:
        print(f"{_c('[v]', 'gray')} {msg}")

class U2VictorApp:
    def __init__(self, device):
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
        # --- 初始化 LLM 助手 ---
        self.llm_helper = None
        self.llm_full_mode = False
        if LLM_AVAILABLE:
            llm_settings = load_llm_settings()
            if llm_settings.get("created_config"):
                log_warn(f"未找到 config.py，已自动生成: {llm_settings.get('config_path')}")
                log_warn("请填写 LLM_BASE_URL / LLM_MODEL（如需远程模型再填 LLM_API_KEY）后重启程序。")
            self.llm_helper = LLMHelper(llm_settings)
            if self.llm_helper.is_enabled():
                log_info("LLM 辅助答题已启用。")
                self.llm_full_mode = self.llm_helper.is_full_mode()
                if self.llm_full_mode:
                    log_info("全LLM辅助模式已启用：优先使用 LLM 作答。")
            elif llm_settings.get("enabled"):
                log_warn("LLM 已开启但配置不完整，辅助答题功能将不可用。")
                log_warn(f"配置文件位置: {llm_settings.get('config_path')}")
            else:
                log_info("LLM 辅助答题已禁用。")
        else:
            log_warn("LLM 组件加载失败，辅助答题功能不可用。")
        # --- 结束初始化 ---

        self.lastType = ''
        self.is_king_mode = False
        self.position = 1
        self.runTime = 0
        try:
            user_input = input("请输入每一题的间隔秒数(可输入小数，回车默认为2s)>").strip()
            self.relaxTime = float(user_input) if user_input != '' else 2.0
            if self.relaxTime < 0:
                self.relaxTime = 2.0
        except Exception:
            self.relaxTime = 2.0

    def _expected_count(self, title_name):
        return 2 if self.lastType == title_name else 1

    def _is_llm_enabled(self):
        return self.llm_helper and self.llm_helper.is_enabled()

    def _click_choice_by_answer_char(self, answer_char, choice_A, choice_B, choice_C, log_prefix):
        if answer_char == 'A':
            choice_A.click(); log_ok(f"{log_prefix}: {choice_A.text}"); time.sleep(self.relaxTime); return True
        if answer_char == 'B':
            choice_B.click(); log_ok(f"{log_prefix}: {choice_B.text}"); time.sleep(self.relaxTime); return True
        if answer_char == 'C':
            choice_C.click(); log_ok(f"{log_prefix}: {choice_C.text}"); time.sleep(self.relaxTime); return True
        return False

    def _try_llm_choice(self, question_text, choice_A, choice_B, choice_C, log_prefix):
        if not self._is_llm_enabled():
            return False
        choices_dict = {'A': choice_A.text, 'B': choice_B.text, 'C': choice_C.text}
        answer_char = self.llm_helper.answer_choice_question(question_text, choices_dict)
        if self._click_choice_by_answer_char(answer_char, choice_A, choice_B, choice_C, log_prefix):
            return True
        log_warn(f"{log_prefix}: LLM 未能提供有效答案。")
        return False

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
        start_time = time.time()
        
        self.position = self.getPosition()

        counts = self._get_title_counts()

        if counts[1] == self._expected_count('拼写'):
            vlog(f"题型: 拼写 | 识别耗时 {time.time() - start_time:.4f}s")
            return 1

        if counts[7] == self._expected_count('构词法拼词'):
            vlog(f"题型: 构词法拼词 | 识别耗时 {time.time() - start_time:.4f}s")
            return 7

        if counts[2] == self._expected_count('英译汉'):
            vlog(f"题型: 英译汉 | 识别耗时 {time.time() - start_time:.4f}s")
            return 2

        if counts[345] == self._expected_count('大杂烩'):
            vlog(f"题型: 大杂烩 | 识别耗时 {time.time() - start_time:.4f}s")
            return 345

        if counts[6] == self._expected_count('听音识词'):
            vlog(f"题型: 听音识词 | 识别耗时 {time.time() - start_time:.4f}s")
            return 6
        
        # 增加重试机制，防止因页面加载延迟无法识别
        vlog("初次识别失败，进入重试…")
        for _ in range(5):
            time.sleep(0.5)
            exists = self._get_title_exists()
            for mode in (1, 7, 2, 345, 6):
                if exists[mode]:
                    vlog(f"'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
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
        start_time = time.time()
        title = self.d(resourceId=self.ID_POSITION).get_text()
        if not title:
            raise ValueError("未读取到题号文本")

        title = title.strip()
        
        match_king = re.search(r"第\s*\d+\s*关", title)
        if match_king:
            self.is_king_mode = True
            vlog(f"进入万词王模式: 获取总题数耗时: {time.time() - start_time:.4f} 秒")
            return 100
            
        self.is_king_mode = False
        match = re.search(r"(\d+)\s*/\s*(\d+)", title)
        if not match:
            raise ValueError(f"无法解析题号文本: {title!r}")

        current = int(match.group(1))
        total = int(match.group(2))
        if total < current:
            raise ValueError(f"题号异常: 当前题号({current})大于总题数({total})")

        vlog(f"获取总题数耗时: {time.time() - start_time:.4f} 秒")
        return total - current + 1

    def __spellTitle(self):
        """ 解决拼写题型 """
        self.lastType = '拼写'
        
        all_yinbiao = self.d.xpath(f'//*[@resource-id="{self.ID_YINBIAO}"]').all()
        all_chinese = self.d.xpath(f'//*[@resource-id="{self.ID_CHINESE}"]').all()
        noteText = all_yinbiao[0].text if self.position == 1 else all_yinbiao[-1].text
        mean = self.reSaveChinese(all_chinese[0].text if self.position == 1 else all_chinese[-1].text)
        llm_tried = False

        if self.llm_full_mode and self._is_llm_enabled():
            llm_tried = True
            word = self.llm_helper.answer_spelling(mean, noteText)
            if word:
                log_ok(f"拼写 (LLM): {word}")
                for char in word:
                    self.d(resourceId=f"{self.pkg_name}:id/key_{char.upper()}", clickable=True).click()
                self.d(resourceId=self.ID_KEY_CONFIRM).click()
                time.sleep(self.relaxTime)
                return
            log_warn("拼写: 全LLM模式未能提供有效答案，回退题库。")

        match = re.search(r"美\[(.+)\]", noteText)
        if not match:
            # --- LLM 辅助 ---
            if not llm_tried and self._is_llm_enabled():
                word = self.llm_helper.answer_spelling(mean, noteText)
                if word:
                    log_ok(f"拼写 (LLM): {word}")
                    for char in word:
                        self.d(resourceId=f"{self.pkg_name}:id/key_{char.upper()}", clickable=True).click()
                    self.d(resourceId=self.ID_KEY_CONFIRM).click()
                    time.sleep(self.relaxTime)
                    return
                else:
                    log_warn("拼写: LLM 未能提供有效答案。")
            # --- 结束LLM ---
            if self.is_king_mode:
                raise Exception("万词王模式人工介入: 拼写无法提取美式音标")
            log_warn("拼写: 无法提取美式音标，将试错")
            self.d(resourceId=f"{self.pkg_name}:id/key_A").click()
            self.d(resourceId=self.ID_KEY_CONFIRM).click()
            time.sleep(3)
            return

        note_USA = match.group(1)
        words = self.searcher.noteSearchWord(note_USA)
        if not words: # 如果题库没找到
            # --- LLM 辅助 ---
            if not llm_tried and self._is_llm_enabled():
                word = self.llm_helper.answer_spelling(mean, noteText)
                if word:
                    log_ok(f"拼写 (LLM): {word}")
                    for char in word:
                        self.d(resourceId=f"{self.pkg_name}:id/key_{char.upper()}", clickable=True).click()
                    self.d(resourceId=self.ID_KEY_CONFIRM).click()
                    time.sleep(self.relaxTime)
                    return
                else:
                    log_warn("拼写: LLM 未能提供有效答案。")
            # --- 结束LLM ---
            if self.is_king_mode:
                raise Exception("万词王模式人工介入: 拼写未找到答案")
            log_warn("拼写: 无答案，将试错")
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
        log_ok(f"拼写: {word}")
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
        llm_tried = False

        if self.llm_full_mode and self._is_llm_enabled():
            llm_tried = True
            llm_parts = self.llm_helper.answer_build_word(part_word, parts_on_screen)
            if llm_parts:
                log_ok(f"构词法 (LLM): 点击 {' + '.join(llm_parts)}")
                for part_to_click in llm_parts:
                    for elem in clickable_text_views:
                        if elem.text == part_to_click:
                            elem.click()
                            break
                time.sleep(self.relaxTime)
                return
            log_warn("构词法: 全LLM模式未能提供有效答案，回退题库。")
        
        # candidates 现在是这样的列表: [{'word': 'organise', 'parts_to_click': ['ise']}, ...]
        candidates = self.searcher.getPutAnswer(part_word, parts_on_screen, self.position)
        
        best_candidate_parts = []

        if not candidates:
            if not llm_tried and self._is_llm_enabled():
                llm_parts = self.llm_helper.answer_build_word(part_word, parts_on_screen)
                if llm_parts:
                    log_ok(f"构词法 (LLM): 点击 {' + '.join(llm_parts)}")
                    for part_to_click in llm_parts:
                        for elem in clickable_text_views:
                            if elem.text == part_to_click:
                                elem.click()
                                break
                    time.sleep(self.relaxTime)
                    return
                log_warn("构词法: LLM 未能提供有效答案。")
            if self.is_king_mode:
                raise Exception("万词王模式人工介入: 构词法无答案")
            log_warn("构词法: 无题库命中，将试错")
            if clickable_text_views:
                clickable_text_views[randint(0, len(clickable_text_views)-1)].click()
            time.sleep(3)
            return

        elif len(candidates) == 1:
            best_candidate_parts = candidates[0]['parts_to_click']
            log_info(f"构词法: 唯一候选 -> {candidates[0]['word']}") # 日志现在会打印正确的单词
        else:
            log_info(f"构词法: 发现多个候选，开始比对释义...")
            rates = []
            for cand in candidates:
                # **核心修正**：cand['word'] 现在是字符串 "organise"，可以被正确处理
                answer_means = self.searcher.getMeanFromWord(cand['word'])
                answer_mean_str = self.reSaveChinese(''.join(answer_means))
                rate = self.compareWordsMean(answer_mean_str, question_mean)
                rates.append(rate)
                # 日志现在会打印正确的单词
                vlog(f"  -> 候选 '{cand['word']}' (释义: {answer_mean_str[:20]}...) 相似度: {rate:.4f}")
            
            best_choice_index = rates.index(max(rates))
            # 从最佳候选者中获取需要点击的部分
            best_candidate_parts = candidates[best_choice_index]['parts_to_click']
            # 日志现在会打印正确的单词
            log_ok(f"构词法: 智能识别 -> {candidates[best_choice_index]['word']}")

        # 点击逻辑现在使用 'parts_to_click' 的值
        for part_to_click in best_candidate_parts:
            for elem in clickable_text_views:
                if elem.text == part_to_click:
                    elem.click()
                    break
        
        time.sleep(self.relaxTime)

    def __get_choice_elements(self):
        """ 封装获取选项A,B,C元素的操作 """
        start_time = time.time()
        choices = self.d.xpath('//android.widget.TextView[@clickable="true"]').all()
        option_choices = [c for c in choices if c.text and re.match(r'^[A-C]\.', c.text)]

        if len(option_choices) < 3:
            option_choices = [c for c in choices if c.text]
            if len(option_choices) < 3:
                 return None, None, None
            
        vlog(f"__get_choice_elements 获取选项耗时: {time.time() - start_time:.4f} 秒")
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
            log_err("英译汉: 选项获取失败，跳过")
            return

        print(f"[{self.lastType}] 提取原始英文: {repr(raw_word)}")
        print(f"[{self.lastType}] 分割后单英文: {repr(word)}")
        print(f"[{self.lastType}] 选项A: {repr(choice_A.text)}")
        print(f"[{self.lastType}] 选项B: {repr(choice_B.text)}")
        print(f"[{self.lastType}] 选项C: {repr(choice_C.text)}")

        if self.llm_full_mode:
            question_text = f"单词 '{word}' 的中文意思是什么？"
            if self._try_llm_choice(question_text, choice_A, choice_B, choice_C, f"英译汉 (LLM优先) {word}"):
                return

        resultList = self.searcher.getEnglishtoChinese(word)
        print(f"[{self.lastType}] 题库直接匹配结果: {resultList}")
        
        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                print(f"[{self.lastType}] 检查 clean_result: {repr(clean_result)}")
                # 双向 in 匹配：题库答案可能比选项短（如 '决定；决心' vs '决定；决心；果断'）
                buttons_list = [choice_A, choice_B, choice_C]
                prefixes = ['A. ', 'B. ', 'C. ']
                for btn, prefix in zip(buttons_list, prefixes):
                    choice_text = btn.text.replace(prefix, '')
                    if choice_text in clean_result or clean_result in choice_text:
                        btn.click(); log_ok(f"英译汉: {word} -> {choice_text}")
                        time.sleep(self.relaxTime)
                        return
                # 兜底: 脱水到纯汉字后再比对（兼容全角/半角括号等符号差异）
                clean_result_cn = self.reSaveChinese(clean_result)
                for btn, prefix in zip(buttons_list, prefixes):
                    choice_cn = self.reSaveChinese(btn.text.replace(prefix, ''))
                    if choice_cn in clean_result_cn or clean_result_cn in choice_cn:
                        btn.click(); log_ok(f"英译汉: {word} -> {btn.text.replace(prefix, '')} (汉字兜底)")
                        time.sleep(self.relaxTime)
                        return

        answer_means = self.searcher.getMeanFromWord(word)
        print(f"[{self.lastType}] 题库搜索 word 的含义: {answer_means}")
        
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
                    
        print(f"[{self.lastType}] 相似度: {rates}")


        if max(rates) >= 0.5:
            best_choice_index = rates.index(max(rates))
            buttons[best_choice_index].click()
            log_info(f"英译汉: {word} -> 机器识别 {choices_text[best_choice_index]}")
            time.sleep(self.relaxTime)
            return

        # --- LLM 辅助 ---
        if self._is_llm_enabled():
            question_text = f"单词 '{word}' 的中文意思是什么？"
            if self._try_llm_choice(question_text, choice_A, choice_B, choice_C, f"英译汉 (LLM) {word}"):
                return
        # --- 结束LLM ---
        
        if self.is_king_mode:
            raise Exception("万词王模式人工介入: 英译汉无答案")
        buttons[randint(0, 2)].click()
        log_warn("英译汉: 无答案，将试错")
        time.sleep(3)
            
    def __question(self):
        """ 解决大杂烩 """
        self.lastType = '大杂烩'
        
        questions = self.d.xpath(f'//*[@resource-id="{self.ID_QUESTION}"]').all()
        text = questions[0].text if self.position == 1 else questions[-1].text
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            log_err("大杂烩: 选项获取失败，跳过")
            return

        clean_text = self.filter_chinese_and_english(text)

        if self.llm_full_mode:
            if self._try_llm_choice(text, choice_A, choice_B, choice_C, "大杂烩 (LLM优先)"):
                return
        
        if self.is_chinese(text):
            vlog('大杂烩子类: 汉译英')
            resultList = self.searcher.getChinesetoEnglish(clean_text) or self.searcher.getLongAnswer(clean_text)
        else:
            vlog('大杂烩子类: 复杂语境')
            resultList = self.searcher.getLongAnswer(clean_text)

        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                if clean_result == choice_A.text.replace('A. ', ''):
                    choice_A.click(); log_ok(f"大杂烩: 命中题库 -> {clean_result}"); time.sleep(self.relaxTime); return
                elif clean_result == choice_B.text.replace('B. ', ''):
                    choice_B.click(); log_ok(f"大杂烩: 命中题库 -> {clean_result}"); time.sleep(self.relaxTime); return
                elif clean_result == choice_C.text.replace('C. ', ''):
                    choice_C.click(); log_ok(f"大杂烩: 命中题库 -> {clean_result}"); time.sleep(self.relaxTime); return
        
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
                log_info(f"大杂烩: 机器识别 -> {choices_text[rates.index(max(rates))]}")
                time.sleep(self.relaxTime)
                return
        
        # --- LLM 辅助 ---
        if self._is_llm_enabled():
            if self._try_llm_choice(text, choice_A, choice_B, choice_C, "大杂烩 (LLM)"):
                return
        # --- 结束LLM ---
        
        if self.is_king_mode:
            raise Exception("万词王模式人工介入: 大杂烩无答案")
        log_warn("大杂烩: 无答案，将试错")
        choices = [choice_A, choice_B, choice_C]
        choices[randint(0, 2)].click()
        time.sleep(3)

    def __listen(self):
        self.lastType = '听音识词'
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            log_err("听音识词: 选项获取失败，跳过")
            return
        
        choices_text_list = [
            choice_A.text.replace('A. ', '').strip(),
            choice_B.text.replace('B. ', '').strip(),
            choice_C.text.replace('C. ', '').strip()
        ]

        if self.llm_full_mode:
            question_text = "听音识词题：请根据发音在选项中选择正确单词。"
            if self._try_llm_choice(question_text, choice_A, choice_B, choice_C, "听音识词 (LLM优先)"):
                return
        
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
                    log_ok(f"听音识词: 命中题库 -> {answer_from_db}")
                    time.sleep(self.relaxTime)
                    return

        if self._is_llm_enabled():
            question_text = "听音识词题：请根据发音在选项中选择正确单词。"
            if self._try_llm_choice(question_text, choice_A, choice_B, choice_C, "听音识词 (LLM)"):
                return

        if self.is_king_mode:
            raise Exception("万词王模式人工介入: 听音识词无答案")
        log_warn("听音识词: 题库未命中，将随机选择")
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
        connect_start_time = time.time()
        try:
            d = u2.connect()
        except Exception as connect_e:
            if "Can't find any android device" in str(connect_e) or "emulator" in str(connect_e):
                log_warn("未找到设备，尝试重启 adb 服务...")
                import subprocess
                subprocess.run(["adb", "kill-server"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                time.sleep(1)
                subprocess.run(["adb", "start-server"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                time.sleep(3)
                log_info("重启 adb 成功，重新尝试连接...")
                d = u2.connect()
            else:
                raise connect_e
                
        log_ok(f"设备连接成功 ({d.device_info})")
        # 实例化 app 对象时，SearchResult 的 __init__ 会被调用并打印其耗时
        app_init_start_time = time.time()
        app = U2VictorApp(d)
        vlog(f"U2VictorApp 初始化完成, 耗时: {time.time() - app_init_start_time:.4f} 秒")
        
    except Exception as e:
        log_err(f"初始化失败，请检查设备连接和uiautomator2环境: {e}")
        input("按回车键退出...")
        exit()

    while True:
        if input("准备好了吗? (输入 'n' 退出程序) > ") != 'n':
            try:
                total_questions = app.getTotal()
                log_info(f"检测到共 {total_questions} 题")
                solved_question_count = 0
                total_elapsed_seconds = 0.0
                for i in range(total_questions):
                    question_start_time = time.time()
                    print(_c(f"\n第 {i+1}/{total_questions} 题", 'blue', True))
                    try:
                        title_type = app.tellTitle()
                        app.solveTitle(title_type)
                    except Exception as e:
                        if "万词王模式人工介入" in str(e):
                            log_warn(str(e))
                            log_warn('请手动完成这一题后，按回车键继续...')
                            input()
                            continue
                        log_err(f'发生错误，请手动完成一题后按回车继续: {e}')
                        import traceback
                        traceback.print_exc()
                        input()
                        continue
                    # 打印单题总耗时
                    question_elapsed = time.time() - question_start_time
                    vlog(f"第 {i+1} 题耗时: {question_elapsed:.4f} 秒")
                    solved_question_count += 1
                    total_elapsed_seconds += question_elapsed
                
                if solved_question_count > 0:
                    average_time_per_question = total_elapsed_seconds / solved_question_count
                    log_ok(f"完成 {solved_question_count} 题 | 平均 {average_time_per_question:.2f}s/题")

                app.runTime += 1
                app.lastType = ''
                log_info(f"完成第 {app.runTime} 轮")
            except Exception as e:
                log_err(f"获取总题数或开始时发生错误: {e}")
                input("按回车键重试...")
        else:
            break
# --- END OF FILE VictorApp.py ---
