import re

def filter_chinese_and_english(input_str):
    return ''.join(re.findall(r'[a-zA-Z\u4e00-\u9fa5]+', input_str))

s = "tin\n英[tɪn] 美[tɪn]"
print("Filtered:", filter_chinese_and_english(s))
