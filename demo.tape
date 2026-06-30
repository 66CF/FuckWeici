Output demo.gif

Set FontSize 16
Set Width 800
Set Padding 16
Set Theme "Catppuccin Mocha"

Type "uv run python main.py"
Enter
Sleep 800ms

# ── 启动日志 ──
Type 'gum log --level info --prefix "启动" "FuckWeici 已启动"'
Enter
Sleep 400ms
Type 'gum log --level info --prefix "环境" "设备=emulator-5554"'
Enter
Sleep 400ms
Type 'gum log --level info --prefix "环境" "题库=db/weici_ext459.db"'
Enter
Sleep 400ms
Type 'gum log --level info --prefix "环境" "答题间隔=0.50s 包名=com.android.weici.senior.student"'
Enter
Sleep 400ms
Type 'gum log --level info --prefix "提示" "进入维词答题界面后确认开始"'
Enter
Sleep 600ms

# ── 等待确认 ──
Type 'gum log --level warn --prefix "等待" "请把设备停留在答题界面。准备好后按回车。"'
Enter
Sleep 500ms
Type 'gum log --level info --prefix "状态" "正在读取当前题目状态..."'
Enter
Sleep 600ms

# ── 答题过程 ──
Type 'gum log --level info --prefix "题目" "1/100 大杂烩"'
Enter
Sleep 300ms
Type 'gum log --level info --prefix "命中" "faithfully · 题库直出"'
Enter
Sleep 400ms

Type 'gum log --level info --prefix "题目" "2/100 大杂烩"'
Enter
Sleep 300ms
Type 'gum log --level info --prefix "命中" "mechanic · 题库直出"'
Enter
Sleep 400ms

Type 'gum log --level info --prefix "题目" "3/100 英译汉"'
Enter
Sleep 300ms
Type 'gum log --level info --prefix "命中" "注意；专心 · attention"'
Enter
Sleep 400ms

Type 'gum log --level info --prefix "题目" "4/100 英译汉"'
Enter
Sleep 300ms
Type 'gum log --level info --prefix "命中" "侮辱；冒犯 · insult"'
Enter
Sleep 400ms

Type 'gum log --level info --prefix "题目" "5/100 大杂烩"'
Enter
Sleep 300ms
Type 'gum log --level info --prefix "命中" "accomplish · 题库直出"'
Enter
Sleep 800ms
