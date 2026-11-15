"""Turns account-level rows into the aggregate files the chapters read. This is the step a spreadsheet can't carry.

  accounts.csv   account_id,approval_month                       one row per account
  billing.csv    account_id,billing_month,revenue,volume         one row per account per month it billed (volume = processing volume,
                                                                 used only for Chapter 2's Seasonal volume row; leave it 0 if you don't have it)

Writes cohorts.csv, cohort_billing.csv, book_snapshots.csv and book_followon.csv next to your settings.csv.

The approval month of an account is the earlier of its approval month and its first billing month (an account that bills
before its recorded approval counts from its first statement).
"""
import os, sys
import numpy as np, pandas as pd
from .months import mi, ml

def prepare(folder, accounts_csv=None, billing_csv=None, close=None):
    accounts_csv = accounts_csv or os.path.join(folder, 'accounts.csv'); billing_csv = billing_csv or os.path.join(folder, 'billing.csv')
    if close is None:
        S = pd.read_csv(os.path.join(folder, 'settings.csv')); close = mi(S.set_index('key').loc['close', 'value'])
    A = pd.read_csv(accounts_csv, dtype={'account_id': str}); Bl = pd.read_csv(billing_csv, dtype={'account_id': str})
    Bl['s'] = Bl['billing_month'].map(mi); Bl = Bl[Bl['s'] <= close]
    A['am'] = A['approval_month'].map(mi); A = A[A['am'] <= close].reset_index(drop=True)
    idx = {a: i for i, a in enumerate(A['account_id'])}
    Bl = Bl[Bl['account_id'].isin(idx)]
    r = Bl['account_id'].map(idx).to_numpy(); s0 = int(Bl['s'].min()); W = close - s0 + 1; s = (Bl['s'] - s0).to_numpy(); n = len(A)
    PR = np.zeros((n, W), bool); REV = np.zeros((n, W)); VOL = np.zeros((n, W))
    PR[r, s] = True; np.add.at(REV, (r, s), Bl['revenue'].to_numpy(float)); np.add.at(VOL, (r, s), Bl['volume'].to_numpy(float))
    first = np.where(PR.any(1), s0 + np.argmax(PR, axis=1), 10 ** 9)
    COH = np.minimum(A['am'].to_numpy(), first)
    # cohorts and their billing
    co = pd.Series(COH).value_counts().sort_index()
    pd.DataFrame({'approval_month': [ml(c) for c in co.index], 'accounts_approved': co.values}).to_csv(os.path.join(folder, 'cohorts.csv'), index=False)
    rr, ss = np.nonzero(PR)
    cb = pd.DataFrame({'c': COH[rr], 's': ss + s0, 'rev': REV[rr, ss], 'b': REV[rr, ss] > 0}).groupby(['c', 's']).agg(accounts_billing=('b', 'sum'), revenue=('rev', 'sum')).reset_index()
    pd.DataFrame({'approval_month': cb['c'].map(ml), 'billing_month': cb['s'].map(ml), 'accounts_billing': cb['accounts_billing'], 'revenue': cb['revenue'].round(2)}).to_csv(
        os.path.join(folder, 'cohort_billing.csv'), index=False)
    book = book_snapshots(folder, REV, VOL, COH, s0, close)
    return dict(accounts=n, billing_rows=int(PR.sum()), first_billing_month=ml(s0), close=ml(close), **book)

def book_snapshots(folder, REV, VOL, COH, s0, close):
    """Chapter 2's book, as it stood at every month-end close, by approval month and billing status.

    The book at a close o: every account approved by o that billed more than zero in o, or was approved in the last three months (o - approval <= 2)
    and may not have billed yet. status: billing (billed more than zero in o) or not billing.
      book_snapshots.csv   as_of, approval_month, status, accounts, revenue, billing_accounts, volume, stay_accounts, stay_revenue
                           revenue, billing accounts and volume in o. stay_*: the billing accounts still billing twelve months later, and their revenue in o.
      book_followon.csv    for every December close: what the same groups billed in each month of the next year (revenue, billing accounts, volume)."""
    W = REV.shape[1]; snaps, fol = [], []
    for o in range(s0 + 11, close + 1):
        j = o - s0
        live = (COH <= o) & ((REV[:, j] > 0) | (o - COH <= 2))
        ix = np.nonzero(live)[0]; rv = REV[ix, j]; b = rv > 0
        st = np.where(b, 0, 1).astype(np.int8)                # 0 billing, 1 not billing
        stay = b & ((REV[ix, j + 12] > 0) if j + 12 < W else np.zeros(len(ix), bool))
        g = pd.DataFrame({'c': COH[ix], 't': st, 'rev': rv, 'b': b, 'vol': VOL[ix, j], 'stay': stay, 'srev': np.where(stay, rv, 0.0)})
        agg = g.groupby(['c', 't']).agg(accounts=('rev', 'size'), revenue=('rev', 'sum'), billing_accounts=('b', 'sum'), volume=('vol', 'sum'),
                                        stay_accounts=('stay', 'sum'), stay_revenue=('srev', 'sum')).reset_index()
        agg.insert(0, 'as_of', ml(o)); snaps.append(agg)
        if o % 12 == 11:                                   # a December: the next year's months for the same groups
            for m in range(1, 13):
                jj = j + m
                if jj >= W: break
                h = pd.DataFrame({'c': COH[ix], 't': st, 'rev': REV[ix, jj], 'b': REV[ix, jj] > 0, 'vol': VOL[ix, jj]})
                a2 = h.groupby(['c', 't']).agg(revenue=('rev', 'sum'), billing_accounts=('b', 'sum'), volume=('vol', 'sum')).reset_index()
                a2.insert(0, 'month', ml(o + m)); a2.insert(0, 'as_of', ml(o)); fol.append(a2)
    SL = ['billing', 'not billing']
    S = pd.concat(snaps); S['approval_month'] = S['c'].map(ml); S['status'] = S['t'].map(lambda t: SL[t])
    S[['as_of', 'approval_month', 'status', 'accounts', 'revenue', 'billing_accounts', 'volume', 'stay_accounts', 'stay_revenue']].round(2).to_csv(os.path.join(folder, 'book_snapshots.csv'), index=False)
    Fo = pd.concat(fol); Fo['approval_month'] = Fo['c'].map(ml); Fo['status'] = Fo['t'].map(lambda t: SL[t])
    Fo[['as_of', 'approval_month', 'status', 'month', 'revenue', 'billing_accounts', 'volume']].round(2).to_csv(os.path.join(folder, 'book_followon.csv'), index=False)
    return dict(book_closes=len(snaps), book_rows=len(S), followon_rows=len(Fo))

if __name__ == '__main__':
    print(prepare(sys.argv[1]))
