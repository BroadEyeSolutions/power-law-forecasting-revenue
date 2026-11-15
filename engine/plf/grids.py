"""A grid is one table from the guide: a title, column headers, and rows of (label, values). Written as CSV, one file per table."""
import csv, os

class Grid:
    def __init__(self, name, title, columns, rows=None, note=''):
        self.name, self.title, self.columns, self.note = name, title, list(columns), note
        self.rows = list(rows or [])
    def add(self, label, values):
        self.rows.append((label, list(values))); return self
    def write(self, folder):
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, self.name + '.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(self.columns)
            for label, vals in self.rows:
                w.writerow([label] + ['' if v is None else (repr(float(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else v) for v in vals])
