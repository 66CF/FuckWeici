# FuckWeici
基于 [uiautomator2](https://github.com/openatx/uiautomator2) 的维词安卓自动脚本

## 项目结构
- `VictorApp_u2.py`：主自动化逻辑，负责题型识别、自动点击等。
- `SearchResult.py`：题库管理与智能查找逻辑，负责从 json 文件中检索答案。
- `Data/`：存放题库数据的 json 文件，包括 `fb_word_detail.json`、`WordCorresponding.json`、`newAnswer.json` 等。

## 如何使用
1. **环境准备**
   - 安装 Python 3.x
   - 安装 `uiautomator2` ：`pip install -U uiautomator2`
   - 手机连接电脑，开启 USB 调试，并保证能用 uiautomator2 识别到设备
   - 确认 APP「维词」已安装在手机上，并处于主界面
2. **运行脚本**
   ```bash
   python VictorApp_u2.py
   ```
   - 按指引输入每题间隔时间
   - 按提示操作，脚本会自动完成答题流程

## 注意事项
- 若遇 uiautomator2 连接异常或元素识别失败，可尝试 adb kill-server 重启

## 鸣谢 & 参考
- [B站视频-BV18z4y1x7N6](https://www.bilibili.com/video/BV18z4y1x7N6)
- [uiautomator2 项目](https://github.com/openatx/uiautomator2)

## 待实现
- [x] AI辅助
- [ ] 听力
- [ ] 更优雅的界面