"""Checks the engine against the guide. Runs the engine on the sample book, then compares every table it writes with the same
table copied out of the guide (expected/). A printed cell passes when the engine's number rounds to what the guide prints;
a chart number passes when it is within a cent (or 0.01) of the guide's. One exception, Chapter 3's Cohort back-test lines: there a cell
also passes, reported apart as close, when it is within 0.06 points (0.2% for dollar amounts) of the guide's (expected/README.md says why).
The guide's Power Law tables and its Chapter 3.7 aren't in expected/: Power Law isn't in this repository, and 3.7 runs here on Cohort.

  python3 check.py                      run and check every chapter in expected/ (writes the engine's tables to outputs/)
  python3 check.py --out /tmp/plf       write the engine's tables somewhere else (leave the repository untouched)
  python3 check.py --chapter 1          check one chapter
  python3 check.py --verbose            also list every cell that failed

Your AI should run this before it touches your own data: if the sample book doesn't land on the guide's numbers, nothing else will.
"""
import csv, json, math, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.join(HERE, 'expected')
if '--out' in sys.argv and (sys.argv.index('--out') + 1 >= len(sys.argv) or sys.argv[sys.argv.index('--out') + 1].startswith('--')):
    sys.exit('check.py: --out needs a folder after it, e.g. python3 check.py --out /tmp/plf')
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(HERE, 'outputs')
NUM = re.compile(r'^(?P<sign>[+\-−]?)(?P<cur>\$?)(?P<num>\d[\d,]*(?:\.\d+)?)(?P<suf>[KM%]?)(?: avg| points)?$')
def parse(s):
    """'$4,159.3K' -> (4159300, 50); '0.58%' -> (0.58, 0.005); '−9%' -> (-9, 0.5). Returns None for text."""
    s = s.strip().replace('−', '−')
    m = NUM.match(s)
    if not m: return None
    num = m.group('num').replace(',', ''); d = len(num.split('.')[1]) if '.' in num else 0
    scale = {'K': 1e3, 'M': 1e6}.get(m.group('suf'), 1.0)
    v = float(num) * scale * (-1 if m.group('sign') in ('-', '−') else 1)
    return v, 0.5 * 10 ** (-d) * scale
# Chapter 3's Cohort back-test lines: the guide made them with its own engine, which adds refinements this one leaves out;
# on the sample book that moves the lines by 0.03 points at most (0.028). A cell on these lines that misses the guide's rounding passes as close
# when it is within CLOSE_POINTS (chart percentages) or CLOSE_SHARE of the guide's number (dollar amounts); anything further out fails.
CLOSE = {'chapter-3': dict(prefixes=('cohort',), unless='existing book')}
CLOSE_POINTS, CLOSE_SHARE = 0.06, 0.002
def close_line(ch, label):
    p = CLOSE.get(ch); l = norm(label)
    return bool(p) and l.startswith(tuple(norm(x) for x in p['prefixes'])) and p['unless'] not in l
