# --- START OF FILE config.py ---

# LLM API Configuration
# ---------------------
# 将此文件中的 'YOUR_...' 替换为您的实际凭据。
# 如果您不想使用LLM辅助功能，请将 LLM_ENABLED 设置为 False。

# 是否启用LLM辅助答题
LLM_ENABLED = False

# 您的API密钥
# 例如: "gsk_..." (Groq), "sk-..." (OpenAI), "fk..." (OpenAI API Proxy)
LLM_API_KEY = "YOUR_API_KEY_HERE"

# API的基础URL
# - Groq: "https://api.groq.com/openai/v1"
# - OpenAI: "https://api.openai.com/v1"
# - DeepSeek: "https://api.deepseek.com/v1"
# - 自定义代理: "https://your.proxy.com/v1"
LLM_BASE_URL = "https://api.openai.com/v1"

# 您想使用的模型名称
# - Groq: "llama3-8b-8192", "gemma-7b-it"
# - OpenAI: "gpt-3.5-turbo", "gpt-4o"
# - DeepSeek: "deepseek-chat"
LLM_MODEL = "gpt-4o-mini"

# --- END OF FILE config.py ---
