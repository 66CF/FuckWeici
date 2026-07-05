# FuckWeici

![Python](https://img.shields.io/badge/Python_3.10+-uv-3776AB?logo=python&logoColor=white) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Android-brightgreen) ![GitHub stars](https://img.shields.io/github/stars/66CF/FuckWeici?style=social) ![uiautomator2](https://img.shields.io/badge/uiautomator2-3DDC84?style=flat) ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat)

维词（Weici）App 自动答题脚本，基于 uiautomator2 实现 Android 端自动化，通过本地题库数据库匹配答案并自动点击。

## 工作流程

```mermaid
flowchart LR
    A[启动] --> B[选择间隔]
    B --> C[连接设备]
    C --> D[加载题库]
    D --> E[进入答题页]
    E --> F[读取页面状态]
    F --> G{识别题型}
    G --> H[题库匹配<br/>拼写 / 英译汉 / 大杂烩 / 听音识词 / 构词法]
    H --> I{命中?}
    I -->|是| J[自动点击 / 输入]
    I -->|否| K{模式}
    K -->|普通| L[随机兜底]
    K -->|万词王| M[人工接管]
    J --> N{本轮结束?}
    L --> N
    M --> N
    N -->|否| F
    N -->|是| O[输出统计]
    O --> P{继续?}
    P -->|是| E
    P -->|否| Q[退出]
```

## 支持的题型

| 类型 | 说明 |
|------|------|
| 拼写题 | 根据音标拼写单词，自动点击虚拟键盘 |
| 英译汉 | 看英文选中文释义（三选一） |
| 大杂烩 | 语境选词、汉译英、补全句子等混合题型 |
| 听音识词 | 听音频选单词（三选一） |
| 构词法拼词 | 选择正确词缀拼出复合词 |

支持「万词王」无尽模式（100 题/关）自动检测。

## 安装与运行

<p>
  <a href="https://github.com/66CF/FuckWeici/archive/refs/heads/main.zip">
    <img src="https://img.shields.io/badge/下载项目-ZIP-2ea44f?style=for-the-badge" alt="下载项目 ZIP">
  </a>
</p>

1. 点击 `Code → Download ZIP` 下载项目并解压。
2. 双击 `安装依赖.bat` 安装 `uv`、`adb`、`gum` 和项目依赖。
3. 打开[MuMu 模拟器](https://mumu.163.com/)或安卓手机，进入[维词](https://imtt.dd.qq.com/sjy.00022/sjy.00004/16891/apk/EC254B9AAA616B4D96F4C304CFA5F3EF.apk)的答题页面。真机需要先开启 USB 调试并授权电脑连接。
4. 双击 `启动.bat`，按提示选择答题间隔。第一次建议选 `2 秒`。

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
