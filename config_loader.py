import importlib.util
import os
import shutil
import sys
from pathlib import Path


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _is_placeholder(value):
    if not value:
        return True
    text = str(value).strip()
    return text in {"YOUR_API_KEY_HERE", "YOUR_..."} or text.startswith("YOUR_")


def _module_attr(module, name, default=None):
    return getattr(module, name, default) if module else default


def _load_py_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def ensure_user_config(runtime_dir):
    config_path = runtime_dir / "config.py"
    if config_path.exists():
        return config_path, False

    # onefile 下模板可能在 _MEIPASS，onefolder 下通常在 runtime_dir
    candidates = [runtime_dir / "config.example.py"]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "config.example.py")

    for template_path in candidates:
        if template_path.exists():
            shutil.copyfile(template_path, config_path)
            return config_path, True

    return config_path, False


def load_llm_settings():
    runtime_dir = get_runtime_dir()
    config_path, created = ensure_user_config(runtime_dir)

    config_module = None
    if config_path.exists():
        try:
            config_module = _load_py_module(str(config_path), "user_config")
        except Exception:
            config_module = None

    enabled = _module_attr(config_module, "LLM_ENABLED", False)
    api_key = _module_attr(config_module, "LLM_API_KEY", "")
    base_url = _module_attr(config_module, "LLM_BASE_URL", "")
    model = _module_attr(config_module, "LLM_MODEL", "")

    # 环境变量优先，便于 exe 用户免改文件
    env_enabled = os.getenv("LLM_ENABLED")
    env_api_key = os.getenv("LLM_API_KEY")
    env_base_url = os.getenv("LLM_BASE_URL")
    env_model = os.getenv("LLM_MODEL")

    if env_enabled is not None:
        enabled = _as_bool(env_enabled)
    if env_api_key:
        api_key = env_api_key
    if env_base_url:
        base_url = env_base_url
    if env_model:
        model = env_model

    enabled = bool(_as_bool(enabled))
    api_key = str(api_key or "").strip()
    base_url = str(base_url or "").strip().rstrip("/")
    model = str(model or "").strip()

    has_valid_key = not _is_placeholder(api_key)
    fully_configured = enabled and has_valid_key and bool(base_url) and bool(model)

    return {
        "enabled": enabled,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "config_path": str(config_path),
        "created_config": created,
        "fully_configured": fully_configured,
    }
