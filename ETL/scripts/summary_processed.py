from pathlib import Path
import csv
p = Path('data/processed/orders_processed.csv')
print('path', p.resolve())
print('exists', p.exists())
if not p.exists():
    raise SystemExit(1)
rows = 0
tot = 0.0
sample = []
with p.open(newline='', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for i, row in enumerate(reader):
        if i < 5:
            sample.append(row)
        rows += 1
        try:
            tot += float(row.get('total_amount') or 0)
        except Exception:
            pass
print('rows', rows)
print('total_amount_sum', tot)
print('\nSample rows (first 5):')
for r in sample:
    print(r)
