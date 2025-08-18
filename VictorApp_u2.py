# --- START OF FILE VictorApp_u2.py (Optimized) ---

import uiautomator2 as u2
import re
import time
import difflib
from random import randint
from SearchResult import SearchResult

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
            print("识别为: 拼写")
            print(f"    - [UI识别] 'tellTitle' 耗时: {time.time() - start_time:.4f} 秒")
            return 1

        if (self.lastType != '构词法拼词' and self.d(resourceId=self.ID_PART_WORD).count == 1) or \
           (self.lastType == '构词法拼词' and self.d(resourceId=self.ID_PART_WORD).count == 2):
            print("识别为: 构词法拼词")
            print(f"    - [UI识别] 'tellTitle' 耗时: {time.time() - start_time:.4f} 秒")
            return 7

        if (self.lastType != '英译汉' and self.d(resourceId=self.ID_ENGLISH).count == 1) or \
           (self.lastType == '英译汉' and self.d(resourceId=self.ID_ENGLISH).count == 2):
            print("识别为: 英译汉")
            print(f"    - [UI识别] 'tellTitle' 耗时: {time.time() - start_time:.4f} 秒")
            return 2

        if (self.lastType != '大杂烩' and self.d(resourceId=self.ID_QUESTION).count == 1) or \
           (self.lastType == '大杂烩' and self.d(resourceId=self.ID_QUESTION).count == 2):
            print("识别为: 大杂烩")
            print(f"    - [UI识别] 'tellTitle' 耗时: {time.time() - start_time:.4f} 秒")
            return 345

        if (self.lastType != '听音识词' and self.d(resourceId=self.ID_SOUND).count == 1) or \
           (self.lastType == '听音识词' and self.d(resourceId=self.ID_SOUND).count == 2):
            print("识别为: 听音识词")
            print(f"    - [UI识别] 'tellTitle' 耗时: {time.time() - start_time:.4f} 秒")
            return 6
        
        # 增加重试机制，防止因页面加载延迟无法识别
        print("    - [UI识别] 初次识别失败，进入重试...")
        for i in range(5):
            time.sleep(0.5)
            if self.d(resourceId=self.ID_KEYBOARD).exists: 
                print(f"    - [UI识别] 'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 1
            if self.d(resourceId=self.ID_PART_WORD).exists: 
                print(f"    - [UI识别] 'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 7
            if self.d(resourceId=self.ID_ENGLISH).exists:
                print(f"    - [UI识别] 'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 2
            if self.d(resourceId=self.ID_QUESTION).exists:
                print(f"    - [UI识别] 'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
                return 345
            if self.d(resourceId=self.ID_SOUND).exists:
                print(f"    - [UI识别] 'tellTitle' 重试成功, 总耗时: {time.time() - start_time:.4f} 秒")
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
        print(f"[性能分析] 获取总题数耗时: {time.time() - start_time:.4f} 秒")
        return total - current + 1

    def __spellTitle(self):
        """ 解决拼写题型 """
        self.lastType = '拼写'
        
        # 计时UI元素获取
        ui_fetch_start = time.time()
        all_yinbiao = self.d.xpath(f'//*[@resource-id="{self.ID_YINBIAO}"]').all()
        all_chinese = self.d.xpath(f'//*[@resource-id="{self.ID_CHINESE}"]').all()
        noteText = all_yinbiao[0].text if self.position == 1 else all_yinbiao[-1].text
        mean = self.reSaveChinese(all_chinese[0].text if self.position == 1 else all_chinese[-1].text)
        print(f"    - [UI交互] 获取音标和中文意思耗时: {time.time() - ui_fetch_start:.4f} 秒")

        match = re.search(r"美\[(.+)\]", noteText)
        if not match:
            print(f"无法从 '{noteText}' 中提取美式音标，试错跳过。")
            self.d(resourceId=f"{self.pkg_name}:id/key_A").click()
            self.d(resourceId=self.ID_KEY_CONFIRM).click()
            time.sleep(3)
            return

        note_USA = match.group(1)
        
        # 计时数据查找
        search_start = time.time()
        words = self.searcher.noteSearchWord(note_USA)
        word = words[0]
        if len(words) > 1:
            rates = []
            for w in words:
                answerList = self.searcher.getMeanFromWord(w)
                answerMean = self.reSaveChinese(''.join(answerList))
                rates.append(self.compareWordsMean(answerMean, mean))
            word = words[rates.index(max(rates))]
        print(f"    - [数据处理] 根据音标和意思查找单词耗时: {time.time() - search_start:.4f} 秒, 结果: {word}")

        # 计时模拟点击
        click_start = time.time()
        for char in word:
            self.d(resourceId=f"{self.pkg_name}:id/key_{char.upper()}", clickable=True).click()
        # time.sleep(0.1)
        self.d(resourceId=self.ID_KEY_CONFIRM).click()
        print(f"    - [UI交互] 模拟键盘输入耗时: {time.time() - click_start:.4f} 秒")
        
        print("————————机器识别")
        time.sleep(self.relaxTime)

    def __buildWord(self):
        """ 解决构词法拼词 """
        self.lastType = '构词法拼词'

        # 计时UI元素获取
        ui_fetch_start = time.time()
        part_words = self.d.xpath(f'//*[@resource-id="{self.ID_PART_WORD}"]').all()
        part_word = part_words[0].text if self.position == 1 else part_words[-1].text
        clickable_text_views = self.d.xpath('//android.widget.TextView[@clickable="true"]').all()
        parts = [elem.text for elem in clickable_text_views]
        print(f"    - [UI交互] 获取构词法题目元素耗时: {time.time() - ui_fetch_start:.4f} 秒")
        
        # 数据查找过程已在 SearchResult 中计时，这里只调用
        resultList = self.searcher.getPutAnswer(part_word, parts, self.position)
        
        if not resultList:
            print("————————无答案 试错")
            if clickable_text_views:
                clickable_text_views[randint(0, len(clickable_text_views)-1)].click()
            time.sleep(3)
            return

        # 计时模拟点击
        click_start = time.time()
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
        print(f"    - [UI交互] 模拟点击构词法选项耗时: {time.time() - click_start:.4f} 秒")

        print("————————题库获取")
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
            
        print(f"    - [UI交互] __get_choice_elements 获取选项耗时: {time.time() - start_time:.4f} 秒")
        if self.position == 1:
            return option_choices[0], option_choices[1], option_choices[2]
        else:
            return option_choices[-3], option_choices[-2], option_choices[-1]

    def __englishToChinese(self):
        """ 解决英译汉 """
        self.lastType = '英译汉'
        
        # 计时UI元素获取
        ui_fetch_start = time.time()
        english_words = self.d.xpath(f'//*[@resource-id="{self.ID_ENGLISH}"]').all()
        word = english_words[0].text if self.position == 1 else english_words[-1].text
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            print("选项元素获取失败，跳过")
            return
        print(f"    - [UI交互] 获取英译汉题目和选项耗时: {time.time() - ui_fetch_start:.4f} 秒")

        # 计时题库查找
        db_search_start = time.time()
        resultList = self.searcher.getEnglishtoChinese(self.filter_chinese_and_english(word))
        print(f"    - [数据处理] 题库查找(getEnglishtoChinese)耗时: {time.time() - db_search_start:.4f} 秒")
        
        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                if choice_A.text.replace('A. ', '') in clean_result:
                    choice_A.click()
                    print("————————题库获取")
                    time.sleep(self.relaxTime)
                    return
                elif choice_B.text.replace('B. ', '') in clean_result:
                    choice_B.click()
                    print("————————题库获取")
                    time.sleep(self.relaxTime)
                    return
                elif choice_C.text.replace('C. ', '') in clean_result:
                    choice_C.click()
                    print("————————题库获取")
                    time.sleep(self.relaxTime)
                    return

        # 计时机器识别（如果题库未命中）
        rec_search_start = time.time()
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
        print(f"    - [数据处理] 机器识别(相似度计算)耗时: {time.time() - rec_search_start:.4f} 秒")

        if max(rates) > 0.5:
            best_choice_index = rates.index(max(rates))
            buttons[best_choice_index].click()
            print("————————机器识别")
            time.sleep(self.relaxTime)
        else:
            buttons[randint(0, 2)].click()
            print("————————无答案 试错")
            time.sleep(3)
            
    # 其他函数 __question, __listen 也可仿照上述方法添加计时，此处省略以保持简洁

    # ... (此处省略 __question 和 __listen 的修改，您可以仿照上面的例子自行添加)
    # ...
    def __question(self):
        """ 解决大杂烩 """
        self.lastType = '大杂烩'
        
        # 计时UI元素获取
        ui_fetch_start = time.time()
        questions = self.d.xpath(f'//*[@resource-id="{self.ID_QUESTION}"]').all()
        text = questions[0].text if self.position == 1 else questions[-1].text
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            print("选项元素获取失败，跳过")
            return
        print(f"    - [UI交互] 获取大杂烩题目和选项耗时: {time.time() - ui_fetch_start:.4f} 秒")

        # 计时数据处理和查找
        search_start = time.time()
        clean_text = self.filter_chinese_and_english(text)
        
        if self.is_chinese(text):
            print('————汉译英')
            resultList = self.searcher.getChinesetoEnglish(clean_text) or self.searcher.getLongAnswer(clean_text)
        else:
            print('————复杂语境')
            resultList = self.searcher.getLongAnswer(clean_text)
        print(f"    - [数据处理] 题库查找耗时: {time.time() - search_start:.4f} 秒")

        if resultList:
            for result in resultList:
                clean_result = result[4:-1]
                if clean_result == choice_A.text.replace('A. ', ''):
                    choice_A.click(); print("————————题库获取"); time.sleep(self.relaxTime); return
                elif clean_result == choice_B.text.replace('B. ', ''):
                    choice_B.click(); print("————————题库获取"); time.sleep(self.relaxTime); return
                elif clean_result == choice_C.text.replace('C. ', ''):
                    choice_C.click(); print("————————题库获取"); time.sleep(self.relaxTime); return
        
        if self.is_chinese(text):
            # 计时机器识别
            rec_start_time = time.time()
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
            print(f"    - [数据处理] 机器识别(相似度计算)耗时: {time.time() - rec_start_time:.4f} 秒")
            
            if max(rates) > 0.5:
                buttons[rates.index(max(rates))].click()
                print("————————机器识别")
                time.sleep(self.relaxTime)
                return

        print("————————无答案 通过试错系统")
        choices = [choice_A, choice_B, choice_C]
        choices[randint(0, 2)].click()
        time.sleep(3)

    def __listen(self):
        self.lastType = '听音识词'
        choice_A, choice_B, choice_C = self.__get_choice_elements()
        if not all([choice_A, choice_B, choice_C]):
            print("选项元素获取失败，跳过")
            return
        
        print("听力题暂不支持作答————通过试错系统")
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
        print(f"设备连接成功: {d.device_info}, 耗时: {time.time() - connect_start_time:.4f} 秒")
        # 实例化 app 对象时，SearchResult 的 __init__ 会被调用并打印其耗时
        app_init_start_time = time.time()
        app = U2VictorApp(d)
        print(f"U2VictorApp 初始化完成, 耗时: {time.time() - app_init_start_time:.4f} 秒")
        
    except Exception as e:
        print(f"初始化失败，请检查设备连接和uiautomator2环境: {e}")
        input("按回车键退出...")
        exit()

    while True:
        if input("准备好了吗? (输入 'n' 退出程序) > ") != 'n':
            try:
                total_questions = app.getTotal()
                print(f"检测到共 {total_questions} 题。")
                solved_question_count = 0
                total_elapsed_seconds = 0.0
                for i in range(total_questions):
                    question_start_time = time.time()
                    print(f"\n--- 正在解答第 {i+1} / {total_questions} 题 ---")
                    try:
                        title_type = app.tellTitle()
                        app.solveTitle(title_type)
                    except Exception as e:
                        print(f'程序发生错误，请手动完成一题后按回车继续: {e}')
                        import traceback
                        traceback.print_exc()
                        input()
                        continue
                    # 打印单题总耗时
                    question_elapsed = time.time() - question_start_time
                    print(f"--- 第 {i+1} 题总耗时: {question_elapsed:.4f} 秒 ---")
                    solved_question_count += 1
                    total_elapsed_seconds += question_elapsed
                
                if solved_question_count > 0:
                    average_time_per_question = total_elapsed_seconds / solved_question_count
                    print(f"本轮共完成 {solved_question_count} 题，平均每题耗时: {average_time_per_question:.4f} 秒")

                app.runTime += 1
                app.lastType = ''
                print(f"\n程序已完整执行 {app.runTime} 轮。")
            except Exception as e:
                print(f"在开始或获取总题数时发生错误: {e}")
                input("按回车键重试...")
        else:
            break