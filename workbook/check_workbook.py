"""Checks the workbook's formulas against the engine: every guide table the workbook carries (layout.json says where) must give
the engine's numbers. The workbook must be recalculated first (open and save it in Excel, or LibreOffice headless).

  python3 workbook/check_workbook.py [workbook.xlsx]

It reads the engine's tables from the repository's own outputs/ folder, so run python3 check.py first, without --out.
"""
import csv, json, os, sys
from openpyxl import load_workbook
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def num(v):
    if v is None or v == '': return None
    try: return float(v)
    except (TypeError, ValueError): return v
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'Forecasting-Revenue_Workbook.xlsx')
    L = json.load(open(os.path.join(HERE, 'layout.json'))); wb = load_workbook(path, data_only=True)
    ok = bad = 0; probs = []
    for t in L['tables']:
        ws = wb[t['sheet']]; eng = list(csv.reader(open(os.path.join(ROOT, 'outputs', 'chapter-' + t['grid'][0], t['grid'] + '.csv'), encoding='utf-8')))[1:]
        used = set(); pcols = set()
        for p in t['pct']:
            if p.startswith('@cols:'): pcols = {int(x) for x in p[6:].split(',')}
        for i, lab in enumerate(t['labels']):
            r = t['first_row'] + i
            if (ws.cell(r, 1).value or '').replace('’', "'") != lab.replace('’', "'"): probs.append((t['grid'], lab, f'sheet row {r} is {ws.cell(r, 1).value!r}')); bad += 1; continue
            same = (lambda a, b_: a.replace('’', "'").startswith(b_.replace('’', "'")[:28])) if t.get('match') == 'prefix' else (lambda a, b_: a.replace('’', "'") == b_.replace('’', "'"))
            er = next((j for j, e in enumerate(eng) if j not in used and same(e[0], lab)), None)
            if er is None: probs.append((t['grid'], lab, 'no engine row')); bad += 1; continue
            used.add(er)
            for j in range(t['ncols']):
                if j in t.get('skip', []): continue
                w = num(ws.cell(r, t['col'] + j).value); e = num(eng[er][1 + j]) if 1 + j < len(eng[er]) else None
                if isinstance(w, float) and (lab in t['pct'] or j in pcols): w *= 100
                if w is None and e is None: continue
                if isinstance(w, float) and isinstance(e, float) and abs(w - e) <= 1e-6 * max(1.0, abs(e)): ok += 1; continue
                if isinstance(w, str) and str(w).startswith('#'): probs.append((t['grid'], lab, f'col {j + 1}: Excel error {w}')); bad += 1; continue
                probs.append((t['grid'], lab, f'col {j + 1}: workbook {w!r}, engine {e!r}')); bad += 1
    print(f'{ok:,} workbook cells match the engine, {bad:,} do not ({len(L["tables"])} tables).')
    for p in probs[:40]: print('  ', *p)
    sys.exit(0 if bad == 0 else 1)
if __name__ == '__main__':
    main()