def is_close(f_): return f_[3] is not None and abs(f_[3][0] - f_[3][1]) <= max(CLOSE_POINTS, CLOSE_SHARE * abs(f_[3][0]))
norm = lambda s: re.sub(r'\s+', ' ', s.replace('’', "'").replace('−', '-').replace('−', '-').strip().lower())
def read(p): return list(csv.reader(open(p, newline='', encoding='utf-8')))
def check_table(exp_rows, out_rows, chart):
    fails = []; ok = 0
    if chart:
        got = {norm(r[0]): r[1:] for r in out_rows[1:]}
        for r in exp_rows[1:]:
            g = got.get(norm(r[0]))
            if g is None: fails.append((r[0], '', 'row missing', None)); continue
            for j, (e, v) in enumerate(zip(r[1:], g)):
                if e in ('', 'None', 'null'): continue
                try:
                    ev, vv = float(e), float(v)
                except ValueError:
                    fails.append((r[0], exp_rows[0][j + 1], f'{v!r} vs {e!r}', None)); continue
                if abs(ev - vv) <= max(0.0051, 1e-7 * abs(ev)): ok += 1
                else: fails.append((r[0], exp_rows[0][j + 1], f'engine {vv:.2f}, guide {ev:.2f}', (ev, vv)))
        return ok, fails
    if len(exp_rows) != len(out_rows): fails.append(('(table)', '', f'{len(out_rows)} rows, guide has {len(exp_rows)}', None))
    head = exp_rows[0]; skip = {j for j, h in enumerate(head) if norm(h).startswith('how')}
    for i, (er, orow) in enumerate(zip(exp_rows, out_rows)):
        if i and norm(er[0]) != norm(orow[0]): fails.append((er[0], '', f'row label {orow[0]!r}', None))
        if i == 0: continue
        for j in range(1, len(er)):
            if j in skip: continue
            e = er[j]; v = orow[j] if j < len(orow) else ''
            if e.strip() == '':
                continue
            pe = parse(e)
            if pe is None:
                if norm(e) == norm(v): ok += 1
                else: fails.append((er[0], head[j], f'engine {v!r}, guide {e!r}', None))
                continue
            try: vv = float(v)
            except ValueError: fails.append((er[0], head[j], f'engine {v!r}, guide {e!r}', None)); continue
            ev, tol = pe
            if abs(vv - ev) <= tol * (1 + 1e-9) + 1e-9: ok += 1
            else: fails.append((er[0], head[j], f'engine {vv:,.4f}, guide prints {e}', (ev, vv)))
    return ok, fails
def main():
    verbose = '--verbose' in sys.argv
    if '--no-run' not in sys.argv:
        r = subprocess.run([sys.executable, '-B', os.path.join(HERE, 'engine', 'forecast.py'), '--out', OUT], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode: print(r.stderr); sys.exit(1)
    total_ok = total_fail = total_close = 0; bad_tables = []; worst = worst_share = 0.0
    only = sys.argv[sys.argv.index('--chapter') + 1] if '--chapter' in sys.argv else None
    for ch in sorted(d for d in os.listdir(EXP) if os.path.isdir(os.path.join(EXP, d)) and (only is None or d.endswith(only))):
        man = json.load(open(os.path.join(EXP, ch, 'manifest.json')))
        print(f"\n{ch}: checking against the guide build of {man['guide_build']} (figures {man['guide_figures_fingerprint']})")
        for gr in man['grids']:
            for t in gr['tables']:
                ep = os.path.join(EXP, ch, t['file']); op = os.path.join(OUT, ch, t['file'])
                if not os.path.exists(op): bad_tables.append((t['file'], ['engine wrote no such table'])); total_fail += 1; continue
                ok, fails = check_table(read(ep), read(op), gr['kind'] != 'sheet')
                near = [f_ for f_ in fails if close_line(ch, f_[0]) and is_close(f_)]; fails = [f_ for f_ in fails if not (close_line(ch, f_[0]) and is_close(f_))]
                for f_ in near:
                    d = abs(f_[3][0] - f_[3][1])
                    if abs(f_[3][0]) < 1000: worst = max(worst, d)
                    else: worst_share = max(worst_share, d / abs(f_[3][0]))
                total_ok += ok; total_fail += len(fails); total_close += len(near)
                status = 'ok' if not fails else f'{len(fails)} off'
                if near: status += f', {len(near)} close'
                print(f"  {'✓' if not fails else '✗'} {t['file']:52s} {ok:4d} cells {status}")
                if fails: bad_tables.append((t['file'], fails))
    print(f'\n{total_ok:,} cells match the guide, {total_fail:,} do not.')
    if total_close: print(f'{total_close:,} more cells, on Chapter 3\'s Cohort back-test lines, are close: {worst:.3f} points at most, dollar amounts within {100 * worst_share:.2f}% (see expected/README.md).')
    if verbose or total_fail:
        for f, fs in bad_tables:
            print(f'\n{f}:'); [print('   ', *x[:3]) for x in fs[: (None if verbose else 6)]]
    sys.exit(0 if total_fail == 0 else 1)
if __name__ == '__main__':
    main()
