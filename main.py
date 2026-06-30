import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from random import randint

import uiautomator2 as u2
from database import Database

# ── 常量 ──

GUM = shutil.which("gum")
GUM_COLORS = {"accent": "#7DD3FC", "muted": "#94A3B8"}
STATUS = {"ok": ("命中", "info"), "warn": ("兜底", "warn"), "error": ("失败", "error"), "info": ("提示", "info")}
RELAX_TIME_CHOICES = ("0.5 秒", "1 秒", "2 秒", "3 秒", "5 秒", "自定义")

QUESTION_TITLES = {1: "拼写", 2: "英译汉", 345: "大杂烩", 6: "听音识词", 7: "构词法拼词"}
PKG = "com.android.weici.senior.student"

RES_ID = {
    "keyboard": f"{PKG}:id/keyboard",
    "part_word": f"{PKG}:id/part_word",
    "english": f"{PKG}:id/english",
    "question": f"{PKG}:id/question",
    "sound": f"{PKG}:id/sound",
    "position": f"{PKG}:id/position",
    "yinbiao": f"{PKG}:id/yinbiao",
    "chinese": f"{PKG}:id/chinese",
    "key_confirm": f"{PKG}:id/key_to_confirm",
}

# ── Gum 辅助函数 ──

def _run_gum(args, input_text=None, capture_output=False):
    if not GUM:
        return None
    try:
        return subprocess.run(
            [GUM, *args],
            input=input_text,
            stdout=subprocess.PIPE if capture_output else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (OSError, ValueError):
        return None


def _gum_interactive():
    return bool(GUM and sys.stdin.isatty())


def _gum_log(level, message, *, prefix=None):
    message = re.sub(r"\s+", " ", str(message or "")).strip()
    args = ["log", "--level", level]
    if prefix:
        args.extend(["--prefix", prefix])
    completed = _run_gum(args + [message])
    if completed is None or completed.returncode != 0:
        label = level.upper()
        prefix_text = f" {prefix}:" if prefix else ""
        print(f"{label}{prefix_text} {message}")


def _report(status, summary, detail=None):
    label, level = STATUS.get(status, (status.upper(), "info"))
    line = str(summary)
    if detail:
        line += f" · {detail}"
    _gum_log(level, line, prefix=label)


def _run_with_spinner(title, func):
    if not _gum_interactive():
        return func()
    fd, marker_name = tempfile.mkstemp(prefix="fw-gum-spin-", suffix=".done")
    os.close(fd)
    marker = Path(marker_name)
    marker.unlink(missing_ok=True)
    result = {}

    def runner():
        try:
            result["value"] = func()
        except BaseException as exc:
            result["error"] = exc
        finally:
            try:
                marker.touch(exist_ok=True)
            except OSError:
                pass

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    wait_script = (
        "import pathlib,time\n"
        f"marker = pathlib.Path({str(marker)!r})\n"
        "while not marker.exists():\n"
        "    time.sleep(0.1)\n"
    )
    _run_gum([
        "spin", "--spinner", "dot", "--title", title,
        "--spinner.foreground", GUM_COLORS["accent"],
        "--title.foreground", GUM_COLORS["muted"],
        "--", sys.executable, "-c", wait_script,
    ])
    thread.join()
    marker.unlink(missing_ok=True)
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _gum_confirm(message, *, affirmative="继续", negative="退出", default=True):
    if _gum_interactive():
        args = [
            "confirm", message,
            "--affirmative", affirmative, "--negative", negative,
            "--prompt.foreground", GUM_COLORS["accent"],
            "--selected.background", GUM_COLORS["accent"],
            "--selected.foreground", "#0F172A",
            "--unselected.foreground", "#CBD5E1",
        ]
        if default:
            args.append("--default")
        completed = _run_gum(args)
        if completed is not None:
            return completed.returncode == 0
    raw = _prompt_input(f"{message}（回车={affirmative}，q={negative}）").strip().lower()
    return raw != "q"


def _prompt_input(message, placeholder=""):
    if _gum_interactive():
        args = [
            "input", "--prompt", f"{message}: ", "--placeholder", placeholder,
            "--prompt.foreground", GUM_COLORS["accent"],
            "--cursor.foreground", GUM_COLORS["accent"],
        ]
        completed = _run_gum(args, capture_output=True)
        if completed is not None and completed.returncode == 0:
            return completed.stdout.rstrip("\r\n")
        if completed is not None:
            return ""
    try:
        return input(f"{message}: ")
    except EOFError:
        return ""


def ask_relax_time(default_value=2.0):
    selected_choice = "2 秒"
    if default_value == 0.5:
        selected_choice = "0.5 秒"
    elif default_value in (1, 2, 3, 5):
        selected_choice = f"{int(default_value)} 秒"

    if _gum_interactive():
        completed = _run_gum(
            [
                "choose", *RELAX_TIME_CHOICES,
                "--header", "每题操作间隔", "--height", str(len(RELAX_TIME_CHOICES)),
                "--selected", selected_choice,
                "--cursor.foreground", GUM_COLORS["accent"],
                "--selected.foreground", GUM_COLORS["accent"],
                "--header.foreground", GUM_COLORS["muted"],
            ],
            capture_output=True,
        )
        if completed is not None and completed.returncode == 0:
            choice = completed.stdout.strip()
            if choice != "自定义":
                match = re.search(r"\d+(?:\.\d+)?", choice)
                if match:
                    return float(match.group())

    if not sys.stdin.isatty():
        return default_value

    while True:
        raw = (
            _prompt_input(f"自定义每题操作间隔（秒，默认 {default_value}）", str(default_value)).strip()
            or str(default_value)
        )
        try:
            value = float(raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            _report("warn", "输入无效 · 请输入大于等于 0 的数字")


def wait_for_start():
    while True:
        if not _gum_confirm("准备好开始了吗？", affirmative="开始", negative="退出"):
            raise SystemExit(0)
        return


def wait_until_quiz_ready(device):
    while True:
        _gum_log("warn", "请把设备停留在答题界面。准备好后回到这里按回车，我会先尝试读取题号。", prefix="等待")
        wait_for_start()
        try:
            _gum_log("info", "正在读取当前题目状态...", prefix="状态")
            return device.get_remaining_questions()
        except Exception as exc:
            _report("warn", f"还没识别到答题页 · {exc}")


def wait_for_manual_resume(reason):
    _gum_log("warn", f"{reason}\n\n请你在手机上手动完成这一题，然后回到这里按回车继续。", prefix="等待")
    if not _gum_confirm("手动处理完成了吗？", affirmative="继续", negative="退出"):
        raise SystemExit(0)


def ask_continue_next_round():
    return _gum_confirm("继续下一轮？", affirmative="继续", negative="结束")


# ── 设备抽象层 ──

class Device:
    def __init__(self, d):
        self.d = d
        self.is_king_mode = False
        self.position = 1
        self._last_type = ""

    def _count(self, key):
        return self.d(resourceId=RES_ID[key]).count

    def _exists(self, key):
        return self.d(resourceId=RES_ID[key]).exists

    def _get_text(self, key):
        return self.d(resourceId=RES_ID[key]).get_text()

    def _xpath_all(self, key):
        return self.d.xpath(f'//*[@resource-id="{RES_ID[key]}"]').all()

    def _xpath_clickable(self):
        return self.d.xpath('//android.widget.TextView[@clickable="true"]').all()

    def _click_key(self, key_id):
        self.d(resourceId=f"{PKG}:id/key_{key_id}", clickable=True).click()

    def _click_confirm(self):
        self.d(resourceId=RES_ID["key_confirm"]).click()

    TYPE_NAMES = {1: "拼写", 2: "英译汉", 345: "大杂烩", 6: "听音识词", 7: "构词法拼词"}

    def detect_question_type(self):
        self.position = self._detect_position()

        counts = {
            1: self._count("keyboard"),
            7: self._count("part_word"),
            2: self._count("english"),
            345: self._count("question"),
            6: self._count("sound"),
        }

        for mode in (1, 7, 2, 345, 6):
            expected = 2 if self._last_type == self.TYPE_NAMES[mode] else 1
            if counts[mode] == expected:
                self._last_type = self.TYPE_NAMES[mode]
                return mode

        for _ in range(5):
            time.sleep(0.5)
            for mode in (1, 7, 2, 345, 6):
                if self._exists(mode):
                    self._last_type = self.TYPE_NAMES[mode]
                    return mode

        raise Exception("无法识别题型，请检查界面。")

    def _detect_position(self):
        elements = self._xpath_all("position")
        if not elements or len(elements) < 2:
            return 1
        t1, t2 = elements[0].text, elements[-1].text
        if not t1 or not t2:
            return 1
        try:
            m1 = re.search(r"\d+", t1)
            m2 = re.search(r"\d+", t2)
            if m1 and m2:
                return 1 if int(m1.group()) > int(m2.group()) else -1
        except Exception:
            pass
        return 1

    def get_remaining_questions(self):
        title = self._get_text("position")
        if not title:
            raise ValueError("未读取到题号文本")
        title = title.strip()

        if re.search(r"第\s*\d+\s*关", title):
            self.is_king_mode = True
            return 100

        self.is_king_mode = False
        match = re.search(r"(\d+)\s*/\s*(\d+)", title)
        if not match:
            raise ValueError(f"无法解析题号文本: {title!r}")
        current, total = int(match.group(1)), int(match.group(2))
        if total < current:
            raise ValueError(f"题号异常: 当前题号({current})大于总题数({total})")
        return total - current + 1

    def get_choices(self):
        choices = self._xpath_clickable()
        filtered = [c for c in choices if c.text and re.match(r"^[A-C]\.", c.text)]
        if len(filtered) < 3:
            filtered = [c for c in choices if c.text]
            if len(filtered) < 3:
                return None, None, None
        if self.position == 1:
            return filtered[0], filtered[1], filtered[2]
        return filtered[-3], filtered[-2], filtered[-1]

    def get_positional_text(self, key):
        elements = self._xpath_all(key)
        if not elements:
            return ""
        return elements[0].text if self.position == 1 else elements[-1].text


# ── 答题策略 ──

def _compare_similarity(a, b):
    return difflib.SequenceMatcher(None, a, b).quick_ratio()


def _chinese_only(text):
    return "".join(re.findall(r"[\u4e00-\u9fa5]+", text))


def _is_chinese(text):
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def _filter_chinese_and_english(text):
    return "".join(re.findall(r"[a-zA-Z\u4e00-\u9fa5]+", text))


def _best_match_by_meaning(db, candidates, question_mean):
    rates = []
    for word in candidates:
        answer_means = db.get_meanings(word)
        answer_str = _chinese_only("".join(answer_means))
        rates.append(_compare_similarity(answer_str, question_mean))
    return candidates[rates.index(max(rates))]


def _click_choice(button, label, report_status, report_summary, report_detail, relax_time):
    button.click()
    _report(report_status, report_summary, report_detail)
    time.sleep(relax_time)


def _handle_no_answer(device, is_king, report_msg, fallback_fn):
    if is_king:
        raise Exception(f"万词王模式人工介入: {report_msg}")
    _report("warn", "题库未命中", fallback_fn())


def solve_spelling(device, db, relax_time):
    yinbiao = device.get_positional_text("yinbiao")
    chinese = device.get_positional_text("chinese")
    mean = _chinese_only(chinese)

    match = re.search(r"美\[(.+)\]", yinbiao)
    if not match:
        _handle_no_answer(device, device.is_king_mode, "拼写无法提取美式音标", lambda: "已改为试错点击")
        device._click_key("A")
        device._click_confirm()
        time.sleep(3)
        return

    note = match.group(1)
    words = db.search_by_note(note)
    if not words:
        _handle_no_answer(device, device.is_king_mode, "拼写未找到答案", lambda: "已改为试错点击")
        device._click_key("A")
        device._click_confirm()
        time.sleep(3)
        return

    word = _best_match_by_meaning(db, words, mean) if len(words) > 1 else words[0]
    word = db.resolve_spelling(word)

    for char in word:
        device._click_key(char.upper())
    device._click_confirm()
    _report("ok", word, "拼写")
    time.sleep(relax_time)


def solve_english_to_chinese(device, db, relax_time):
    raw = device.get_positional_text("english")
    word = raw.split("\n")[0].strip() if raw else ""
    match = re.match(r"^[a-zA-Z\s\-\(\)\.\']+", word)
    if match:
        word = match.group(0).strip()

    ca, cb, cc = device.get_choices()
    if not all([ca, cb, cc]):
        _report("error", "选项获取失败", "已跳过")
        return

    buttons = [ca, cb, cc]
    prefixes = ["A. ", "B. ", "C. "]
    results = db.get_english_to_chinese(word)

    if results:
        for result in results:
            clean = result[4:-1]
            for btn, pfx in zip(buttons, prefixes):
                choice_text = btn.text.replace(pfx, "")
                if choice_text in clean or clean in choice_text:
                    _click_choice(btn, choice_text, "ok", choice_text, word, relax_time)
                    return
            clean_cn = _chinese_only(clean)
            for btn, pfx in zip(buttons, prefixes):
                choice_cn = _chinese_only(btn.text.replace(pfx, ""))
                if choice_cn in clean_cn or clean_cn in choice_cn:
                    _click_choice(btn, btn.text.replace(pfx, ""), "ok", btn.text.replace(pfx, ""), f"{word} · 汉字兜底", relax_time)
                    return

    answer_means = db.get_meanings(word)
    choices_text = [c.text.replace(f"{chr(65 + i)}. ", "") for i, c in enumerate(buttons)]
    rates = [0, 0, 0]
    for i, choice in enumerate(choices_text):
        cleaned = _chinese_only(choice.replace("；", ""))
        for aw in answer_means:
            ca_clean = _chinese_only(aw)
            rate = _compare_similarity(ca_clean, cleaned)
            if rate > rates[i]:
                rates[i] = rate

    if max(rates) >= 0.5:
        idx = rates.index(max(rates))
        _click_choice(buttons[idx], choices_text[idx], "info", choices_text[idx], f"{word} · 相似度匹配", relax_time)
        return

    _handle_no_answer(device, device.is_king_mode, "英译汉无答案", lambda: f"{word} · 已随机选择")
    buttons[randint(0, 2)].click()
    time.sleep(3)


def solve_word_build(device, db, relax_time):
    part_word = device.get_positional_text("part_word")
    question_mean = _chinese_only(device.get_positional_text("chinese"))
    clickable = device._xpath_clickable()
    parts_on_screen = [e.text for e in clickable]

    candidates = db.get_word_build_answers(part_word, parts_on_screen)
    if not candidates:
        _handle_no_answer(device, device.is_king_mode, "构词法无答案", lambda: "构词法已随机点击")
        if clickable:
            clickable[randint(0, len(clickable) - 1)].click()
        time.sleep(3)
        return

    if len(candidates) == 1:
        parts = candidates[0]["parts_to_click"]
        _report("ok", candidates[0]["word"], "唯一候选")
    else:
        best = _best_match_by_meaning(db, [c["word"] for c in candidates], question_mean)
        idx = next(i for i, c in enumerate(candidates) if c["word"] == best)
        parts = candidates[idx]["parts_to_click"]
        _report("ok", candidates[idx]["word"], "多候选比对后命中")

    for part in parts:
        for elem in clickable:
            if elem.text == part:
                elem.click()
                break
    time.sleep(relax_time)


def solve_mixed(device, db, relax_time):
    text = device.get_positional_text("question")
    ca, cb, cc = device.get_choices()
    if not all([ca, cb, cc]):
        _report("error", "选项获取失败", "已跳过")
        return

    buttons = [ca, cb, cc]
    clean_text = _filter_chinese_and_english(text)

    if _is_chinese(text):
        results = db.get_chinese_to_english(clean_text) or db.get_context_answer(clean_text)
    else:
        results = db.get_context_answer(clean_text)

    if results:
        for result in results:
            clean_result = result[4:-1]
            for i, btn in enumerate(buttons):
                choice_text = btn.text.replace(f"{chr(65 + i)}. ", "")
                if clean_result == choice_text:
                    _click_choice(btn, clean_result, "ok", clean_result, "题库直出", relax_time)
                    return

    if _is_chinese(text):
        choices_text = [c.text.replace(f"{chr(65 + i)}. ", "") for i, c in enumerate(buttons)]
        question_tokens = [t for t in re.split(r"[;；,，、\(\)（）\s]+", text) if t]
        clean_tokens = [_chinese_only(t) for t in question_tokens if _chinese_only(t)]
        full_clean = _chinese_only(text)
        if full_clean and full_clean not in clean_tokens:
            clean_tokens.append(full_clean)

        rates = [0, 0, 0]
        for i, choice_word in enumerate(choices_text):
            for choice_mean in db.get_meanings(choice_word):
                cm = _chinese_only(choice_mean)
                if not cm:
                    continue
                for qt in clean_tokens:
                    if not qt:
                        continue
                    if cm in qt or qt in cm:
                        rates[i] = max(rates[i], 1.0)
                        continue
                    rate = _compare_similarity(qt, cm)
                    if rate > rates[i]:
                        rates[i] = rate

        if max(rates) >= 0.5:
            idx = rates.index(max(rates))
            _click_choice(buttons[idx], choices_text[idx], "info", choices_text[idx], "语义相似度匹配", relax_time)
            return

    _handle_no_answer(device, device.is_king_mode, "大杂烩无答案", lambda: "已随机选择")
    buttons[randint(0, 2)].click()
    time.sleep(3)


def solve_listening(device, db, relax_time):
    ca, cb, cc = device.get_choices()
    if not all([ca, cb, cc]):
        _report("error", "选项获取失败", "已跳过")
        return

    choices_text = [
        ca.text.replace("A. ", "").strip(),
        cb.text.replace("B. ", "").strip(),
        cc.text.replace("C. ", "").strip(),
    ]

    answer = db.get_listen_answer(choices_text)
    if answer:
        answer = answer.strip().strip("'\"")
        candidates = [
            (ca, {ca.text.strip(), choices_text[0]}),
            (cb, {cb.text.strip(), choices_text[1]}),
            (cc, {cc.text.strip(), choices_text[2]}),
        ]
        for btn, valid in candidates:
            if answer in valid:
                _click_choice(btn, answer, "ok", answer, "题库直出", relax_time)
                return

    _handle_no_answer(device, device.is_king_mode, "听音识词无答案", lambda: "已随机选择")
    [ca, cb, cc][randint(0, 2)].click()
    time.sleep(3)


SOLVERS = {
    1: solve_spelling,
    2: solve_english_to_chinese,
    345: solve_mixed,
    6: solve_listening,
    7: solve_word_build,
}


# ── 主程序 ──

def main():
    try:
        relax_time = ask_relax_time(2.0)

        def connect_device():
            try:
                return u2.connect()
            except Exception as e:
                if "Can't find any android device" in str(e) or "emulator" in str(e):
                    subprocess.run(["adb", "kill-server"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    time.sleep(1)
                    subprocess.run(["adb", "start-server"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    time.sleep(3)
                    return u2.connect()
                raise

        d = _run_with_spinner("初始化：连接 Android 设备", connect_device)
        db = _run_with_spinner("初始化：加载题库与索引", Database)
        device = Device(d)

        _gum_log("info", "FuckWeici 已启动", prefix="启动")
        _gum_log("info", f"设备={getattr(d, 'serial', '已连接')}", prefix="环境")
        _gum_log("info", f"题库={Path(db.db_path).resolve()}", prefix="环境")
        _gum_log("info", f"答题间隔={relax_time:.2f}s 包名={PKG}", prefix="环境")
        _gum_log("info", "进入维词答题界面后确认开始；无法处理的题会提示手动接管。", prefix="提示")
    except Exception as exc:
        _gum_log("error", f"启动失败: {exc}\n\n请先确认 adb 已连接设备，且题库文件可以正常读取。", prefix="错误")
        raise SystemExit(1)

    try:
        run_count = 0
        while True:
            total = wait_until_quiz_ready(device)
            solved = 0
            manual = 0
            elapsed = 0.0

            for i in range(total):
                t0 = time.time()
                try:
                    qtype = device.detect_question_type()
                    progress = f"{i + 1}/{total}" if total else str(i + 1)
                    _gum_log("info", f"{progress} {QUESTION_TITLES.get(qtype, '识别成功')}", prefix="题目")
                    SOLVERS[qtype](device, db, relax_time)
                    elapsed += time.time() - t0
                    solved += 1
                except Exception as exc:
                    manual += 1
                    if "万词王模式人工介入" in str(exc):
                        _report("warn", f"需要人工接管 · {exc}")
                    else:
                        _report("error", f"本题未能自动完成 · {exc}")
                    wait_for_manual_resume("这一题脚本没有顺利完成。")

            run_count += 1
            device._last_type = ""
            avg = elapsed / solved if solved else 0.0
            rate = f"{(solved / total) * 100:.0f}%" if total else "0%"
            _gum_log(
                "info",
                f"第 {run_count} 轮 总题数={total} 完成={solved} "
                f"人工={manual} 自动完成率={rate} "
                f"总耗时={elapsed:.2f}s 平均每题={avg:.2f}s",
                prefix="总结",
            )
            if not ask_continue_next_round():
                break
    except Exception as exc:
        _gum_log("error", f"运行中断: {str(exc) or '出现未知错误'}", prefix="错误")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
