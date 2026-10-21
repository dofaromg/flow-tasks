import csv

def load_dictionary(path="dictionary/fluin_dictionary_base.csv"):
    data = {}
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data[row["symbol"]] = row
    return data

def query_symbol(dictionary, symbol):
    return dictionary.get(symbol)
