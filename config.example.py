# --- START OF FILE config.example.py ---

# LLM API Configuration
# ---------------------
# 复制并重命名为 config.py 后填写真实参数。

# 是否启用 LLM 辅助答题
LLM_ENABLED = True

# API Key（例如 sk-... / gsk_...）
LLM_API_KEY = "YOUR_API_KEY_HERE"

# API 基础地址（OpenAI 兼容）
# 例如:
# - https://api.openai.com/v1
# - https://api.deepseek.com/v1
# - https://api.groq.com/openai/v1
LLM_BASE_URL = "https://api.openai.com/v1"

# 模型名称
LLM_MODEL = "gpt-4o-mini"

# --- END OF FILE config.example.py ---
