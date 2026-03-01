import csv
from collections import Counter

cats = []
titles = []

with open('/Users/rupeshsingh/Downloads/kotabook.com/wc-product-export-2-3-2026-1772392873414.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cats.append(row['Categories'])
        titles.append(row['Name'])

unique_cats = sorted(list(set(cats)))
print("--- Unique Categories ---")
for c in unique_cats:
    print(f"- {c}")

print("\n--- Title Keywords (Institutes) ---")
institutes = ['Allen', 'Aakash', 'Resonance', 'Physics Wallah', 'PW', 'Motion', 'Unacademy', 'Reliable']
found_inst = [inst for inst in institutes if any(inst.lower() in t.lower() for t in titles)]
print(f"Products found for: {found_inst}")
