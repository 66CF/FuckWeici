# FuckWeici

![Python](https://img.shields.io/badge/Python_3.10+-uv-3776AB?logo=python&logoColor=white) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Android-brightgreen) ![GitHub stars](https://img.shields.io/github/stars/66CF/FuckWeici?style=social) ![uiautomator2](https://img.shields.io/badge/uiautomator2-3DDC84?style=flat) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat)

维词（Weici）App 自动答题脚本，基于 uiautomator2 实现 Android 端自动化，通过本地题库数据库匹配答案并自动点击。

<div align="center">

![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=3DDC84&center=true&vCenter=true&width=700&height=220&lines=INFO+%E5%90%AF%E5%8A%A8:+FuckWeici+%E5%B7%B2%E5%90%AF%E5%8A%A8;INFO+%E7%8E%AF%E5%A2%83:+%E8%AE%BE%E5%A4%87%3Demulator-5554;INFO+%E6%8F%90%E7%A4%BA:+%E8%BF%9B%E5%85%A5%E7%BB%B4%E8%AF%8D%E7%AD%94%E9%A2%98%E7%95%8C%E9%9D%A2%E5%90%8E%E7%A1%AE%E8%AE%A4%E5%BC%80%E5%A7%8B;INFO+%E9%A2%98%E7%9B%AE:+1%2F100+%E5%A4%A7%E6%9D%82%E7%83%A9;INFO+%E5%91%BD%E4%B8%AD:+faithfully+%C2%B7+%E9%A2%98%E5%BA%93%E7%9B%B4%E5%87%BA;INFO+%E9%A2%98%E7%9B%AE:+2%2F100+%E8%8B%B1%E8%AF%91%E6%B1%89;INFO+%E5%91%BD%E4%B8%AD:+%E6%B3%A8%E6%84%8F%EF%BC%9B%E4%B8%93%E5%BF%83+%C2%B7+attention)

</div>

## 支持的题型

| 类型 | 说明 |
|------|------|
| 拼写题 | 根据音标拼写单词，自动点击虚拟键盘 |
| 英译汉 | 看英文选中文释义（三选一） |
| 大杂烩 | 语境选词、汉译英、补全句子等混合题型 |
| 听音识词 | 听音频选单词（三选一） |
| 构词法拼词 | 选择正确词缀拼出复合词 |

支持「万词王」无尽模式（100 题/关）自动检测。

## 环境要求

- Windows 系统
- Python 3.12+
- [gum](https://github.com/charmbracelet/gum) 终端交互工具（安装脚本会自动检测并尝试安装）
- Android 设备（已开启 USB 调试并连接 ADB）或 [MuMu 模拟器](https://mumu.163.com/)
- 已安装维词 App（包名 `com.android.weici.senior.student`）
  - [维词 APK 下载](https://imtt.dd.qq.com/sjy.00022/sjy.00004/16891/apk/EC254B9AAA616B4D96F4C304CFA5F3EF.apk)

## 安装

双击 `安装依赖.bat`，脚本会自动检测并安装 `uv`、`adb`、`gum`，然后同步项目依赖。

或手动执行：

```bash
uv sync
```

## 运行

1. 用 USB 连接 Android 设备，确保 ADB 已授权
2. 在手机上打开维词 App，进入答题页面
3. 双击 `启动.bat`，或执行：

```bash
uv run python main.py
```

4. 在 gum 选择菜单中选择答题间隔时间（默认 2 秒），确认后脚本开始自动答题

## 配置

- **题库路径**：通过环境变量 `FW_DB_PATH` 指定，默认使用 `db/weici_ext459.db`
- **设备数据库路径**：`/data/data/com.android.weici.senior.student/databases/`（需 root 权限拉取）
- **答题间隔**：启动时通过 gum choose 选择，控制每题之间的等待时间

## 项目结构

```
├── main.py              # 主入口：配置、设备抽象、答题策略、CLI 编排
├── database.py          # 题库加载、数据模型、索引构建、答案查询
├── test_database.py     # 单元测试
├── pyproject.toml       # 项目元数据与依赖
├── 启动.bat             # Windows 启动脚本
├── 安装依赖.bat         # Windows 自动安装脚本
└── db/                  # SQLite 题库目录
```

## 依赖

- [uiautomator2](https://github.com/openatx/uiautomator2) — Android UI 自动化
- [gum](https://github.com/charmbracelet/gum) — 终端选择、确认、初始化 Spin 与 Log 输出
