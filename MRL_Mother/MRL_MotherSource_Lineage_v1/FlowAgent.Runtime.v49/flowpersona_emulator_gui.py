
# flowpersona_emulator_gui.py - 簡易 GUI 語場模擬器（使用 tkinter）

import os
import random
import tkinter as tk
from tkinter import ttk, messagebox

MEMORY_DIR = "memory"

def list_fltnz():
    return sorted([
        f for f in os.listdir(MEMORY_DIR)
        if f.endswith(".fltnz")
    ])

def load_lines(filepath):
    with open(os.path.join(MEMORY_DIR, filepath), "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

class FlowPersonaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FlowPersona 語場人格模擬器 GUI")
        self.memory_files = list_fltnz()

        self.persona_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self.setup_widgets()

    def setup_widgets(self):
        ttk.Label(self.root, text="選擇語場模組：").grid(row=0, column=0, sticky="w")
        self.persona_menu = ttk.Combobox(self.root, textvariable=self.persona_var, values=self.memory_files, state="readonly", width=40)
        self.persona_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.root, text="輸入：").grid(row=1, column=0, sticky="w")
        self.input_entry = ttk.Entry(self.root, textvariable=self.input_var, width=50)
        self.input_entry.grid(row=1, column=1, padx=5, pady=5)
        self.input_entry.bind("<Return>", self.respond)

        ttk.Label(self.root, text="模擬回應：").grid(row=2, column=0, sticky="nw")
        self.output_display = tk.Text(self.root, height=10, width=50, wrap="word")
        self.output_display.grid(row=2, column=1, padx=5, pady=5)

        self.send_button = ttk.Button(self.root, text="送出", command=self.respond)
        self.send_button.grid(row=3, column=1, sticky="e", padx=5, pady=5)

    def respond(self, event=None):
        persona_file = self.persona_var.get()
        if not persona_file:
            messagebox.showwarning("未選擇模組", "請先選擇語場模組。")
            return

        if not self.input_var.get().strip():
            return

        lines = load_lines(persona_file)
        response = random.choice(lines) if lines else "（空白人格語場）"
        self.output_display.insert(tk.END, f"你 > {self.input_var.get()}
")
        self.output_display.insert(tk.END, f"人格 > {response}

")
        self.output_display.see(tk.END)
        self.input_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = FlowPersonaGUI(root)
    root.mainloop()
