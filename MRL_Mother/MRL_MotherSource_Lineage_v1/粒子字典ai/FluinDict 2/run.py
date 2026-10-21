from dict_loader import load_dictionary, query_symbol

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="輸入粒子語素查詢")
    args = parser.parse_args()

    d = load_dictionary()
    if args.query:
        result = query_symbol(d, args.query)
        if result:
            print(f"語素：{args.query}")
            for k, v in result.items():
                print(f"{k}: {v}")
        else:
            print("❌ 找不到對應語素。")
