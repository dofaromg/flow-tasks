import argparse
import json
import re

def parse_fltnz(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    trace_lines = content.strip().splitlines()
    parsed = []

    for line in trace_lines:
        match_ping = re.match(r"\[(.*?)\]\s+::pinged→\s+(.*)", line)
        match_response = re.match(r"\[(.*?)\]\s+::response→\s+『(.*?)』", line)
        match_init = "::initiated::" in line
        if match_ping:
            parsed.append({
                "timestamp": match_ping.group(1),
                "action": "pinged",
                "target": match_ping.group(2).strip()
            })
        elif match_response:
            parsed.append({
                "timestamp": match_response.group(1),
                "action": "response",
                "message": match_response.group(2).strip()
            })
        elif match_init:
            parsed.append({
                "action": "initiated"
            })

    return parsed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FluinTraceInterpreter - 粒子語場記憶解析器")
    parser.add_argument("--input", required=True, help="輸入 .fltnz 檔案路徑")
    parser.add_argument("--output", required=False, help="輸出 JSON 檔案路徑（預設與輸入同名）")
    args = parser.parse_args()

    output_path = args.output or args.input.replace(".fltnz", ".parsed.json")
    result = parse_fltnz(args.input)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[✓] 已解析完畢：{output_path}")
