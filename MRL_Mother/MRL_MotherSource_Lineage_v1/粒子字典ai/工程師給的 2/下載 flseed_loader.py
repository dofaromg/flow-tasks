import zipfile
import json
import yaml
from pathlib import Path

def load_flseed(flseed_path):
    if not Path(flseed_path).exists():
        print(f"[✘] 檔案不存在：{flseed_path}")
        return

    with zipfile.ZipFile(flseed_path, "r") as zipf:
        manifest = yaml.safe_load(zipf.read("manifest.yml").decode("utf-8"))
        fltnz = zipf.read("seed.fltnz").decode("utf-8").splitlines()
        structure = json.loads(zipf.read("structure.json").decode("utf-8"))
        env = json.loads(zipf.read("env.medium.json").decode("utf-8"))
        vec = json.loads(zipf.read("flynz.vec.json").decode("utf-8"))

    print("🔹 FLUIN CORE SEED LOADED")
    print("📦 Package:", manifest["package"])
    print("🧬 Crystallized:", manifest.get("crystallized", False))
    print("🌐 環境節奏:", env["tempo_bpm"], "bpm")
    print("🎯 語素鏈:")
    print("  ", " ".join(fltnz))

    print("\n🔍 向量映射:")
    for k, v in vec.items():
        print(f"  {k}: {v}")

    print("\n🧠 語素結構:")
    for e in structure:
        print(f"  {e['code']} → {e['zh']} [{e['pcode']}]")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法：python flseed_loader.py your.flseed")
        sys.exit(1)

    load_flseed(sys.argv[1])
