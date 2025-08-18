# --- START OF FILE SearchResult.py (Optimized) ---

import json, os
import itertools
import time # 导入 time 模块

class SearchResult():
    def __init__(self):
        # 记录整个初始化的开始时间
        init_start_time = time.time()
        print("[性能分析] SearchResult 初始化开始...")

        # 计时加载 fb_word_detail.json
        load_start_time = time.time()
        with open('Data/fb_word_detail.json', 'r', encoding='utf-8') as self.f:
            self.DATA = json.loads(self.f.read())
        print(f"    - [文件IO] 加载 'fb_word_detail.json' 耗时: {time.time() - load_start_time:.4f} 秒")

        # 计时生成或加载 WordCorresponding.json
        word_corr_start_time = time.time()
        if not os.path.exists('Data/WordCorresponding.json'):
            print("    - [数据处理] 'WordCorresponding.json' 不存在，开始生成...")
            with open("Data/WordCorresponding.json",'w',encoding='utf-8') as self.f:
                self.WordCorresponding = self.generateWordCorresponding()
                self.f.write(json.dumps(self.WordCorresponding,ensure_ascii=False,indent=4))
            print(f"    - [数据处理] 生成并写入 'WordCorresponding.json' 耗时: {time.time() - word_corr_start_time:.4f} 秒")
        else:
            with open("Data/WordCorresponding.json", 'r', encoding='utf-8') as self.f:
                self.WordCorresponding = json.loads(self.f.read())
            print(f"    - [文件IO] 加载 'WordCorresponding.json' 耗时: {time.time() - word_corr_start_time:.4f} 秒")

        # 计时加载 newAnswer.json
        load_start_time = time.time()
        with open('Data/newAnswer.json', 'r', encoding='utf-8') as self.f:
            self.newDATA = json.loads(self.f.read())
        print(f"    - [文件IO] 加载 'newAnswer.json' 耗时: {time.time() - load_start_time:.4f} 秒")
        
        print(f"[性能分析] SearchResult 初始化完成, 总耗时: {time.time() - init_start_time:.4f} 秒")


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
        # 重点监控此函数性能
        func_start_time = time.time()

        indexs = self.find_indexes(self.newDATA["构词法"][0],question)
        for i in indexs:
            try:
                length = len(self.newDATA["构词法"][1][i])
                searchList = []
                if position == 1:
                    for j in parts[:length]:
                        searchList.append(j)
                else:
                    for j in parts[-length:]:
                        searchList.append(j)
                
                # 排列组合是性能消耗大户，单独计时
                perm_start_time = time.time()
                varyList = self.get_all_permutations(searchList)
                print(f"        - [CPU密集] getPutAnswer-排列组合计算耗时: {time.time() - perm_start_time:.4f} 秒 (生成了 {len(varyList)} 种可能)")
                
                for k in varyList:
                    if list(k) == self.newDATA["构词法"][1][i]:
                        print(f"    - [数据处理] 'getPutAnswer' 查找成功, 总耗时: {time.time() - func_start_time:.4f} 秒")
                        return self.newDATA["构词法"][2][i]
            except Exception as e:
                print(e)
                continue
        else:
            print(f"    - [数据处理] 'getPutAnswer' 未找到答案, 总耗时: {time.time() - func_start_time:.4f} 秒")
            return 0

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