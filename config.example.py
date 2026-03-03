# --- START OF FILE config.example.py ---

# LLM API Configuration
# ---------------------
# 复制并重命名为 config.py 后填写真实参数。

# 是否启用 LLM 辅助答题
LLM_ENABLED = True

# 是否启用“全LLM辅助模式”
# True: 优先使用 LLM 作答，再回退题库
# False: 优先使用题库，LLM 仅作兜底
LLM_FULL_MODE = False

# API Key（例如 sk-... / gsk_...）
# Ollama 本地服务可留空
LLM_API_KEY = ""

# API 基础地址（OpenAI 兼容）
# 例如:
# - https://api.openai.com/v1
# - https://api.deepseek.com/v1
# - https://api.groq.com/openai/v1
# - Ollama: http://localhost:11434
LLM_BASE_URL = "http://localhost:11434"

# 模型名称
LLM_MODEL = "qwen3.5:4b"

# 是否开启模型深度思考（Qwen/Ollama 可用）
LLM_ENABLE_THINKING = False

# --- END OF FILE config.example.py ---
