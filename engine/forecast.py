"""Run the guide's forecasts on a book.

  python3 engine/forecast.py                       the sample book (data/sample) into outputs/
  python3 engine/forecast.py --data mybook --out myoutputs
  python3 engine/forecast.py --data mybook --out mybook/outputs --prepare   first turn mybook/accounts.csv and billing.csv into the aggregate files

Every table the guide shows is written as one CSV, named after its chapter, section and step (see METHOD.md).
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plf.book import Book
from plf.chapter1 import NetNewInYear
from plf.chapter2 import ExistingBook
from plf.chapter3 import BackTest

def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default=os.path.join(here, 'data', 'sample')); ap.add_argument('--out', default=os.path.join(here, 'outputs'))
    ap.add_argument('--prepare', action='store_true', help='build the aggregate files from accounts.csv and billing.csv first')
    a = ap.parse_args()
    if a.prepare:
        from plf.prepare import prepare; print('prepare:', prepare(a.data))
    t0 = time.time(); b = Book(a.data); ch1 = NetNewInYear(b); grids = ch1.all_grids()
    out = os.path.join(a.out, 'chapter-1')
    for g in grids: g.write(out)
    print(f'Chapter 1: {len(grids)} tables written to {out} ({time.time() - t0:.1f}s)')
    if b.SNAP:
        t0 = time.time(); ch2 = ExistingBook(b, ch1); g2 = ch2.grids(); out2 = os.path.join(a.out, 'chapter-2')
        for g in g2: g.write(out2)
        print(f'Chapter 2: {len(g2)} tables written to {out2} ({time.time() - t0:.1f}s)')
        t0 = time.time(); bt = BackTest(b, ch1, ch2); R1 = ch1.straight_line_numbers(); Q = ch1.seasonal_shares()
        co = ch1.cohort_forecast(ch1.NY, b.close)[0].sum(0); three = dict(straight=R1['target'] * R1['w'], seasonal=R1['target'] * Q['avg'], cohort=co)
        g3 = bt.grids(three, ch2); out3 = os.path.join(a.out, 'chapter-3')
        for g in g3: g.write(out3)
        print(f'Chapter 3: {len(g3)} tables written to {out3} ({time.time() - t0:.1f}s)')

if __name__ == '__main__':
    main()
