import zipfile
import json
import argparse
from pathlib import Path

def run_seed(flpkg_path, mode="translate", save=False):
    if not Path(flpkg_path).exists():
        print(f"[✘] 檔案不存在：{flpkg_path}")
        return

    with zipfile.ZipFile(flpkg_path, "r") as zipf:
        structure = json.loads(zipf.read("structure.json").decode("utf-8"))
        fltnz = zipf.read("seed.fltnz").decode("utf-8").splitlines()

    print("🧠 [FluinCoreSeed 模擬執行]")
    print("→ 模式：", mode)
    print("→ fltnz 語句：", " ".join(fltnz))

    if mode == "translate":
        words = [entry["zh"] for entry in structure if entry["zh"]]
        print("🗣️ 翻譯結果（自然語）：", "".join(words))

        if save:
            output = {
                "flpkg": Path(flpkg_path).name,
                "fltnz": fltnz,
                "translated": "".join(words)
            }
            Path("storage/flows").mkdir(parents=True, exist_ok=True)
            out_path = Path("storage/flows") / (Path(flpkg_path).stem + ".json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print("📦 結果已儲存至：", out_path)

    elif mode == "generate":
        print("🚧 [尚未實作] 語場生成模擬器（未來支援跳點與人格觸發）")
    else:
        print("[✘] 不支援的模式")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help=".flpkg 封裝檔")
    parser.add_argument("--mode", default="translate", help="模式：translate 或 generate")
    parser.add_argument("--save", action="store_true", help="是否儲存結果至 /storage/flows/")
    args = parser.parse_args()

    run_seed(args.file, mode=args.mode, save=args.save)
