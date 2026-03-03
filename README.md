# FuckWeici
基于 [uiautomator2](https://github.com/openatx/uiautomator2) 的维词安卓自动答题脚本。

## 环境要求
- Windows 10/11
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- 已安装并可用的 `adb`（Android Platform Tools）
- Android 设备已开启 USB 调试

## 快速开始（uv）

### 方式 A：双击运行（推荐，Windows）
1. 先安装 uv。
2. 双击运行 `安装依赖.bat`。
3. 手机开启 USB 调试并连接电脑，确认 `adb devices` 能看到设备。
4. 首次使用执行一次初始化：`uv run python -m uiautomator2 init`
5. 打开手机维词 App 并停在答题页面。
6. 双击运行 `启动.bat`。

### 方式 B：命令行（通用）
```bash
uv python install 3.12
uv sync
uv run python -m uiautomator2 init
uv run python VictorApp.py
```

## uv 安装示例（Windows）
```powershell
winget install --id=astral-sh.uv -e
```

## 功能说明
- 自动识别并处理多种题型：拼写、英译汉、构词法、大杂烩、听音识词。
- 优先使用本地题库答题，未命中时可切换到 LLM 辅助。
- 支持自定义每题间隔时间。

## LLM 配置（可选）
编辑 `config.py`：
- `LLM_ENABLED = True/False`：是否启用 LLM 辅助。
- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`：模型服务配置。

不使用 LLM 时，将 `LLM_ENABLED` 设为 `False` 即可。

### Release 版 EXE 如何启用 LLM
- 首次运行 `FuckWeici.exe` 时，如果目录里没有 `config.py`，程序会自动生成。
- 打开生成的 `config.py`，填写 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 后重启 exe。
- 也可直接用环境变量覆盖：`LLM_ENABLED`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。

## 常见问题
- `uv` 未找到：先安装 uv，或执行 `winget install --id=astral-sh.uv -e`。
- 设备连不上：先执行 `adb devices` 检查连接，再尝试 `adb kill-server` 后重连。
- 启动报 uiautomator2 相关错误：执行 `uv run python -m uiautomator2 init` 后重试。
- 识别失败：确保维词在前台，且停在答题界面。

## 项目结构
- `VictorApp.py`：主流程与题型处理。
- `SearchResult.py`：本地题库检索。
- `LLMHelper.py`：LLM 调用封装。
- `config.py`：LLM 配置。
- `Data/`：题库数据。

## 依赖管理说明
- 项目使用 `uv + pyproject.toml` 管理依赖。
- 依赖定义在 `pyproject.toml` 的 `[project.dependencies]`。

## 参考
- [B站视频-BV18z4y1x7N6](https://www.bilibili.com/video/BV18z4y1x7N6)
- [uiautomator2 项目](https://github.com/openatx/uiautomator2)
