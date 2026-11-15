"""Chapter 2: Existing Book. The accounts already on the book, as a layer cake, built the way Chapter 1 builds net new. Each layer starts from the one before:
  1 Straight Line  this year's book closed out by last year's shares; next year's book comes in at this year's December plus this year's new accounts'
                   December (Chapter 1's close-out); next year's total = this year's total x (next year's book / this year's book); the months from
                   January's share of this year, every month after up by the same step, adding to the total
  2 Seasonal       Straight Line's year, filled by each month's average share of its year (every earlier year, plus this year's closed months)
  3 Cohort         every approval cohort: its December x what cohorts of the same age billed in a year against their December in earlier years;
                   the months take Seasonal's shares
Billing accounts: Straight Line runs from the start to the start x the average kept, in equal steps; Seasonal keeps it; each cohort runs the same way at
its own kept rate. The guide's fourth layer, Power Law (every cohort split by tier), isn't in this repository.
Every rate comes only from years before the year forecast. Billing = billed more than zero that month. METHOD.md, Chapter 2, walks through it.
"""
import numpy as np
from .months import NAMES, FULL, ym, year, mon, ml

STEP = np.arange(1, 13) / 12.0
LAY = ['straight', 'seasonal', 'cohort']
def co_key(a): return int(a) if a < 24 else int(min(24 + (a - 24) // 12 * 12, 120))      # by month for two years, then in years, to ten

def sl_shares(s1):
    """Chapter 1's Straight Line: January at share s1 of the year, every month after up by the same step, twelve months adding to 1."""
    d = (1 - 12 * s1) / 66; return np.array([s1 + i * d for i in range(12)])

def season_avg(RT, base):
    """Chapter 1's Seasonal: each month's average share of its year over every earlier year; a year still open joins for its closed months,
    read against the year it is on course for (its closed months / the full years' average share of them)."""
    S = RT['S']; avg = S.mean(0).copy(); part = base.get('part')
    if part is not None and 0 < len(part) < 12:
        k = len(part); part = np.asarray(part, float); est = part.sum() / avg[:k].sum(); avg[:k] = (S[:, :k].sum(0) + part / est) / (len(S) + 1)
    return avg

class ExistingBook:
    def __init__(self, book, nn):
        b = self.b = book; self.nn = nn               # nn: Chapter 1's NetNewInYear: the plan's count, and this year's new accounts
        self.IY, self.k = year(b.close), mon(b.close)
        decs = sorted(o for o in b.SNAP if mon(o) == 12)
        self.FIRSTY = year(decs[0]) + 1               # the first year with a December before it
        self.hist = {}; self._rc = {}
        for y in range(self.FIRSTY, self.IY + 1): self.hist[y] = self._hist(y)

    # ------------------------------------------------------------ what each year's book did
    def snap(self, y):
        """The book entering year y: its December y-1 groups (approval month, billing or not)."""
        return self.b.SNAP[ym(y - 1, 12)]
    def fol(self, y): return self.b.FOL.get(ym(y - 1, 12), {})
    def _hist(self, y):
        S = self.snap(y); F = self.fol(y); d = ym(y - 1, 12)
        months = sum(1 for m in range(1, 13) if ym(y, m) <= self.b.close)
        rev = np.zeros(12); acc = np.zeros(12); vol = np.zeros(12)
        for g in F.values(): rev += g['rev']; acc += g['bill']; vol += g['vol']
        h = dict(start_rev=sum(g['rev'] for g in S), start_acc=sum(g['bill'] for g in S), start_vol=sum(g['vol'] for g in S),
                 new_rev=sum(g['rev'] for g in S if g['c'] >= ym(y - 1, 1)), new_acc=sum(g['bill'] for g in S if g['c'] >= ym(y - 1, 1)),
                 rev=rev[:months], acc=acc[:months], vol=vol[:months], closed=months,
                 stay_n=sum(g['stay_n'] for g in S), stay_rev=sum(g['stay_rev'] for g in S))
        if months == 12: h['kept_rev'] = rev[11] / h['start_rev']; h['kept_acc'] = acc[11] / h['start_acc']
        return h
    def prior(self, Y): return [y for y in range(self.FIRSTY, Y) if self.hist.get(y, {}).get('closed') == 12]

    # ------------------------------------------------------------ the rates each layer reads, from the years before
    def rates(self, Y, years=None):
        P = list(years) if years is not None else self.prior(Y)
        if tuple(P) in self._rc: return self._rc[tuple(P)]
        H = self.hist; kr = float(np.mean([H[y]['kept_rev'] for y in P])); ka = float(np.mean([H[y]['kept_acc'] for y in P]))
        S = np.array([H[y]['rev'] / H[y]['rev'].sum() for y in P]); SV = np.array([H[y]['vol'] / H[y]['vol'].sum() for y in P])
        co = {}
        for y in P:
            d = ym(y - 1, 12); F = self.fol(y)
            for g in self.snap(y):
                e = F.get((g['c'], g['t']), dict(rev=np.zeros(12), bill=np.zeros(12)))
                er, eb, yr = e['rev'][11], e['bill'][11], float(np.sum(e['rev'])); age = d - g['c']
                r = co.setdefault(co_key(age), np.zeros(9))   # billing: start rev, end rev, count, end billing | not billing: count, end rev, end billing | year rev: billing, not billing
                if g['t'] < 4: r[0] += g['rev']; r[1] += er; r[2] += g['bill']; r[3] += eb; r[7] += yr
                else: r[4] += g['n']; r[5] += er; r[6] += eb; r[8] += yr
        self._rc[tuple(P)] = dict(kr=kr, ka=ka, S=S, sh=S.mean(0), shv=SV.mean(0), co=co, years=P); return self._rc[tuple(P)]

    @staticmethod
    def end_of(store, kk, s, b, n_nb, fallback):
        """A group's next December (revenue, billing accounts) at its key's kept rates, and its year at its key's ratio of year to December:
        billing accounts at the billing rates, the rest at what not-billing accounts of that key went on to bill, per account."""
        if kk == 'young': r = np.sum([v for k_, v in store.items() if k_ < 12], 0)                             # next year's new accounts, as one cohort
        else: r = store.get(kk)
        if r is None or (s > 0 and r[0] <= 0) or (n_nb > 0 and r[4] <= 0): r = fallback
        er = (s * r[1] / r[0] if s > 0 else 0.0) + (n_nb * r[5] / r[4] if n_nb > 0 else 0.0)
        ea = (b * r[3] / r[2] if b > 0 else 0.0) + (n_nb * r[6] / r[4] if n_nb > 0 else 0.0)
        yr = (s * r[7] / r[0] if s > 0 else 0.0) + (n_nb * r[8] / r[4] if n_nb > 0 else 0.0)
        return er, ea, yr

    def layer_paths(self, items, RT, base):
        """items: groups entering the year, each dict(s, b, nb, age, tier, coh). tier (a group code): 0 billing, 4 not billing, 5 planned, 6 next year's new.
        base: this year's book (year: its full year, closed out if still open; jan: its January; start: what it came in at; part: its closed months if open).
        -> each layer's monthly revenue and billing accounts, and the cohort groups behind them."""
        S0 = sum(i['s'] for i in items if i['tier'] != 4); A0 = sum(i['b'] for i in items)
        target = base['year'] * S0 / base['start']; avg = season_avg(RT, base); acc_line = A0 + STEP * (A0 * RT['ka'] - A0)
        out = {'straight': (target * sl_shares(base['jan'] / base['year']), acc_line), 'seasonal': (target * avg, acc_line.copy())}
        groups_all = {}
        for nm, store in (('cohort', RT['co']),):
            groups = {}
            for i in items:
                t = i['tier']; gk = i['coh']
                kk = 'young' if t == 6 else co_key(i['age'])
                g = groups.setdefault(gk, dict(s=0.0, b=0.0, nb=0.0, key=kk, age=i['age'], coh=i['coh'], tier=t))
                g['s'] += i['s'] if t != 4 else 0.0; g['b'] += i['b']; g['nb'] += i['nb']
            fb = np.sum(list(store.values()), 0); R = np.zeros(12); A = np.zeros(12)
            for g in groups.values():
                er, ea, yr = self.end_of(store, g['key'], g['s'], g['b'], g['nb'], fb); g['year_rev'] = yr; g['end_acc'] = ea
                g['rev'] = yr * avg; g['end_rev'] = float(g['rev'][11]); g['acc'] = g['b'] + STEP * (ea - g['b'])
                R += g['rev']; A += g['acc']
            out[nm] = (R, A); groups_all[nm] = groups
        return out, groups_all

    def start_closed(self, Y):
        """The book entering Y from its closed December: one item per (approval month, billing or not)."""
        d = ym(Y - 1, 12)
        return [dict(s=g['rev'], b=g['bill'], nb=(g['n'] if g['t'] == 4 else 0.0), age=d - g['c'], tier=g['t'], coh=g['c'], rev_all=g['rev']) for g in self.snap(Y)]

    def base_closed(self, Y):
        """This year's book when its year has closed: the book entering Y-1, its year, its January and what it came in at."""
        h = self.hist[Y - 1]; return dict(year=float(h['rev'].sum()), jan=float(h['rev'][0]), start=float(h['start_rev']), part=None)

    def base_open(self, y, k):
        """This year's book (entering y) closed out at month k, Chapter 1's way: its months closed / last year's book's share of those months = its year;
        the months still open take last year's shares. Its billing accounts in December: month k's x last year's book's December over month k."""
        PY = self.hist[y - 1]['rev']; part = np.asarray(self.hist[y]['rev'][:k], float); sh = PY / PY.sum()
        yr = part.sum() / sh[:k].sum(); months = np.concatenate([part, yr * sh[k:]])
        PA = self.hist[y - 1]['acc']; ak = float(self.hist[y]['acc'][k - 1]); acc_dec = ak * PA[11] / PA[k - 1]
        return dict(year=float(yr), jan=float(part[0]), start=float(self.hist[y]['start_rev']), start_acc=float(self.hist[y]['start_acc']), part=part, months=months,
                    dec=float(months[11]), acc_dec=float(acc_dec), acc_k=ak, py_acc_ratio=float(PA[11] / PA[k - 1]), open_share=float(sh[k:].sum()), closed=float(part.sum()), k=k)

    def nn_open(self, y, k):
        """This year's new accounts (approved in y) closed out at month k, Chapter 1's Straight Line: their months closed / last year's share of those
        months; December at last year's December share. Billing in December: Chapter 1's count (its months closed / last year's share, rounded) x the
        share of last year's new accounts billing in December."""
        b = self.b; PY = self.nn.nn_row(y - 1); part = self.nn.nn_row(y, k); yr = part.sum() / (PY[:k].sum() / PY.sum()); dec = yr * PY[11] / PY.sum()
        pc = self.nn.acc_row(y - 1); cnt = float(round(self.nn.acc_row(y, k).sum() / (pc[:k].sum() / pc.sum())))
        billing = sum(b.ab(c, ym(y - 1, 12)) for c in range(ym(y - 1, 1), ym(y - 1, 12) + 1)); bill = float(billing / pc.sum())
        return dict(year=float(yr), dec=float(dec), closed=float(part.sum()), count=cnt, bill_share=bill, acc_dec=float(cnt * bill),
                    py_dec=float(PY[11]), py_year=float(PY.sum()), py_count=float(pc.sum()), py_billing=float(billing))

    def plan_start(self, Y, k, goal=None, dec_override=None):
        """The book entering Y as seen at month k of Y-1. One start for every layer, Chapter 1's close-out.
        Every group's December is read part by part from month k (month k x last year's December over month k for the same cohorts; the plan's count,
        at what last year's cohort of the same month billed in December per approved account, for the months still to come), then each part is scaled
        to Chapter 1's numbers: the accounts already on the book to this year's book's December closed out by last year's shares (base_open), and this
        year's new accounts to Chapter 1's December for them (nn_open). Billing accounts the same way.
        dec_override: {month: December revenue} for the months still to be approved, in place of the plan's count (Chapter 3's latest cohorts' pace);
        the count is that revenue over last year's December revenue per account, and the new accounts are then left as read."""
        b = self.b; y0 = Y - 1; o, d = ym(y0, k), ym(y0, 12); o1, d1 = ym(y0 - 1, k), ym(y0 - 1, 12)
        cs = lambda lo, hi: [c for c in range(lo, hi + 1)]
        old1 = cs(b.c0, ym(y0 - 1, 1) - 1); new1 = cs(ym(y0 - 1, 1), o1)
        rr = lambda C, s: sum(b.cr(c, s) for c in C); aa = lambda C, s: sum(b.ab(c, s) for c in C)
        r_old, a_old = rr(old1, d1) / rr(old1, o1), aa(old1, d1) / aa(old1, o1)
        r_new = rr(new1, d1) / rr(new1, o1) if rr(new1, o1) > 0 else 0.0; a_new = aa(new1, d1) / aa(new1, o1) if aa(new1, o1) > 0 else 0.0
        planY = self.nn.plan_accounts(y0, goal); BO = self.base_open(y0, k); NN = self.nn_open(y0, k)
        old_items, new_items = [], []
        for g in b.SNAP[o]:
            new = g['c'] >= ym(y0, 1); r, a = (r_new, a_new) if new else (r_old, a_old)
            (new_items if new else old_items).append(dict(s=g['rev'] * r, b=g['bill'] * a, nb=(g['n'] if g['t'] == 4 else 0.0), age=d - g['c'], tier=g['t'], coh=g['c']))
        read_old = sum(i['s'] for i in old_items if i['tier'] != 4); read_old_acc = sum(i['b'] for i in old_items)
        for i in old_items: i['s'] *= BO['dec'] / read_old; i['b'] *= BO['acc_dec'] / read_old_acc
        sofar = sum(i['s'] for i in new_items if i['tier'] != 4); rows = []
        for m in range(k + 1, 13):
            n = planY[m - 1]; c1 = ym(y0 - 1, m); n1 = b.n(c1)
            sr = b.cr(c1, d1) / n1; sb = b.ab(c1, d1) / n1
            if dec_override is not None: n = float(dec_override.get(m, 0.0)) / sr if sr > 0 else 0.0
            rows.append([m, float(n), sr, sb])
        if dec_override is None:                                           # the months still to come make up the rest of Chapter 1's December
            tc = NN['dec'] - sofar; pl_rev = sum(n * sr for _, n, sr, _ in rows)
            if tc > 0 and pl_rev > 0: rows = [[m, n * tc / pl_rev, sr, sb] for m, n, sr, sb in rows]
            else:
                rows = [[m, 0.0, sr, sb] for m, n, sr, sb in rows]
                for i in new_items: i['s'] *= (NN['dec'] / sofar if sofar > 0 else 1.0)
        planned = []
        for m, n, sr, sb in rows:
            c_ = ym(y0, m); new_items.append(dict(s=n * sr, b=n * sb, nb=(n if n * sr == 0 else 0.0), age=d - c_, tier=5, coh=c_))
            planned.append(dict(month=NAMES[m - 1], count=float(n), dec_rev=float(n * sr), dec_acc=float(n * sb)))
        if dec_override is None:
            an = sum(i['b'] for i in new_items)
            if an > 0:
                for i in new_items: i['b'] *= NN['acc_dec'] / an
                for p_ in planned: p_['dec_acc'] *= NN['acc_dec'] / an
        part = dict(old=dict(oct_rev=rr(cs(b.c0, ym(y0, 1) - 1), o), oct_acc=aa(cs(b.c0, ym(y0, 1) - 1), o), ratio_rev=r_old, ratio_acc=a_old, read_rev=read_old, read_acc=read_old_acc,
                             dec_rev=sum(i['s'] for i in old_items if i['tier'] != 4), dec_acc=sum(i['b'] for i in old_items)),
                    new=dict(oct_rev=rr(cs(ym(y0, 1), o), o), oct_acc=aa(cs(ym(y0, 1), o), o), ratio_rev=r_new, ratio_acc=a_new, sofar_rev=sofar,
                             dec_rev=sum(i['s'] for i in new_items if i['tier'] != 4), dec_acc=sum(i['b'] for i in new_items), planned=planned), base=BO, nn=NN)
        return old_items + new_items, part

    def year_actual(self, Y, k):
        F = self.fol(Y); R = np.zeros(k); A = np.zeros(k)
        for g in F.values(): R += g['rev'][:k]; A += g['bill'][:k]
        return R, A

    def reforecast(self, paths, groups, Y, k, RT):
        """At month k of Y: the months closed are what billed. Straight Line and Seasonal (Chapter 1's way): the year = the months closed / last year's
        book's share of them; what's left goes on the months still open, on the straight line from January's share (Straight Line) or by each month's
        average share of the year (Seasonal); billing accounts carry on down the line from the latest month. Cohort: each cohort's open months =
        its path, rescaled by its own months closed against its path."""
        F = self.fol(Y); act_r, act_a = self.year_actual(Y, k); res = {}
        PYr = self.hist[Y - 1]['rev']; est = act_r.sum() / (PYr[:k].sum() / PYr.sum()); rest = est - act_r.sum()
        for nm in ('straight', 'seasonal'):
            pr, pa = paths[nm]; w = sl_shares(act_r[0] / est) if nm == 'straight' else RT['sh']; fa = act_a[-1] / pa[k - 1]
            res[nm] = (np.concatenate([act_r, rest * w[k:] / w[k:].sum()]), np.concatenate([act_a, pa[k:] * fa]))
        for nm in ('cohort',):
            open_r = np.zeros(12 - k); open_a = np.zeros(12 - k)
            for gk, g in groups[nm].items():
                fg = [v for (c, t), v in F.items() if c == gk]
                ar = sum((v['rev'][:k] for v in fg), np.zeros(k)); ab = sum((v['bill'][:k] for v in fg), np.zeros(k))
                f = ar.sum() / g['rev'][:k].sum() if g['rev'][:k].sum() > 0 else 1.0; fa = ab[-1] / g['acc'][k - 1] if g['acc'][k - 1] > 0 else 1.0
                open_r += g['rev'][k:] * f; open_a += g['acc'][k:] * fa
            res[nm] = (np.concatenate([act_r, open_r]), np.concatenate([act_a, open_a]))
        return res

    def legacy_at(self, o, new_dec, goal=None, H=24, dec_override=None):
        """The existing book forecast at close o, every layer, for months ahead 1..H (Chapter 3).
        Year of the close: each layer's path from the December before, made again at the close (the Reforecast). The next year: from December,
        estimated at the close (plan_start: this year's book closed out plus this year's new accounts), or as closed if the close is a December. Two
        years out: each layer's own December a year on, with that year's new accounts (new_dec[layer]: the same method's net new forecast for that
        December) joining in January; its year is the year before's x (that start / the year before's start), as in Straight Line.
        Rates only from years closed by the close."""
        Y, k = year(o), mon(o); res = {nm: np.full(H, np.nan) for nm in LAY}
        yrs_ok = [y for y in range(self.FIRSTY, Y + (1 if k == 12 else 0)) if ym(y, 12) <= o]
        def put(nm, y, vals):
            for m, v in zip(range(1, 13), vals):
                i = ym(y, m) - o - 1
                if 0 <= i < H: res[nm][i] = v
        if k < 12:
            RT = self.rates(Y, [y for y in yrs_ok if y < Y]); pY, gY = self.layer_paths(self.start_closed(Y), RT, self.base_closed(Y)); rf = self.reforecast(pY, gY, Y, k, RT)
            for nm in LAY: put(nm, Y, rf[nm][0])
            st, _ = self.plan_start(Y + 1, k, goal, dec_override); b1 = self.base_open(Y, k)
        else:
            st = self.start_closed(Y + 1); b1 = self.base_closed(Y + 1)
        RT1 = self.rates(Y + 1, yrs_ok); p1, g1 = self.layer_paths(st, RT1, b1)
        for nm in LAY: put(nm, Y + 1, p1[nm][0])
        if ym(Y + 2, 1) - o - 1 < H:
            S1 = sum(i['s'] for i in st if i['tier'] != 4)
            for nm in LAY:
                if nm in ('straight', 'seasonal'):
                    S0 = p1[nm][0][11] + new_dec[nm]
                    p2, _ = self.layer_paths([dict(s=S0, b=1.0, nb=0.0, age=24, tier=0, coh=0)], RT1,
                                             dict(year=float(p1[nm][0].sum()), jan=float(p1[nm][0][0]), start=S1, part=None)); put(nm, Y + 2, p2[nm][0])
                else:
                    items = []
                    for g in g1[nm].values():
                        s_ = g['rev'][11]; b_ = 1.0 if g['rev'][11] > 0 else 0.0; t_ = g['tier'] if g['tier'] < 4 else 5
                        if t_ == 5: items.append(dict(s=s_, b=b_, nb=(1.0 if s_ == 0 else 0.0), age=g['age'] + 12, tier=5, coh=g['coh']))
                        elif b_ > 0: items.append(dict(s=s_, b=b_, nb=0.0, age=g['age'] + 12, tier=t_, coh=g['coh']))
                        else: items.append(dict(s=0.0, b=0.0, nb=1.0, age=g['age'] + 12, tier=t_, coh=g['coh']))
                    items.append(dict(s=new_dec[nm], b=1.0, nb=0.0, age=6, tier=6, coh=ym(Y + 1, 7)))
                    p2, _ = self.layer_paths(items, RT1, dict(year=1.0, jan=1 / 12, start=1.0, part=None)); put(nm, Y + 2, p2[nm][0])
        return res

    # ------------------------------------------------------------ the guide's tables
    def results(self):
        """Everything the chapter shows, computed once."""
        if hasattr(self, '_res'): return self._res
        IY = self.IY; NY = IY + 1; K = self.b.plan_month; out = {}
        out['check'] = {}
        for Y in range(self.FIRSTY + 1, IY + 1):
            RT = self.rates(Y); paths, _ = self.layer_paths(self.start_closed(Y), RT, self.base_closed(Y)); h = self.hist[Y]; kk = h['closed']; act = h['rev'][:kk]
            out['check'][Y] = {nm: dict(months=paths[nm][0], miss=float(paths[nm][0][:kk].sum() / act.sum() - 1), mape=float(np.mean(np.abs(paths[nm][0][:kk] / act - 1)))) for nm in LAY}
        RT6 = self.rates(IY); p6, g6 = self.layer_paths(self.start_closed(IY), RT6, self.base_closed(IY))
        out['reforecast'] = {kk: self.reforecast(p6, g6, IY, kk, RT6) for kk, _ in self.nn.checks()}
        RT7 = self.rates(NY); st7, part7 = self.plan_start(NY, self.k); b7 = self.base_open(IY, self.k); p7, g7 = self.layer_paths(st7, RT7, b7)
        S07 = sum(i['s'] for i in st7 if i['tier'] != 4)
        out['ny'] = dict(RT=RT7, items=st7, part=part7, base=b7, paths=p7, groups=g7, start_rev=S07, start_acc=sum(i['b'] for i in st7),
                         target=b7['year'] * S07 / b7['start'], growth=S07 / b7['start'] - 1, avg=season_avg(RT7, b7))
        RT6p = self.rates(IY, [y for y in self.prior(IY) if y < IY - 1]); st6p, _ = self.plan_start(IY, K); p6p, _ = self.layer_paths(st6p, RT6p, self.base_open(IY - 1, K)); a6 = self.hist[IY]['rev']
        out['iy_planned'] = {nm: float(p6p[nm][0][:len(a6)].sum() / a6.sum() - 1) for nm in LAY}
        self._res = out; return out

    def grids(self):
        from .grids import Grid
        R = self.results(); IY = self.IY; NY = IY + 1; H = self.hist; P = R['ny']; RT = P['RT']; L = P['paths']; BO = P['base']; NN = P['part']['nn']; k = self.k
        G = []; M13 = [''] + NAMES + ['Year']
        done = [y for y in sorted(H) if 'kept_rev' in H[y]]
        # Step 1: every year the book came in; this year's next December is Step 2's forecast
        g = Grid('2-1-straight-line_step-1__t1', 'Every year the book came in', ['Entering', 'December revenue', 'Of it, last year’s new accounts', 'Billing accounts', 'Of them, last year’s new',
                 'Next December’s revenue', 'Revenue kept', 'Next December’s billing accounts', 'Accounts kept'])
        for y in sorted(H):
            h = H[y]; dn = 'kept_rev' in h; fc = (y == IY)
            nd = h['rev'][11] if dn else (BO['dec'] if fc else None); nk = h['kept_rev'] * 100 if dn else (BO['dec'] / h['start_rev'] * 100 if fc else None)
            na = h['acc'][11] if dn else (BO['acc_dec'] if fc else None); nka = h['kept_acc'] * 100 if dn else (BO['acc_dec'] / h['start_acc'] * 100 if fc else None)
            g.add(str(y), [h['start_rev'], h['new_rev'], h['start_acc'], h['new_acc'], nd, nk, na, nka])
        g.add(f'Average, {done[0]} to {done[-1]}', [None] * 5 + [RT['kr'] * 100, None, RT['ka'] * 100]); G.append(g)
        # Step 2: Chapter 1's Step 1 on the book you carry in
        PYb, PYa = H[IY - 1]['rev'], H[IY - 1]['acc']; IYm = BO['months']; IYa = list(H[IY]['acc'][:k]) + [BO['acc_k'] * PYa[m] / PYa[k - 1] for m in range(k, 12)]
        NYm, NYa = L['straight']; s1 = BO['jan'] / BO['year']
        g = Grid('2-1-straight-line_step-2__t1', 'Close out this year, add the new accounts, draw the line: revenue', M13)
        g.add('PY (last year)', list(PYb) + [PYb.sum()]).add('+ Last year’s new', [None] * 11 + [H[IY]['new_rev'], None])
        g.add('IY (this year)', list(IYm) + [BO['year']]).add('January as a share of IY', [s1 * 100] + [None] * 12)
        g.add('+ This year’s new', [None] * 11 + [NN['dec'], None]).add('NY (next year)', list(NYm) + [P['target']]); G.append(g)
        g = Grid('2-1-straight-line_step-2__t2', 'Close out this year, add the new accounts, draw the line: billing accounts', [''] + NAMES)
        g.add('PY (last year)', list(PYa)).add('+ Last year’s new', [None] * 11 + [H[IY]['new_acc']]).add('IY (this year)', IYa)
        g.add('+ This year’s new', [None] * 11 + [NN['acc_dec']]).add('NY (next year)', list(NYa)); G.append(g)
        g = Grid('2-1-straight-line_step-2__t3', 'Close out this year, add the new accounts, draw the line: the math', ['', 'Value', 'How it is worked out'])
        for lab, v, how in (('PY, December', PYb[11], 'the PY row’s December'), ('Last year’s new accounts, December', H[IY]['new_rev'], 'Chapter 1: PY’s December'),
                            ('IY’s book came in at', H[IY]['start_rev'], '= PY December + last year’s new accounts'), (f'IY, January to {FULL[k - 1]} (closed)', BO['closed'], 'the closed IY cells, added up'),
                            (f'{" and ".join(FULL[m] for m in range(k, 12))} as a share of PY', BO['open_share'] * 100, 'PY: the open months ÷ the year'),
                            ('IY, the full year', BO['year'], '= closed ÷ (1 − that share)'), ('IY, December', BO['dec'], '= the full year × PY’s December share'),
                            ('This year’s new accounts, December', NN['dec'], 'Chapter 1: IY’s December'), ('NY’s book comes in at', P['start_rev'], '= IY December + this year’s new accounts'),
                            ('Bigger than IY’s book', P['growth'] * 100, '= NY’s book ÷ IY’s book − 1 (where Chapter 1 has the goal)'), ('Target, next year', P['target'], '= the full year × (1 + that)'),
                            ('January as a share of IY', s1 * 100, 'IY January ÷ IY, the full year'), ('NY January', NYm[0], '= the target × that share'),
                            ('Each month after', NYm[1] - NYm[0], '= (the target − 12 × NY January) ÷ 66'), ('NY December', NYm[11], '= NY January + 11 steps'),
                            ('IY billing accounts, December', BO['acc_dec'], f'= {FULL[k - 1]}’s count × PY’s December ÷ {FULL[k - 1]}'),
                            ('This year’s new accounts billing in December', NN['acc_dec'], '= Chapter 1’s count × the share of last year’s new accounts billing in December'),
                            ('NY’s book comes in with', P['start_acc'], '= IY December + this year’s new accounts'), ('NY December, billing accounts', NYa[11], '= that × the average kept, one equal step a month')):
            g.add(lab, [v, how])
        G.append(g)
        # Step 2's chart: every year as billed, and each year's Straight Line (next year's from this year closed out)
        yrs = list(range(self.FIRSTY, NY + 1)); xs = [f'{NAMES[m - 1]} {y}' for y in yrs for m in range(1, 13)]
        act = []; sl = []
        for y in yrs:
            h = H.get(y); act += (list(h['rev']) + [None] * (12 - len(h['rev']))) if h else [None] * 12
            sl += list(L['straight'][0]) if y == NY else (list(R['check'][y]['straight']['months']) if y in R['check'] else [None] * 12)
        g = Grid('2-1-straight-line_step-1-chart__v1c1', 'Every year’s book, and its Straight Line', ['series'] + xs)
        g.add('What billed', act).add('Straight Line', sl); G.append(g)
        def chart(name, title, rev, acc):
            c = Grid(name, title, ['series'] + NAMES); c.add('Revenue', rev).add('Billing accounts', acc); return c
        G.append(chart('2-1-straight-line_next-year__v1c1', 'Straight Line, next year', *L['straight']))
        for vi, (kk, lab) in enumerate(self.nn.checks(), 1):
            for nm, pre in (('straight', '2-1-straight-line'), ('seasonal', '2-2-seasonal'), ('cohort', '2-3-cohort')):
                G.append(chart(f'{pre}_reforecast__v{vi}c1', lab, *R['reforecast'][kk][nm]))
        # Seasonal: each month's share of its year (this year joining for its closed months), then Straight Line's year filled by the average share
        S = RT['S']; full = S.mean(0); part = BO['part']; est = part.sum() / full[:k].sum()
        g = Grid('2-2-seasonal_step-1__t1', 'Each month’s share of its year', M13)
        for y, row in zip(RT['years'], S): g.add(str(y), list(row * 100) + [H[y]['rev'].sum()])
        g.add(str(IY), list(part / est * 100) + [None] * (12 - k) + [est])
        g.add('Average', list(P['avg'] * 100) + [None]).add('Processing volume, average', list(RT['shv'] * 100) + [None]); G.append(g)
        g = Grid('2-2-seasonal_step-2__t1', 'Fill Straight Line’s year by the time of year', M13)
        g.add('Straight Line', list(L['straight'][0]) + [L['straight'][0].sum()]).add('Average share of the year', list(P['avg'] * 100) + [100.0])
        g.add('Seasonal', list(L['seasonal'][0]) + [L['seasonal'][0].sum()]); G.append(g)
        G.append(chart('2-2-seasonal_next-year__v1c1', 'Seasonal, next year', *L['seasonal']))
        # Cohort: every approval year's line, the two youngest years opened into months
        rows = {}
        for gk, gr in P['groups']['cohort'].items():
            yv = year(gr['coh']); rk = str(yv) if yv >= NY - 9 else f'{NY - 10} and earlier'; mk = f"{NAMES[mon(gr['coh']) - 1]} {yv}"
            for key in ((rk, None), (rk, mk)):
                r = rows.setdefault(key, dict(s=0.0, b=0.0, nb=0.0, end_acc=0.0, rev=np.zeros(12)))
                for f_ in ('s', 'b', 'nb', 'end_acc'): r[f_] += gr[f_]
                r['rev'] = r['rev'] + gr['rev']
        crow = lambda r: [r['s'], r['b'], (f"{r['rev'].sum() / r['s']:.2f}×" if r['s'] else None), r['rev'].sum(), r['end_acc']]
        top = sorted([k_ for k_ in rows if k_[1] is None], key=lambda k_: (not k_[0].endswith('earlier'), k_[0]))
        CC = ['Approved', 'December revenue', 'Billing accounts', 'Year against December', 'Next year', 'Next December’s billing accounts']
        tot = ['All cohorts', [None] * 3 + [L['cohort'][0].sum(), None]]
        g = Grid('2-3-cohort_step-1__t1', 'Every cohort on its own line, by approval year', CC)
        for k_ in top: g.add(k_[0], crow(rows[k_]))
        g.add(*tot); G.append(g)
        g = Grid('2-3-cohort_step-1__t2', 'Every cohort on its own line, by approval month', CC)
        for k_ in top:
            if k_[0] in (str(IY - 1), str(IY)):
                for sk in sorted([x for x in rows if x[0] == k_[0] and x[1]], key=lambda x: NAMES.index(x[1][:3])): g.add(sk[1], crow(rows[sk]))
            else: g.add(k_[0], crow(rows[k_]))
        g.add(*tot); G.append(g)
        G.append(chart('2-3-cohort_next-year__v1c1', 'Cohort, next year', *L['cohort']))
        TT = {'straight': 'Straight Line', 'seasonal': 'Seasonal', 'cohort': 'Cohort'}
        g = Grid('2-5-three-layers__t1', 'The existing book next year, three layers', M13)
        for nm in LAY: g.add(TT[nm], list(L[nm][0]) + [L[nm][0].sum()])
        G.append(g)
        ckY = sorted(R['check'])
        g = Grid('2-5-three-layers_check__t1', 'Each layer against what billed, every year so far', [''] + [str(y) if H[y]['closed'] == 12 else f'{y}, Jan to {NAMES[H[y]["closed"] - 1]}' for y in ckY] + ['Typical month off'])
        for nm in LAY: g.add(TT[nm], [R['check'][y][nm]['miss'] * 100 for y in ckY] + [np.mean([R['check'][y][nm]['mape'] for y in ckY]) * 100])
        G.append(g)
        g = Grid('2-5-three-layers_this-year-at-each-close__t1', f'The existing book in {IY}, as it stood at each close', [''] + [lab for _, lab in self.nn.checks()])
        for nm in LAY: g.add(TT[nm], [R['reforecast'][kk][nm][0].sum() for kk, _ in self.nn.checks()])
        G.append(g)
        for vi, nm in enumerate(LAY, 1): G.append(chart(f'2-0-existing-book_chart__v{vi}c1', TT[nm], *L[nm]))
        return G
