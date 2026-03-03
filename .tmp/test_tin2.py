import sys
sys.path.append("c:/Users/Qty/Desktop/FuckWeici")
from VictorApp import U2VictorApp

class MockD:
    pass

class MockApp(U2VictorApp):
    def __init__(self):
        self.d = MockD()
        self.pkg_name = "mock"
        self.relaxTime = 0
        from SearchResult import SearchResult
        self.searcher = SearchResult()
        self.llm_helper = None
        self.is_king_mode = False

app = MockApp()

word = "tin"
print("word:", word)
answer_means = app.searcher.getMeanFromWord(word)
print("answer_means:", answer_means)

choices_text = ["鉴定；辨认", "牺牲；祭品", "（化学）锡"]

rates = [0, 0, 0]
for i, choice in enumerate(choices_text):
    cleaned_choice = app.reSaveChinese(choice.replace('；', ''))
    print(f"cleaned_choice {i}:", cleaned_choice)
    for answer_word in answer_means:
        cleaned_answer = app.reSaveChinese(answer_word)
        rate = app.compareWordsMean(cleaned_answer, cleaned_choice)
        print(f"  comparing '{cleaned_answer}' and '{cleaned_choice}', rate: {rate}")
        if rate > rates[i]:
            rates[i] = rate

print("max rate:", max(rates))

