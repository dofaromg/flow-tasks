#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.IO.CLI — MRL 專屬 CLI 顯示引擎（零外部依賴版）
Mr.liou.IO.CLI.v1

替代 rich 函式庫，使用純 Python ANSI 逃逸碼實現：
  - 彩色輸出（前景/背景色）
  - 表格渲染
  - 進度條
  - 面板 / 橫幅
  - 狀態指示器

完全零外部依賴：僅使用 sys, os, time, threading。
"""

import sys
import os
import time
import threading
import shutil
from typing import Any, Dict, List, Optional, Tuple


# ===========================================================================
# ANSI 色彩碼
# ===========================================================================

class _ANSI:
    """ANSI 逃逸碼常數"""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK   = "\033[5m"
    REVERSE = "\033[7m"

    # 前景色
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # 亮色前景
    BRIGHT_BLACK   = "\033[90m"
    BRIGHT_RED     = "\033[91m"
    BRIGHT_GREEN   = "\033[92m"
    BRIGHT_YELLOW  = "\033[93m"
    BRIGHT_BLUE    = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN    = "\033[96m"
    BRIGHT_WHITE   = "\033[97m"

    # 背景色
    BG_BLACK   = "\033[40m"
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"

    # 滑鼠/游標
    CLEAR_LINE   = "\033[2K\r"
    CURSOR_UP    = "\033[1A"
    HIDE_CURSOR  = "\033[?25l"
    SHOW_CURSOR  = "\033[?25h"

    @staticmethod
    def supports_color() -> bool:
        """偵測終端是否支援 ANSI 色彩"""
        if os.getenv("NO_COLOR"):
            return False
        if os.getenv("FORCE_COLOR"):
            return True
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, *codes: str) -> str:
    """套用 ANSI 碼，自動偵測是否支援色彩"""
    if not _ANSI.supports_color():
        return text
    return "".join(codes) + text + _ANSI.RESET


# ===========================================================================
# 標記語言解析器（rich 相容子集）
# ===========================================================================

_MARKUP_MAP = {
    "bold":        _ANSI.BOLD,
    "dim":         _ANSI.DIM,
    "italic":      _ANSI.ITALIC,
    "underline":   _ANSI.UNDERLINE,
    "red":         _ANSI.RED,
    "green":       _ANSI.GREEN,
    "yellow":      _ANSI.YELLOW,
    "blue":        _ANSI.BLUE,
    "magenta":     _ANSI.MAGENTA,
    "cyan":        _ANSI.CYAN,
    "white":       _ANSI.WHITE,
    "bright_red":  _ANSI.BRIGHT_RED,
    "bright_green": _ANSI.BRIGHT_GREEN,
    "bright_cyan": _ANSI.BRIGHT_CYAN,
    "bold cyan":   _ANSI.BOLD + _ANSI.CYAN,
    "bold green":  _ANSI.BOLD + _ANSI.GREEN,
    "bold red":    _ANSI.BOLD + _ANSI.RED,
    "bold magenta": _ANSI.BOLD + _ANSI.MAGENTA,
    "bold yellow": _ANSI.BOLD + _ANSI.YELLOW,
    "bold blue":   _ANSI.BOLD + _ANSI.BLUE,
    "bold white":  _ANSI.BOLD + _ANSI.WHITE,
}


def markup(text: str) -> str:
    """
    解析 [tag]text[/tag] 標記語法（rich 相容子集）

    示例：
        markup("[bold cyan]Hello[/bold cyan] [green]World[/green]")
    """
    if not _ANSI.supports_color():
        import re
        return re.sub(r"\[/?[^\]]*\]", "", text)

    import re
    result = text

    # 處理複合標籤（如 [bold cyan]）
    def replace_tag(m: re.Match) -> str:
        tag = m.group(1).lower()
        content = m.group(2)
        code = _MARKUP_MAP.get(tag, "")
        return code + content + _ANSI.RESET

    # 匹配 [tag]content[/tag] 模式（貪婪最短匹配）
    pattern = r"\[([^\]/]+)\](.*?)\[/\1\]"
    for _ in range(5):  # 最多 5 層巢狀
        new_result = re.sub(pattern, replace_tag, result, flags=re.DOTALL)
        if new_result == result:
            break
        result = new_result

    # 移除剩餘的孤立標籤
    result = re.sub(r"\[/?[^\]]*\]", "", result)
    return result


# ===========================================================================
# Console — 主要輸出介面
# ===========================================================================

class Console:
    """
    Mr.liou.IO.Console — rich.Console 相容替代

    使用方式：
        console = Console()
        console.print("[bold cyan]Hello[/bold cyan]")
        console.print_table(["名稱", "值"], [["A", "1"], ["B", "2"]])
    """

    def __init__(
        self,
        file=None,
        force_color: bool = False,
        no_color: bool = False,
    ):
        self._file = file or sys.stdout
        self._force_color = force_color
        self._no_color = no_color
        self._lock = threading.Lock()

    def _write(self, text: str, end: str = "\n"):
        with self._lock:
            self._file.write(text + end)
            self._file.flush()

    def print(self, *args, sep: str = " ", end: str = "\n", markup_enabled: bool = True):
        """輸出並解析標記語言"""
        parts = []
        for a in args:
            s = str(a)
            if markup_enabled:
                s = markup(s)
            parts.append(s)
        self._write(sep.join(parts), end)

    def log(self, *args, level: str = "INFO"):
        """帶時間戳和等級的日誌輸出"""
        ts = time.strftime("%H:%M:%S")
        level_colors = {
            "INFO":    _ANSI.GREEN,
            "WARNING": _ANSI.YELLOW,
            "ERROR":   _ANSI.RED,
            "DEBUG":   _ANSI.CYAN,
        }
        lc = level_colors.get(level, "")
        msg = " ".join(str(a) for a in args)
        if _ANSI.supports_color():
            prefix = f"{_ANSI.DIM}{ts}{_ANSI.RESET} {lc}{level:7s}{_ANSI.RESET}"
        else:
            prefix = f"{ts} {level:7s}"
        self._write(f"{prefix} {msg}")

    def input(self, prompt: str = "") -> str:
        """帶標記解析的 input 輸入"""
        p = markup(prompt) if _ANSI.supports_color() else prompt
        return input(p)

    def rule(self, title: str = "", char: str = "─", width: Optional[int] = None):
        """水平分隔線"""
        w = width or self._term_width()
        if title:
            title_str = markup(f" {title} ")
            # 估計可見字符寬度
            import re
            visible = re.sub(r"\033\[[^m]*m", "", title_str)
            side = max(1, (w - len(visible)) // 2)
            line = char * side + title_str + char * (w - side - len(visible))
        else:
            line = char * w
        self._write(_c(line, _ANSI.DIM))

    def _term_width(self) -> int:
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80

    def status(self, message: str) -> "_StatusContext":
        """返回可用於 with 語句的狀態指示器"""
        return _StatusContext(self, message)

    def print_json(self, data: Any, indent: int = 2):
        """格式化輸出 JSON"""
        import json
        text = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        # 簡單語法高亮
        if _ANSI.supports_color():
            import re
            text = re.sub(r'"([^"]+)":', lambda m: f'{_ANSI.CYAN}"{m.group(1)}"{_ANSI.RESET}:', text)
            text = re.sub(r':\s*"([^"]*)"', lambda m: f': {_ANSI.GREEN}"{m.group(1)}"{_ANSI.RESET}', text)
            text = re.sub(r':\s*(\d+\.?\d*)', lambda m: f': {_ANSI.YELLOW}{m.group(1)}{_ANSI.RESET}', text)
        self._write(text)


# ===========================================================================
# StatusContext — with 語句狀態動畫
# ===========================================================================

class _StatusContext:
    _SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, console: Console, message: str):
        self._console = console
        self._message = markup(message)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def __enter__(self):
        if _ANSI.supports_color():
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            self._console._write(f"[...] {self._message}")
        return self

    def __exit__(self, *_):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            sys.stdout.write(_ANSI.CLEAR_LINE)
            sys.stdout.flush()

    def _spin(self):
        i = 0
        while not self._stop_event.is_set():
            frame = self._SPINNER[i % len(self._SPINNER)]
            line = f"\r{_ANSI.GREEN}{frame}{_ANSI.RESET} {self._message}"
            sys.stdout.write(line)
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1


# ===========================================================================
# Table — ASCII 表格渲染
# ===========================================================================

class Table:
    """
    Mr.liou.IO.Table — rich.Table 相容替代

    使用方式：
        t = Table(title="粒子列表")
        t.add_column("名稱", style="cyan")
        t.add_column("準確率", style="green")
        t.add_row("Reasoning.P1", "0.9234")
        console.print(t)
    """

    def __init__(
        self,
        title: str = "",
        show_header: bool = True,
        header_style: str = "bold",
        border_style: str = "dim",
        show_lines: bool = False,
        padding: int = 1,
    ):
        self.title = title
        self.show_header = show_header
        self.header_style = header_style
        self.border_style = border_style
        self.show_lines = show_lines
        self.padding = padding
        self._columns: List[Dict] = []
        self._rows: List[List[str]] = []

    def add_column(
        self,
        header: str,
        style: str = "",
        no_wrap: bool = False,
        min_width: int = 0,
        max_width: int = 0,
        justify: str = "left",
    ) -> "Table":
        self._columns.append({
            "header": header,
            "style": style,
            "no_wrap": no_wrap,
            "min_width": min_width,
            "max_width": max_width,
            "justify": justify,
        })
        return self

    def add_row(self, *values: str) -> "Table":
        row = [str(v) for v in values]
        # 補足欄位數
        while len(row) < len(self._columns):
            row.append("")
        self._rows.append(row)
        return self

    def _col_widths(self) -> List[int]:
        widths = [len(col["header"]) for col in self._columns]
        for row in self._rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(cell))
        # 套用 min/max
        for i, col in enumerate(self._columns):
            if col["min_width"]:
                widths[i] = max(widths[i], col["min_width"])
            if col["max_width"]:
                widths[i] = min(widths[i], col["max_width"])
        # 加 padding
        return [w + self.padding * 2 for w in widths]

    def __str__(self) -> str:
        widths = self._col_widths()
        total_w = sum(widths) + len(widths) + 1
        border = _c("─" * total_w, _ANSI.DIM)
        lines = []

        # 標題
        if self.title:
            title_str = markup(f" {self.title} ")
            import re
            visible_len = len(re.sub(r"\033\[[^m]*m", "", title_str))
            pad = max(0, (total_w - visible_len) // 2)
            lines.append(" " * pad + title_str)

        # 上邊框
        top = _c("┌" + "┬".join("─" * w for w in widths) + "┐", _ANSI.DIM)
        lines.append(top)

        # 表頭
        if self.show_header:
            cells = []
            for i, col in enumerate(self._columns):
                h = col["header"].center(widths[i] - self.padding * 2)
                pad_s = " " * self.padding
                cells.append(
                    pad_s + markup(f"[{self.header_style}]{h}[/{self.header_style}]") + pad_s
                )
            lines.append(_c("│", _ANSI.DIM) + _c("│", _ANSI.DIM).join(cells) + _c("│", _ANSI.DIM))
            sep = _c("├" + "┼".join("─" * w for w in widths) + "┤", _ANSI.DIM)
            lines.append(sep)

        # 資料行
        for row_idx, row in enumerate(self._rows):
            cells = []
            for i, col in enumerate(self._columns):
                cell_val = row[i] if i < len(row) else ""
                style = col.get("style", "")
                if style:
                    cell_val = markup(f"[{style}]{cell_val}[/{style}]")
                # 計算對齊（基於可見寬度）
                import re
                vis = re.sub(r"\033\[[^m]*m", "", cell_val)
                w = widths[i] - self.padding * 2
                pad_needed = max(0, w - len(vis))
                just = col.get("justify", "left")
                if just == "right":
                    cell_val = " " * pad_needed + cell_val
                elif just == "center":
                    left_pad = pad_needed // 2
                    right_pad = pad_needed - left_pad
                    cell_val = " " * left_pad + cell_val + " " * right_pad
                else:
                    cell_val = cell_val + " " * pad_needed
                cells.append(" " * self.padding + cell_val + " " * self.padding)

            lines.append(_c("│", _ANSI.DIM) + _c("│", _ANSI.DIM).join(cells) + _c("│", _ANSI.DIM))

            if self.show_lines and row_idx < len(self._rows) - 1:
                sep = _c("├" + "┼".join("─" * w for w in widths) + "┤", _ANSI.DIM)
                lines.append(sep)

        # 下邊框
        bottom = _c("└" + "┴".join("─" * w for w in widths) + "┘", _ANSI.DIM)
        lines.append(bottom)

        return "\n".join(lines)


# ===========================================================================
# Panel — 帶邊框的面板
# ===========================================================================

class Panel:
    """
    Mr.liou.IO.Panel — rich.Panel 相容替代

    使用方式：
        panel = Panel("[bold]MRL System[/bold]\\n粒子語言核心", title="系統資訊")
        console.print(panel)
    """

    def __init__(
        self,
        content: str,
        title: str = "",
        subtitle: str = "",
        style: str = "",
        width: Optional[int] = None,
        padding: int = 1,
    ):
        self.content = content
        self.title = title
        self.subtitle = subtitle
        self.style = style
        self._width = width
        self.padding = padding

    @classmethod
    def fit(cls, content: str, **kwargs) -> "Panel":
        """自動適應寬度的 Panel"""
        return cls(content, **kwargs)

    def _term_width(self) -> int:
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80

    def __str__(self) -> str:
        import re
        w = self._width or min(self._term_width(), 80)
        inner_w = w - 2  # 減去左右邊框

        # 解析內容行
        raw_content = markup(self.content)
        raw_lines = raw_content.split("\n")

        # 頂部邊框
        if self.title:
            title_str = markup(f" {self.title} ")
            vis_title = re.sub(r"\033\[[^m]*m", "", title_str)
            side_len = max(1, (inner_w - len(vis_title)) // 2)
            top_line = "─" * side_len + title_str + "─" * max(0, inner_w - side_len - len(vis_title))
        else:
            top_line = "─" * inner_w

        border_code = _MARKUP_MAP.get(self.style, _ANSI.DIM)
        lines = [_c("╭" + top_line + "╮", border_code)]

        # 上 padding
        for _ in range(self.padding):
            lines.append(_c("│", border_code) + " " * inner_w + _c("│", border_code))

        # 內容
        for raw in raw_lines:
            vis = re.sub(r"\033\[[^m]*m", "", raw)
            pad_right = max(0, inner_w - self.padding - len(vis))
            lines.append(
                _c("│", border_code)
                + " " * self.padding
                + raw
                + " " * pad_right
                + _c("│", border_code)
            )

        # 下 padding
        for _ in range(self.padding):
            lines.append(_c("│", border_code) + " " * inner_w + _c("│", border_code))

        # 底部邊框
        if self.subtitle:
            sub_str = markup(f" {self.subtitle} ")
            vis_sub = re.sub(r"\033\[[^m]*m", "", sub_str)
            side_len = max(1, (inner_w - len(vis_sub)) // 2)
            bot_line = "─" * side_len + sub_str + "─" * max(0, inner_w - side_len - len(vis_sub))
        else:
            bot_line = "─" * inner_w
        lines.append(_c("╰" + bot_line + "╯", border_code))

        return "\n".join(lines)


# ===========================================================================
# ProgressBar — 進度條
# ===========================================================================

class ProgressBar:
    """
    Mr.liou.IO.ProgressBar — 進度條

    使用方式：
        bar = ProgressBar(total=100, description="訓練中")
        for i in range(100):
            bar.update(1)
        bar.finish()
    """

    def __init__(
        self,
        total: int = 100,
        description: str = "",
        width: int = 30,
        fill: str = "█",
        empty: str = "░",
    ):
        self.total = total
        self.description = description
        self.width = width
        self.fill = fill
        self.empty = empty
        self._current = 0
        self._start = time.time()
        self._last_render = 0.0

    def update(self, n: int = 1):
        self._current = min(self._current + n, self.total)
        now = time.time()
        if now - self._last_render >= 0.1:  # 最多每 100ms 渲染一次
            self._render()
            self._last_render = now

    def _render(self):
        pct = self._current / self.total if self.total > 0 else 0
        filled = int(self.width * pct)
        bar = self.fill * filled + self.empty * (self.width - filled)
        elapsed = time.time() - self._start
        speed = self._current / elapsed if elapsed > 0 else 0
        eta = (self.total - self._current) / speed if speed > 0 else 0

        if _ANSI.supports_color():
            bar_str = _c(bar, _ANSI.GREEN)
        else:
            bar_str = bar

        desc = f"{self.description} " if self.description else ""
        line = (f"\r{desc}[{bar_str}] "
                f"{_c(f'{pct*100:.1f}%', _ANSI.YELLOW)} "
                f"{self._current}/{self.total} "
                f"{_c(f'ETA:{eta:.0f}s', _ANSI.DIM)}")
        sys.stdout.write(line)
        sys.stdout.flush()

    def finish(self):
        self._current = self.total
        self._render()
        sys.stdout.write("\n")
        sys.stdout.flush()


# ===========================================================================
# 便利函數（模擬 rich.print）
# ===========================================================================

_default_console = Console()


def print(*args, **kwargs):
    """全域 MRL print（解析標記語言）"""
    _default_console.print(*args, **kwargs)


def log(*args, level: str = "INFO"):
    """全域 MRL log"""
    _default_console.log(*args, level=level)


def rule(title: str = "", char: str = "─"):
    """全域分隔線"""
    _default_console.rule(title, char)


# ===========================================================================
# 自檢測試
# ===========================================================================

if __name__ == "__main__":
    console = Console()

    # 橫幅
    console.print(str(Panel(
        "[bold cyan]MRL 粒子語言核心系統[/bold cyan]\n"
        "[green]Mr.liou.IO.CLI.v1[/green]\n"
        "[dim]零外部依賴 CLI 引擎[/dim]",
        title="MRL System",
        style="blue",
        width=50,
    )))

    # 表格
    table = Table(title="MRL 粒子狀態", show_header=True, header_style="bold magenta")
    table.add_column("粒子名稱", style="cyan")
    table.add_column("類型", style="green")
    table.add_column("準確率", style="yellow", justify="right")
    table.add_column("LoRA 秩", justify="right")

    table.add_row("Particle.Reasoning.P1", "reasoning", "0.9234", "16")
    table.add_row("Particle.Coding.P1", "coding", "0.8871", "8")
    table.add_row("Particle.Language.P1", "language", "0.9100", "4")
    console.print(str(table))

    # 日誌
    console.log("系統初始化完成")
    console.log("準確率超過閾值", level="WARNING")
    console.log("IO 錯誤偵測", level="ERROR")

    # 分隔線
    console.rule("[bold green]訓練進度[/bold green]")

    # 進度條
    bar = ProgressBar(total=50, description="蒸餾訓練")
    for i in range(50):
        bar.update(1)
        time.sleep(0.01)
    bar.finish()

    # JSON 輸出
    console.print("\n[bold]粒子配置 JSON：[/bold]")
    console.print_json({
        "name": "Mr.liou.Particle.Reasoning.P1.v1",
        "type": "reasoning",
        "lora_rank": 16,
        "accuracy": 0.9234,
    })

    console.print("\n[bold green]✅ Mr.liou.IO.CLI 自檢完成[/bold green]")
