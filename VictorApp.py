# --- START OF FILE VictorApp.py ---

import uiautomator2 as u2
import re
import time
import difflib
from random import randint
from SearchResult import SearchResult

# --- 导入LLM相关模块 ---
try:
    import config
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
        if LLM_AVAILABLE and config.LLM_ENABLED:
            self.llm_helper = LLMHelper()
            if self.llm_helper.is_enabled():
                log_info("LLM 辅助答题已启用。")
            else:
                log_warn("LLM 配置不完整或已禁用，辅助答题功能将不可用。")
        else:
            log_info("LLM 辅助答题已禁用。")
        # --- 结束初始化 ---

        self.lastType = ''
        self.position = 1
        self.runTime = 0
        try:
            user_input = input("请输入每一题的间隔秒数(可输入小数，回车默认为2s)>").strip()
            self.relaxTime = float(user_input) if user_input != '' else 2.0
            if self.relaxTime < 0:
                self.relaxTime = 2.0
        except Exception:
            self.relaxTime = 2.0

    def tellTitle(self):
        """ 辨别题型 """
        start_time = time.time()
        
        self.position = self.getPosition()
        
        # 使用 count 方法进行快速判断
        if (self.lastType != '拼写' and self.d(resourceId=self.ID_KEYBOARD).count == 1) or \
           (self.lastType == '拼写' and self.d(resourceId=self.ID_KEYBOARD).count == 2):
            vlog(f"题型: 拼写 | 识别耗时 {time.time() - start_time:.4f}s")
            return 1

        if (self.lastType != '构词法拼词' and self.d(resourceId=self.ID_PART_WORD).count == 1) or \
           (self.lastType == '构词法拼词' and self.d(resourceId=self.ID_PART_WORD).count == 2):
            vlog(f"题型: 构词法拼词 | 识别耗时 {time.time() - start_time:.4f}s")
            return 7

        if (self.lastType != '英译汉' and self.d(resourceId=self.ID_ENGLISH).count == 1) or \
           (self.lastType == '英译汉' and self.d(resourceId=self.ID_ENGLISH).count == 2):
            vlog(f"题型: 英译汉 | 识别耗时 {time.time() - start_time:.4f}s")
            return 2

        if (self.lastType != '大杂烩' and self.d(resourceId=self.ID_QUESTION).count == 1) or \
           (self.lastType == '大杂烩' and self.d(resourceId=self.ID_QUESTION).count == 2):
            vlog(f"题型: 大杂烩 | 识别耗时 {time.time() - start_time:.4f}s")
            return 345

        if (self.lastType != '听音识词' and self.d(resourceId=self.ID_SOUND).count == 1) or \
           (self.lastType == '听音识词' and self.d(resourceId=self.ID_SOUND).count == 2):
            vlog(f"题型: 听音识词 | 识别耗时 {time.time() - start_time:.4f}s")
            return 6
        
        # 增加重试机制，防止因页面加载延迟无法识别
        vlog("初次识别失败，进入重试…")
        for i in range(5):
            time.sleep(0.5)
            if self.d(resourceId=self.ID_KEYBOARD).exists: 
                vlog(f"'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 1
            if self.d(resourceId=self.ID_PART_WORD).exists: 
                vlog(f"'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 7
            if self.d(resourceId=self.ID_ENGLISH).exists:
                vlog(f"'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 2
            if self.d(resourceId=self.ID_QUESTION).exists:
                vlog(f"'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 345
            if self.d(resourceId=self.ID_SOUND).exists:
                vlog(f"'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 6
            
        raise Exception("无法识别题型，请检查界面。")

    def getPosition(self):
        """ 返回该从前面选 还是从后面 现用于构词法"""
        position_elements = self.d.xpath(f'//*[@resource-id="{self.ID_POSITION}"]').all()
        if not position_elements or len(position_elements) < 2: return 1
        
        pos1_text = position_elements[0].text
        pos2_text = position_elements[1].text
        if not pos1_text or not pos2_text: return 1 
        pos1 = int(pos1_text.split('/')[0])
        pos2 = int(pos2_text.split('/')[0])
        return 1 if pos1 > pos2 else -1

    def solveTitle(self, mode):
        if mode in self.TITLES:
            self.TITLES[mode]()

    def getTotal(self):
        """ 获得总题数 """
        start_time = time.time()
        title = self.d(resourceId=self.ID_POSITION).get_text()
        total = int(re.search("/(.+)", title).group(1))
        current = int(re.search("(.+)/", title).group(1))
        vlog(f"获取总题数耗时: {time.time() - start_time:.4f} 秒")
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
            # --- LLM 辅助 ---
            if self.llm_helper and self.llm_helper.is_enabled():
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
            log_warn("拼写: 无法提取美式音标，将试错")
            self.d(resourceId=f"{self.pkg_name}:id/key_A").click()
            self.d(resourceId=self.ID_KEY_CONFIRM).click()
            time.sleep(3)
            return

        note_USA = match.group(1)
        words = self.searcher.noteSearchWord(note_USA)
        if not words: # 如果题库没找到
            # --- LLM 辅助 ---
            if self.llm_helper and self.llm_helper.is_enabled():
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
        
        word = words[0]
        if len(words) > 1:
            rates = []
            for w in words:
                answerList = self.searcher.getMeanFromWord(w)
                answerMean = self.reSaveChinese(''.join(answerList))
                rates.append(self.compareWordsMean(answerMean, mean))
            word = words[rates.index(max(rates))]

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
        clickable_text_views = self.d.xpath('//android.widget.TextView[@clickable="true"]').all()
        parts = [elem.text for elem in clickable_text_views]
        
        resultList = self.searcher.getPutAnswer(part_word, parts, self.position)
        
        if not resultList:
            # --- LLM 辅助 ---
            if self.llm_helper and self.llm_helper.is_enabled():
                pieces_to_click = self.llm_helper.answer_build_word(part_word, parts)
                if pieces_to_click:
                    log_ok(f"构词法 (LLM): {part_word} + {''.join(pieces_to_click)}")
                    clicked_elements = []
                    for piece in pieces_to_click:
                        for elem in clickable_text_views:
                            if elem.text == piece:
                                clicked_elements.append(elem)
                                break
                    for elem in clicked_elements:
                        elem.click()
                    time.sleep(self.relaxTime)
                    return
                else:
                    log_warn("构词法: LLM 未能提供有效答案。")
            # --- 结束LLM ---
            log_warn("构词法: 无题库命中，将试错")
            if clickable_text_views:
                clickable_text_views[randint(0, len(clickable_text_views)-1)].click()
            time.sleep(3)
            return

        click_candidates = []
        source_elements = clickable_text_views if self.position == 1 else reversed(clickable_text_views)
        
        for elem in source_elements:
            if elem.text in resultList:
                click_candidates.append(elem)

        expected_combined = "".join(resultList).replace(part_word, '')
        clicked_text = "".join([elem.text for elem in click_candidates])
        if clicked_text != expected_combined:
            click_candidates.reverse()

        for elem in click_candidates:
            elem.click()
        log_ok(f"构词法: {part_word}")
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
        word = english_words[0].text if self.position == 1 else english_words[-1].text
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            log_err("英译汉: 选项获取失败，跳过")
            return

        resultList = self.searcher.getEnglishtoChinese(self.filter_chinese_and_english(word))
        
        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                if choice_A.text.replace('A. ', '') in clean_result:
                    choice_A.click(); log_ok(f"英译汉: {word} -> {choice_A.text.replace('A. ', '')}")
                    time.sleep(self.relaxTime)
                    return
                elif choice_B.text.replace('B. ', '') in clean_result:
                    choice_B.click(); log_ok(f"英译汉: {word} -> {choice_B.text.replace('B. ', '')}")
                    time.sleep(self.relaxTime)
                    return
                elif choice_C.text.replace('C. ', '') in clean_result:
                    choice_C.click(); log_ok(f"英译汉: {word} -> {choice_C.text.replace('C. ', '')}")
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

        if max(rates) > 0.5:
            best_choice_index = rates.index(max(rates))
            buttons[best_choice_index].click()
            log_info(f"英译汉: {word} -> 机器识别 {choices_text[best_choice_index]}")
            time.sleep(self.relaxTime)
            return

        # --- LLM 辅助 ---
        if self.llm_helper and self.llm_helper.is_enabled():
            question_text = f"单词 '{word}' 的中文意思是什么？"
            choices_dict = {'A': choice_A.text, 'B': choice_B.text, 'C': choice_C.text}
            answer_char = self.llm_helper.answer_choice_question(question_text, choices_dict)
            if answer_char == 'A':
                choice_A.click(); log_ok(f"英译汉 (LLM): {word} -> {choice_A.text}"); time.sleep(self.relaxTime); return
            elif answer_char == 'B':
                choice_B.click(); log_ok(f"英译汉 (LLM): {word} -> {choice_B.text}"); time.sleep(self.relaxTime); return
            elif answer_char == 'C':
                choice_C.click(); log_ok(f"英译汉 (LLM): {word} -> {choice_C.text}"); time.sleep(self.relaxTime); return
            else:
                log_warn("英译汉: LLM 未能提供有效答案。")
        # --- 结束LLM ---
        
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
            question_means = text.split('；')

            for i, choice_word in enumerate(choices_text):
                choice_means_list = self.searcher.getMeanFromWord(choice_word)
                for choice_mean in choice_means_list:
                    clean_choice_mean = self.reSaveChinese(choice_mean)
                    for q_mean in question_means:
                        rate = self.compareWordsMean(q_mean, clean_choice_mean)
                        if rate > rates[i]:
                            rates[i] = rate
            
            if max(rates) > 0.5:
                buttons[rates.index(max(rates))].click()
                log_info(f"大杂烩: 机器识别 -> {choices_text[rates.index(max(rates))]}")
                time.sleep(self.relaxTime)
                return
        
        # --- LLM 辅助 ---
        if self.llm_helper and self.llm_helper.is_enabled():
            choices_dict = {'A': choice_A.text, 'B': choice_B.text, 'C': choice_C.text}
            answer_char = self.llm_helper.answer_choice_question(text, choices_dict)
            if answer_char == 'A':
                choice_A.click(); log_ok(f"大杂烩 (LLM): {choice_A.text}"); time.sleep(self.relaxTime); return
            elif answer_char == 'B':
                choice_B.click(); log_ok(f"大杂烩 (LLM): {choice_B.text}"); time.sleep(self.relaxTime); return
            elif answer_char == 'C':
                choice_C.click(); log_ok(f"大杂烩 (LLM): {choice_C.text}"); time.sleep(self.relaxTime); return
            else:
                log_warn("大杂烩: LLM 未能提供有效答案。")
        # --- 结束LLM ---
        
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
        
        raw_answer_from_db = self.searcher.getListenAnswer(choices_text_list)
        
        if raw_answer_from_db:
            # 终极修复：移除空白字符，然后移除任何包裹字符串的引号
            answer_from_db = raw_answer_from_db.strip().strip("'\"")

            # 现在进行最干净、最可靠的比较
            if choice_A.text.strip() == answer_from_db:
                choice_A.click(); log_ok(f"听音识词: 命中题库 -> {answer_from_db}"); time.sleep(self.relaxTime); return
            elif choice_B.text.strip() == answer_from_db:
                choice_B.click(); log_ok(f"听音识词: 命中题库 -> {answer_from_db}"); time.sleep(self.relaxTime); return
            elif choice_C.text.strip() == answer_from_db:
                choice_C.click(); log_ok(f"听音识词: 命中题库 -> {answer_from_db}"); time.sleep(self.relaxTime); return

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
        d = u2.connect()
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