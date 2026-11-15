"""Loads a book's aggregate files (the shape data/sample/ and templates/ use) into arrays the chapters read.

Files (CSV, one header row):
  settings.csv          key,value      close (YYYY-MM, the last month-end close), goal (0.10 = 10%), and the plan settings
  plan_inputs.csv       month,investment,leads                                  every month you have (Chapter 1 reads PY and IY)
  cohorts.csv           approval_month,accounts_approved                        one row per approval month
  cohort_billing.csv    approval_month,billing_month,accounts_billing,revenue  one row per approval month per billing month
  book_snapshots.csv    as_of,approval_month,status,accounts,revenue,billing_accounts,volume,stay_accounts,stay_revenue   Chapter 2's book at every close
                        status = billing or not billing (in the book, approved in the last three months, not billing yet)
  book_followon.csv     as_of,approval_month,status,month,revenue,billing_accounts,volume   each December's book, in each month of the next year
Nothing after `close` is read, even if it is in the files.
"""
import csv, os
import numpy as np
from .months import mi

def _status(r):
    """0 billing, 4 not billing (4 is the code the chapters use for an account in the book that isn't billing yet)."""
    v = (r.get('status') or '').strip().lower()
    return 4 if v in ('not billing', 'not_billing', 'n') else 0

def _rows(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

class Book:
    def __init__(self, folder):
        self.folder = folder
        S = {r['key'].strip(): r['value'].strip() for r in _rows(os.path.join(folder, 'settings.csv'))}
        self.settings = S
        self.close = mi(S['close'])
        self.goal = float(S.get('goal', 0.10))
        self.cvr_change = float(S.get('plan_cvr_change', 0.10))        # Plan 2: CVR 10% better
        self.cpl_change = float(S.get('plan_cost_per_lead_change', -0.10))  # Plans 3 and 4: cost per lead 10% lower
        self.phase_in = float(S.get('weighted_phase_in', 0.10))        # Weighted: 10% under the plan's rate in January, 10% over in December
        self.plan_month = int(S.get('plan_month', 10))                 # the close each year's plan is made at: the guide plans at the October close
        # cohorts and their billing
        cb = [r for r in _rows(os.path.join(folder, 'cohort_billing.csv')) if mi(r['billing_month']) <= self.close and mi(r['approval_month']) <= self.close]
        co = [r for r in _rows(os.path.join(folder, 'cohorts.csv')) if mi(r['approval_month']) <= self.close]
        self.c0 = min(mi(r['approval_month']) for r in co)
        self.s0 = min(mi(r['billing_month']) for r in cb)            # first billing month on the book
        nc = self.close - self.c0 + 1; ns = self.close - self.s0 + 1
        self.Nc = np.zeros(nc); self.CRa = np.zeros((nc, ns)); self.ABa = np.zeros((nc, ns))
        for r in co: self.Nc[mi(r['approval_month']) - self.c0] += float(r['accounts_approved'])
        for r in cb:
            c, s = mi(r['approval_month']) - self.c0, mi(r['billing_month']) - self.s0
            self.CRa[c, s] += float(r['revenue']); self.ABa[c, s] += float(r['accounts_billing'])
        # plan inputs (illustrative in the sample)
        self.inv = {}; self.leads = {}
        p = os.path.join(folder, 'plan_inputs.csv')
        if os.path.exists(p):
            for r in _rows(p):
                s = mi(r['month'])
                if s <= self.close: self.inv[s] = float(r['investment']); self.leads[s] = float(r['leads'])

        # Chapter 2: the book at every close, by approval month and billing status, and each December's book through the next year
        self.SNAP = {}; self.FOL = {}
        p = os.path.join(folder, 'book_snapshots.csv')
        if os.path.exists(p):
            for r in _rows(p):
                o = mi(r['as_of'])
                if o > self.close: continue
                self.SNAP.setdefault(o, []).append(dict(c=mi(r['approval_month']), t=_status(r), n=float(r['accounts']), rev=float(r['revenue']),
                                                       bill=float(r['billing_accounts']), vol=float(r['volume']), stay_n=float(r['stay_accounts']), stay_rev=float(r['stay_revenue'])))
            for r in _rows(os.path.join(folder, 'book_followon.csv')):
                o, m = mi(r['as_of']), mi(r['month'])
                if m > self.close: continue
                g = self.FOL.setdefault(o, {}).setdefault((mi(r['approval_month']), _status(r)), dict(rev=np.zeros(12), bill=np.zeros(12), vol=np.zeros(12)))
                g['rev'][m - o - 1] += float(r['revenue']); g['bill'][m - o - 1] += float(r['billing_accounts']); g['vol'][m - o - 1] += float(r['volume'])

    # ---- the two numbers everything is built from
    def n(self, c):
        """Accounts approved in month c."""
        i = c - self.c0
        return float(self.Nc[i]) if 0 <= i < len(self.Nc) else 0.0
    def cr(self, c, s):
        """Revenue billed in month s by the accounts approved in month c (0 before the book starts or after the close)."""
        i, j = c - self.c0, s - self.s0
        if i < 0 or j < 0 or i >= self.CRa.shape[0] or j >= self.CRa.shape[1]: return 0.0
        return float(self.CRa[i, j])
    def ab(self, c, s):
        """Accounts billing in month s, of those approved in month c."""
        i, j = c - self.c0, s - self.s0
        if i < 0 or j < 0 or i >= self.ABa.shape[0] or j >= self.ABa.shape[1]: return 0.0
        return float(self.ABa[i, j])
