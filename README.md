# FuckWeici

基于 `uiautomator2` 的维词安卓自动答题脚本，使用本地题库数据库辅助完成常见题型识别与作答。

目前项目主要面向 Windows 环境，附带了开箱即用的 `安装依赖.bat` 和 `启动.bat`。

## 参考资源

- 模拟器：[MuMu 模拟器](https://mumu.163.com/)
- 安装包：[维词 APK](https://imtt.dd.qq.com/sjy.00022/sjy.00004/16891/apk/EC254B9AAA616B4D96F4C304CFA5F3EF.apk)
- 参考实现：[Bilibili - BV18z4y1x7N6](https://www.bilibili.com/video/BV18z4y1x7N6)

## 快速开始

### 1. 安装依赖

直接双击运行：

```bat
安装依赖.bat
```

这个脚本会尝试：

- 安装 `uv`
- 安装 Android Platform Tools（`adb`）
- 执行 `uv sync`

### 2. 连接手机

- 手机开启“开发者选项”和“USB 调试”
- 使用数据线连接电脑
- 确认 `adb devices` 能看到设备
- 如果不方便接真机，也可以使用 [MuMu 模拟器](https://mumu.163.com/)
- 维词安装包可使用这里提供的版本：[维词 APK](https://imtt.dd.qq.com/sjy.00022/sjy.00004/16891/apk/EC254B9AAA616B4D96F4C304CFA5F3EF.apk)

如果你已经自行配置过环境，也可以手动检查：

```powershell
adb devices
```

### 3. 启动脚本

直接双击运行：

```bat
启动.bat
```

或手动执行：

```powershell
uv run python VictorApp.py
```

### 4. 按提示开始答题

程序启动后会：

- 连接设备
- 加载本地题库
- 询问每题间隔秒数，默认 `2s`
- 等待你进入答题界面
- 在你确认后开始自动答题

## 功能简介

- 连接 Android 设备并启动自动答题流程
- 支持从本地 SQLite 题库检索答案
- 支持以下题型
  - 拼写
  - 英译汉
  - 听音识词
  - 构词法拼词
  - 大杂烩 / 语境类题目
- 对部分未直接命中题库的题目进行相似度兜底匹配
- 支持普通闯关模式和“万词王”模式

## 项目结构

```text
FuckWeici/
├─ VictorApp.py             # 主程序，负责设备连接、题型识别与自动作答
├─ SearchResult.py          # 题库加载、索引构建与答案检索逻辑
├─ test_search_result.py    # SearchResult 基础测试
├─ 安装依赖.bat             # 自动安装 uv / adb 并执行 uv sync
├─ 启动.bat                 # 使用 uv 启动主程序
├─ pyproject.toml           # 项目依赖声明
├─ uv.lock                  # 锁定依赖版本
└─ db/                      # 本地题库数据库
```

## 运行要求

- Windows
- Python `3.10+`
- 一台已开启 USB 调试的 Android 设备
- 可用的 `adb`
- 可选：Android 模拟器，例如 [MuMu 模拟器](https://mumu.163.com/)
- 维词 App 包名与代码中一致：`com.android.weici.senior.student`

## 数据库说明

项目默认使用下面的题库文件：

```text
db/weici_ext459.db
```

如果你需要从设备或模拟器中提取维词原始数据库，可以关注应用数据库目录：

```text
/data/data/com.android.weici.senior.student/databases/
```

如果需要切换题库路径，可以设置环境变量 `FW_DB_PATH`：

```powershell
$env:FW_DB_PATH="db\\weici_ext459.db"
uv run python VictorApp.py
```

## 测试

运行基础测试：

```powershell
uv run python test_search_result.py
```

这些测试主要覆盖：

- 听音识词答案匹配
- 英译汉索引是否成功构建
- 音标查词是否能返回结果

## 工作原理

`SearchResult.py` 会从本地 SQLite 数据库中提取：

- 单词与音标、释义映射
- 各题型的题干与答案
- 听音识词选项集合
- 构词法拆分结果

`VictorApp.py` 负责：

- 通过 `uiautomator2` 连接设备
- 识别当前题型
- 从界面提取题干、选项、音标、中文释义等信息
- 调用 `SearchResult` 检索答案
- 在未命中题库时使用相似度策略做兜底判断

项目思路可参考视频实现：[BV18z4y1x7N6](https://www.bilibili.com/video/BV18z4y1x7N6)

## 常见问题

### 1. 启动时报“uv not found”

先运行：

```bat
安装依赖.bat
```

### 2. 提示找不到 Android 设备

可以依次检查：

- 手机是否开启 USB 调试
- 数据线是否支持数据传输
- `adb devices` 是否能识别设备
- 是否已在手机上同意调试授权

程序本身也会在首次连接失败时尝试自动重启 `adb` 服务。

### 3. 题库加载失败

请确认：

- `db/weici_ext459.db` 存在
- 路径没有被环境变量 `FW_DB_PATH` 配错
- 数据库文件未损坏

### 4. 无法识别题型

可能原因：

- 当前页面不在正式答题界面
- App 版本或界面控件 ID 与脚本不一致
- 页面加载较慢，超出了脚本重试窗口

## 注意事项

- 本项目依赖维词 App 当前界面结构，若 App 更新导致控件 ID 变化，脚本可能失效。
- 项目中的题库与包名都偏向特定版本环境，不保证对所有版本通用。
- 自动化脚本存在误判和误点风险，尤其是在题库未命中时会启用兜底策略。

## 许可证

仓库当前未声明开源许可证。如需公开分发或二次使用，建议先补充明确的 License。
