# MRLiou CLI 模擬器與執行器
# CLI-based simulation runner for particle language

import sys
import os
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# 加入當前目錄到路徑以便匯入其他模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logic_pipeline import LogicPipeline
except ImportError:
    # 如果無法匯入，建立簡化版本
    class LogicPipeline:
        def __init__(self):
            self.fn_steps = ["structure", "mark", "flow", "recurse", "store"]
        
        def simulate(self, input_data):
            result = input_data
            for step in self.fn_steps:
                result = f"[{step.upper()} → {result}]"
            return {
                "input": input_data,
                "steps": self.fn_steps,
                "result": result
            }

class ParticleLanguageCLI:
    """MRLiou 粒子語言 CLI 介面"""
    
    def __init__(self):
        self.console = Console()
        self.pipeline = LogicPipeline()
    
    def show_banner(self):
        """顯示歡迎橫幅"""
        banner = Panel.fit(
            "[bold cyan]MRLiou Particle Language Core[/bold cyan]\n"
            "[green]粒子語言核心系統 CLI 模擬器[/green]\n"
            "[dim]FlowAgent 專用任務系統[/dim]",
            style="blue"
        )
        self.console.print(banner)
    
    def show_menu(self):
        """顯示主選單"""
        table = Table(title="可用指令", show_header=True, header_style="bold magenta")
        table.add_column("指令", style="cyan", no_wrap=True)
        table.add_column("說明", style="green")
        
        table.add_row("1", "執行邏輯模擬")
        table.add_row("2", "顯示函數鏈說明") 
        table.add_row("3", "邏輯壓縮/解壓縮測試")
        table.add_row("q", "離開程式")
        
        self.console.print(table)
    
    def run_simulation(self):
        """執行邏輯模擬"""
        user_input = self.console.input("\n[bold]請輸入要處理的資料: [/bold]")
        
        with self.console.status("[bold green]處理中..."):
            result = self.pipeline.simulate(user_input)
        
        # 顯示結果
        result_panel = Panel(
            f"[bold]輸入:[/bold] {result['input']}\n"
            f"[bold]步驟:[/bold] {' → '.join(result['steps'])}\n"
            f"[bold]結果:[/bold] {result['result']}",
            title="執行結果",
            style="green"
        )
        self.console.print(result_panel)
    
    def show_function_chain(self):
        """顯示函數鏈說明"""
        explanations = {
            "structure": "定義輸入資料結構",
            "mark": "建立邏輯跳點標記",
            "flow": "轉換為流程結構節奏", 
            "recurse": "遞歸展開為細部結構",
            "store": "封存至邏輯記憶模組"
        }
        
        table = Table(title="MRLiou 函數鏈說明", show_header=True, header_style="bold blue")
        table.add_column("步驟", style="cyan", no_wrap=True)
        table.add_column("英文", style="yellow")
        table.add_column("說明", style="green")
        
        for i, step in enumerate(self.pipeline.fn_steps, 1):
            table.add_row(str(i), step.upper(), explanations.get(step, "未知"))
        
        self.console.print(table)
    
    def test_compression(self):
        """測試邏輯壓縮/解壓縮"""
        test_steps = ["structure", "mark", "flow", "recurse", "store"]
        compressed = self.pipeline.compress_logic(test_steps)
        decompressed = self.pipeline.decompress_logic(compressed)
        
        compression_panel = Panel(
            f"[bold]原始步驟:[/bold] {' → '.join(test_steps)}\n"
            f"[bold]壓縮形式:[/bold] {compressed}\n"
            f"[bold]解壓縮:[/bold] {' → '.join(decompressed)}",
            title="壓縮/解壓縮測試",
            style="yellow"
        )
        self.console.print(compression_panel)
    
    def run(self):
        """主執行迴圈"""
        self.show_banner()
        
        while True:
            self.console.print()
            self.show_menu()
            
            choice = self.console.input("\n[bold]請選擇功能 (1-3, q): [/bold]").strip().lower()
            
            if choice == "1":
                self.run_simulation()
            elif choice == "2":
                self.show_function_chain()
            elif choice == "3":
                self.test_compression()
            elif choice == "q":
                self.console.print("[bold red]程式結束，感謝使用！[/bold red]")
                break
            else:
                self.console.print("[bold red]無效的選項，請重新選擇[/bold red]")

def main():
    """主函數"""
    try:
        cli = ParticleLanguageCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n程式已中斷")
    except Exception as e:
        print(f"執行錯誤: {e}")

if __name__ == "__main__":
    main()