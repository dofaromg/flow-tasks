from modules.FluinMemoryVault import build_memory
print("Fluin Memory Vault Builder")
log_path = "logs/flmem.log"
entries = []
with open(log_path, encoding="utf-8") as f:
    for line in f:
        try:
            entries.append(eval(line.strip()))
        except:
            pass

output_path = build_memory(entries)
print(f"✅ 記憶模組已建立：{output_path}")