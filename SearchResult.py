# --- START OF FILE SearchResult.py (Optimized) ---

import json, os
import itertools
import time # 导入 time 模块

class SearchResult():
    def __init__(self):
        # 记录整个初始化的开始时间
        init_start_time = time.time()
        print("--- SearchResult 初始化 ---")

        # 计时加载 fb_word_detail.json
        load_start_time = time.time()
        with open('Data/fb_word_detail.json', 'r', encoding='utf-8') as self.f:
            self.DATA = json.loads(self.f.read())
        print(f"  - [IO] 'fb_word_detail.json' 加载完毕 ({time.time() - load_start_time:.4f}s)")

        # 计时生成或加载 WordCorresponding.json
        word_corr_start_time = time.time()
        if not os.path.exists('Data/WordCorresponding.json'):
            print("  - [!] 'WordCorresponding.json' 不存在, 开始生成...")
            with open("Data/WordCorresponding.json",'w',encoding='utf-8') as self.f:
                self.WordCorresponding = self.generateWordCorresponding()
                self.f.write(json.dumps(self.WordCorresponding,ensure_ascii=False,indent=4))
            print(f"  - [CPU] 'WordCorresponding.json' 生成完毕 ({time.time() - word_corr_start_time:.4f}s)")
        else:
            with open("Data/WordCorresponding.json", 'r', encoding='utf-8') as self.f:
                self.WordCorresponding = json.loads(self.f.read())
            print(f"  - [IO] 'WordCorresponding.json' 加载完毕 ({time.time() - word_corr_start_time:.4f}s)")

        # 计时加载 newAnswer.json
        load_start_time = time.time()
        with open('Data/newAnswer.json', 'r', encoding='utf-8') as self.f:
            self.newDATA = json.loads(self.f.read())
        print(f"  - [IO] 'newAnswer.json' 加载完毕 ({time.time() - load_start_time:.4f}s)")
        
        print(f"--- 初始化完成 (总耗时: {time.time() - init_start_time:.4f}s) ---")


    def generateWordCorresponding(self):
        """创建单词 音标 词性 意思列表"""
        self.words = []
        self.word_notes = []
        self.word_parts = []
        self.word_means = [] # 意思过多 用列表作为元素
        for word in self.DATA:
            wordDetail = word
            wordWord = wordDetail['word'] # 单词
            wordNote_USA = wordDetail['usa_phonetic_symbols'] # 美音标
            wordPart = wordDetail['part_of_speech'] # 词性
            if wordPart in ['vt','vi']:
                wordPart = 'v'

            wordMean = []
            for mean in wordDetail['gy_paraphrase']:
                wordMean.append(mean['chinese'])

            self.words.append(wordWord)
            self.word_notes.append(wordNote_USA)
            self.word_parts.append(wordPart)
            self.word_means.append(wordMean) # 注意这是列表

            # 判断是否有派生词
            if wordDetail['gy_derivative'] != []:
                # 存在派生词
                for wordDerivative in wordDetail['gy_derivative']:
                    wordWord = wordDerivative['derivative_word']
                    wordNote_USA = wordDerivative['phonogram']
                    wordPart = wordDerivative['part_of_speech']
                    if wordPart in ['vt', 'vi']:
                        wordPart = 'v'

                    wordMean = [wordDerivative['description']]

                    self.words.append(wordWord)
                    self.word_notes.append(wordNote_USA)
                    self.word_parts.append(wordPart)
                    self.word_means.append(wordMean)  # 注意这是列表
        return {"words":self.words,"notes":self.word_notes,"parts":self.word_parts,"means":self.word_means}

    def noteSearchWord(self,note):
        """ 从音标搜找单词 """
        noteIndexList = self.indexListMore(self.WordCorresponding['notes'],note)
        if len(noteIndexList) == 1:
            return [self.WordCorresponding['words'][noteIndexList[0]]]
        else:
            result = []
            for i in noteIndexList:
                result.append(self.WordCorresponding['words'][i])
            return result

    def partSearchWord(self,wholeWord,part):
        """ 从整个单词和词性找单词 """
        for word in wholeWord:
            if word in self.WordCorresponding["words"]:
                if part == self.WordCorresponding["parts"][self.WordCorresponding["words"].index(word)]:
                    return word
            else:
                continue

    def getMeanFromWord(self,word):
        """ 找单词意思 """
        meanList = []
        wordList = self.indexListMore(self.WordCorresponding["words"],word)
        for i in wordList:
            mean = self.WordCorresponding['means'][i]
            for j in mean:
                if '：' in j:
                    j = j.replace('：','')

                if "；" in j:
                    j = j.split('；')
                    for h in j:
                        meanList.append(h)
                else:
                    meanList.append(j)
        return meanList

    def indexListMore(self,List,element):
        """ 返回 下标 """
        return [i for i, x in enumerate(List) if x == element]

    def getLongAnswer(self,question):
        try:
            resultList = []
            indexs = self.find_indexes(self.newDATA["语境题"][0], question)
            for i in indexs:
                resultList.append(self.newDATA["语境题"][1][i])
            return resultList
        except Exception as e:
            return []

    def get_all_permutations(self,lst):
        permutations = list(itertools.permutations(lst))
        return permutations

    def getListenAnswer(self,choices):
        allChoices = self.get_all_permutations(choices)
        for i in allChoices:
            try:
                return self.newDATA["听音识词"][1][self.newDATA["听音识词"][0].index(list(i))]
            except Exception as e:
                continue
        else:
            return 0

    def find_indexes(self,lst, element):
        indexes = []
        for i in range(len(lst)):
            if lst[i] == element:
                indexes.append(i)
        return indexes

    def getPutAnswer(self,question,parts,position):
        func_start_time = time.time()
        found_answers = []

        indexs = self.find_indexes(self.newDATA["构词法"][0], question)
        for i in indexs:
            try:
                # newAnswer.json 中构词法[1]是需要点击的词缀部分，如 ['ise']
                db_parts_needed = self.newDATA["构词法"][1][i]
                
                # newAnswer.json 中构词法[2]是组成完整单词的所有部分，如 ['organ', 'ise']
                full_word_parts = self.newDATA["构词法"][2][i]

                # 检查屏幕上的选项是否包含我们需要的词缀
                all_needed_parts_on_screen = all(p in parts for p in db_parts_needed)

                if all_needed_parts_on_screen:
                    # **核心修改**：创建一个包含清晰信息的字典
                    candidate = {
                        "word": "".join(full_word_parts),    # 拼接成完整单词字符串，如 "organise"
                        "parts_to_click": db_parts_needed    # 需要点击的词缀，如 ['ise']
                    }
                    found_answers.append(candidate)
                    # 为了日志清晰，打印拼接后的单词
                    print(f"    - [getPutAnswer] 找到候选答案: {candidate['word']}")

            except Exception as e:
                print(f"    - [getPutAnswer] 发生错误: {e}")
                continue
        
        if found_answers:
            print(f"    - [getPutAnswer] 查找完毕，共找到 {len(found_answers)} 个候选 (总耗时: {time.time() - func_start_time:.4f}s)")
            return found_answers
        else:
            print(f"    - [getPutAnswer] 未找到答案 (总耗时: {time.time() - func_start_time:.4f}s)")
            return []

    def getChinesetoEnglish(self,question):
        try:
            resultList = []
            indexs = self.find_indexes(self.newDATA["汉译英"][0], question)
            for i in indexs:
                resultList.append(self.newDATA["汉译英"][1][i])
            return resultList
        except Exception as e:
            return []
            
    def getEnglishtoChinese(self,question):
        try:
            resultList = []
            indexs = self.find_indexes(self.newDATA["英译汉"][0],question)
            for i in indexs:
                resultList.append(self.newDATA["英译汉"][1][i])
            return resultList
        except Exception as e:
            return []