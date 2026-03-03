# --- START OF FILE config.py ---

# LLM API Configuration
# ---------------------
# 将此文件中的 'YOUR_...' 替换为您的实际凭据。
# 如果您不想使用LLM辅助功能，请将 LLM_ENABLED 设置为 False。

# 是否启用LLM辅助答题
LLM_ENABLED = True

# 是否启用“全LLM辅助模式”
# True: 优先使用 LLM 作答，再回退题库
# False: 优先使用题库，LLM 仅作兜底
LLM_FULL_MODE = False

# 您的API密钥
# 例如: "gsk_..." (Groq), "sk-..." (OpenAI), "fk..." (OpenAI API Proxy)
# Ollama 本地服务可留空
LLM_API_KEY = ""

# API的基础URL
# - Groq: "https://api.groq.com/openai/v1"
# - OpenAI: "https://api.openai.com/v1"
# - DeepSeek: "https://api.deepseek.com/v1"
# - 自定义代理: "https://your.proxy.com/v1"
LLM_BASE_URL = "http://localhost:11434"

# 您想使用的模型名称
# - Groq: "llama3-8b-8192", "gemma-7b-it"
# - OpenAI: "gpt-3.5-turbo", "gpt-4o"
# - DeepSeek: "deepseek-chat"
LLM_MODEL = "qwen3.5:4b"

# 是否开启模型深度思考（Qwen/Ollama 可用）
LLM_ENABLE_THINKING = False

# --- END OF FILE config.py ---
