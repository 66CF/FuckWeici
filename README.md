# FuckWeici
基于 [uiautomator2](https://github.com/openatx/uiautomator2) 的维词安卓自动脚本

## 主要功能
- **全自动答题**: 自动识别题型（拼写、英译汉、构词法、大杂烩）并从本地题库查找答案。
- **LLM 辅助**: 当本地题库未命中时，自动调用大型语言模型（如 Llama, GPT）进行智能答题，大幅提高正确率。
- **高度可配置**: 可自定义答题间隔，并通过配置文件轻松接入不同的 LLM API 服务。

## 项目结构
- `VictorApp.py`：主自动化逻辑，负责题型识别、UI 交互和调用 LLM。
- `SearchResult.py`：本地题库管理与查找逻辑。
- `LLMHelper.py`：(新增) 封装了调用 LLM API 的逻辑，负责与 AI 模型通信。
- `config.py`：(新增) 配置文件，用于设置 LLM API 密钥、模型地址等。
- `Data/`：存放本地题库数据的 json 文件。

## 如何使用

### 1. 环境准备
   - 安装 Python 3.x
   - 安装依赖库：
     ```bash
     pip install -U uiautomator2 requests
     ```
   - 手机连接电脑，开启 USB 调试，并保证能用 uiautomator2 识别到设备。
   - 确认 APP「维词」已安装在手机上，并处于主界面。

### 2. 配置 LLM 辅助 (可选但强烈推荐)
为了使用 AI 辅助答题功能，你需要在项目根目录下创建或修改 `config.py` 文件。如果不想使用此功能，可将 `LLM_ENABLED` 设置为 `False`。

### 3. 运行脚本
   ```bash
   python VictorApp.py
   ```
   - 按指引输入每题间隔时间。
   - 按提示操作，脚本会自动完成答题流程。

## 注意事项
- 若遇 uiautomator2 连接异常或元素识别失败，可尝试 `adb kill-server` 重启。
- 请确保 `config.py` 中的 API Key 和 URL 正确无误，否则 LLM 功能无法正常工作。

## 鸣谢 & 参考
- [B站视频-BV18z4y1x7N6](https://www.bilibili.com/video/BV18z4y1x7N6)
- [uiautomator2 项目](https://github.com/openatx/uiautomator2)

## 待实现
- [x] AI辅助
- [x] 听力(可能是部分支持)
- [x] 更优雅的界面（我觉得好看了哈哈哈）