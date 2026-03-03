import sys
sys.path.append("c:/Users/Qty/Desktop/FuckWeici")
from SearchResult import SearchResult

searcher = SearchResult()
word = "tin"
resultList = searcher.getEnglishtoChinese(word)
print("getEnglishtoChinese:", resultList)

answer_means = searcher.getMeanFromWord(word)
print("getMeanFromWord:", answer_means)
