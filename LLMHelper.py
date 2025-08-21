# --- START OF FILE LLMHelper.py ---

import requests
import json
import re
import config  # 导入用户的配置

# 从VictorApp.py复制日志函数以便在此处使用
RESET = "\033[0m"
COLORS = {
    'cyan': "\033[38;2;124;147;206m",
    'yellow': "\033[38;2;199;182;220m",
    'bold': "\033[1m",
}
def _c(text, color=None, bold=False):
    prefix = COLORS['bold'] if bold else ''
    if color and color in COLORS:
        prefix += COLORS[color]
    return f"{prefix}{text}{RESET}" if prefix else text
def log_info(msg): print(f"{_c('[i]', 'cyan', True)} {msg}")
def log_warn(msg): print(f"{_c('[!]', 'yellow', True)} {msg}")


class LLMHelper:
    def __init__(self):
        self.enabled = False
        if config.LLM_ENABLED and config.LLM_API_KEY not in ["", "YOUR_API_KEY_HERE"]:
            self.api_key = config.LLM_API_KEY
            self.base_url = config.LLM_BASE_URL
            self.model = config.LLM_MODEL
            self.enabled = True
        
    def is_enabled(self):
        return self.enabled

    def _call_api(self, prompt, system_prompt="You are a helpful assistant."):
        if not self.is_enabled():
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        try:
            log_info("LLM: 正在请求模型获取答案...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=15  # 15秒超时
            )
            response.raise_for_status()  # 如果HTTP状态码是4xx或5xx，则抛出异常
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            log_warn(f"LLM: API 请求失败: {e}")
            return None
        except (KeyError, IndexError) as e:
            log_warn(f"LLM: 无法解析API响应: {e}")
            return None

    def answer_choice_question(self, question, choices):
        """
        处理单选题。
        choices: {'A': 'A. text', 'B': 'B. text', 'C': 'C. text'}
        """
        prompt = (
            f"请根据下面的问题和选项，选择最合适的答案。\n"
            f"问题: {question}\n"
            f"选项:\n"
            f"{choices['A']}\n"
            f"{choices['B']}\n"
            f"{choices['C']}\n\n"
            f"请直接回答'A'、'B'或'C'中的一个字母，不要包含任何其他解释。"
        )
        system_prompt = "You are an expert in English vocabulary and grammar. Your task is to answer multiple-choice questions by providing only the letter of the correct option (A, B, or C)."
        
        response = self._call_api(prompt, system_prompt)
        if response:
            match = re.search(r'^[A-C]', response, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        return None

    def answer_spelling(self, meaning, phonetic):
        """处理拼写题"""
        prompt = (
            f"请根据单词的中文释义和音标，写出对应的英文单词。\n"
            f"中文释义: {meaning}\n"
            f"音标: {phonetic}\n\n"
            f"请只回答这个单词，不要包含任何其他解释。"
        )
        system_prompt = "You are an English dictionary expert. Your task is to provide the correct English word based on its meaning and phonetic transcription. Respond with only the word itself."

        response = self._call_api(prompt, system_prompt)
        if response and re.match(r'^[a-zA-Z]+$', response):
            return response.lower()
        return None

    def answer_build_word(self, part_word, pieces):
        """处理构词法题"""
        prompt = (
            f"一个完整的单词被分成了已知部分和一些碎片。请从碎片中选择一个或多个，与已知部分组合成一个正确的、有意义的英文单词。\n"
            f"已知部分: '{part_word}' (它可能在单词的开头、中间或结尾)\n"
            f"可用碎片: {', '.join(pieces)}\n\n"
            f"请回答你需要点击的碎片，并用逗号分隔。例如，如果需要点击 'pre' 和 'fix'，就回答 'pre,fix'。如果只需要一个碎片，就只回答那个碎片。"
        )
        system_prompt = "You are an expert in English morphology. Your task is to construct a word from given parts. Respond with the necessary pieces, separated by commas."
        
        response = self._call_api(prompt, system_prompt)
        if response:
            # 清理响应并返回一个碎片列表
            clicked_pieces = [p.strip() for p in response.split(',')]
            # 验证LLM返回的碎片是否都在可用列表中
            if all(p in pieces for p in clicked_pieces):
                return clicked_pieces
        return None

# --- END OF FILE LLMHelper.py ---