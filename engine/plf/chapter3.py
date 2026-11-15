"""Chapter 3: Back Testing. The whole book three ways (Chapter 1's net new plus Chapter 2's existing book), then every method made again at every past
close with only what had closed by then, set against what the whole book billed, out to 24 months.

Four methods (the guide's fifth, Power Law, isn't in this repository):
  straight / seasonal   net new: Chapter 1's Straight Line or Seasonal at the close (this year's rest, then next year); existing book: Chapter 2's layer
  cohort                net new: this year's accounts approved by the close grow from their own month at the close on the path the 24 cohorts above
                        them followed from the same age; accounts not approved yet come in at the plan's count x dollars per account by age (the last
                        24 approval months, each at its own age); both with the whole book's time of year. Existing book: Chapter 2's Cohort layer, two years out
  trend                 a straight line through the whole book's last twelve monthly totals, carried forward
plus cohort_pace: Cohort with every account approved after the close at the latest cohorts' pace (what the last 24 approval months billed at each
age, in dollars) instead of the plan's count: the target year's own new accounts, and the ones that join the existing book (this year's months
still to come, and next year's new accounts two years out). The guide runs this test on Power Law; here it runs on Cohort.
Chapter 3's '2026 so far' tables reforecast this year with Chapter 1's own builds.
"""
import numpy as np
from .grids import Grid
from .months import NAMES, FULL, ym, year, mon, ml
from .chapter1 import sl_shares
from .chapter2 import LAY

HZ = 24; MIN_CLOSES = 12
NAME = {'straight': 'Straight Line', 'seasonal': 'Seasonal', 'cohort': 'Cohort', 'trend': 'Trend line', 'cohort_pace': 'Latest cohorts’ pace'}

class BackTest:
    def __init__(self, book, nn, eb):
        self.b, self.nn, self.eb = book, nn, eb
        b = book; self.first_close = b.s0 + 23                  # 24 months of statements behind the first close
        self.T = {s: sum(b.cr(c, s) for c in range(b.c0, s + 1)) for s in range(b.s0, b.close + 1)}
        self._rows = None; self._bi = {}; self._c = {}

    def act_new(self, s): return sum(self.b.cr(c, s) for c in range(ym(year(s), 1), s + 1))

    # ------------------------------------------------------------ each method's net new at a close, months ahead 1..HZ
    def avg_shares(self, y, k):
        nn = self.nn; yrs = list(range(nn.first_year, y)); S = np.array([nn.nn_row(v) / nn.nn_row(v).sum() for v in yrs]); full = S.mean(0)
        if k == 0: return full
        cur = nn.nn_row(y, k); est = cur.sum() / full[:k].sum(); sh = full.copy(); sh[:k] = (S[:, :k].sum(0) + cur / est) / (len(yrs) + 1)
        return sh / sh.sum()
    def napkin_nniy(self, o, how, goal=None):
        """Straight Line or Seasonal net new at the close: this year's open months, then next year (reaches December of next year)."""
        nn = self.nn; g = nn.g if goal is None else goal; Y, k = year(o), mon(o)
        cur = nn.nn_row(Y, k); prev = nn.nn_row(Y - 1); est = cur.sum() / (prev[:k].sum() / prev.sum()); rest = est - cur.sum(); nxt_total = est * (1 + g)
        if how == 'straight':
            w = sl_shares(cur[0] / est); this = rest * w[k:] / w[k:].sum() if k < 12 else np.zeros(0); nxt = nxt_total * w
        else:
            w = self.avg_shares(Y, 0); this = rest * w[k:] / w[k:].sum() if k < 12 else np.zeros(0)
            nxt = nxt_total * (self.avg_shares(Y, k) if k < 12 else self.avg_shares(Y + 1, 0))
        out = np.full(HZ, np.nan); v = np.concatenate([this, nxt]); out[:min(HZ, len(v))] = v[:HZ]; return out
    # ------------------------------------------------------------ Cohort net new: the back test's reads
    def book_index(self, o):
        """The whole book's time of year at the close: each month over its 12-month centered average (six months before it to five after),
        averaged by calendar month and scaled to average 1.00. A calendar month with no reading yet stays at 1.00."""
        if o in self._bi: return self._bi[o]
        ss = list(range(self.b.s0, o + 1)); v = np.array([self.T[s] for s in ss]); R = {m: [] for m in range(1, 13)}
        for i in range(6, len(v) - 5):
            w = v[i - 6:i + 6].mean()
            if w > 0: R[mon(ss[i])].append(v[i] / w)
        f = np.ones(12)
        if sum(len(x) for x in R.values()) >= 12:
            f = np.array([np.mean(R[m]) if R[m] else np.nan for m in range(1, 13)]); f = f / np.nanmean(f); f = np.where(np.isfinite(f), f, 1.0)
        self._bi[o] = f; return f
    def per_account(self, o):
        """Dollars per approved account by month on the book (0 = the approval month), the time of year taken out: at each age, the last 24
        approval months that have reached that age by the close (from the first billing month on)."""
        k = ('u', o)
        if k in self._c: return self._c[k]
        b = self.b; S = self.book_index(o); u = np.zeros(HZ)
        for a in range(HZ):
            num = den = 0.0
            for c in range(max(o - 23 - a, b.s0), o - a + 1): num += b.cr(c, c + a) / S[mon(c + a) - 1]; den += b.n(c)
            u[a] = num / den if den else 0.0
        self._c[k] = u; return u
    def per_cohort(self, o):
        """The latest cohorts' pace: what one approval month billed at each age, the time of year taken out, averaged over the last 24 that have reached it."""
        k = ('p', o)
        if k in self._c: return self._c[k]
        b = self.b; S = self.book_index(o); v = np.zeros(HZ)
        for a in range(HZ):
            x = [b.cr(o - m - a, o - m) / S[mon(o - m) - 1] for m in range(24) if o - m - a >= b.s0]
            v[a] = float(np.mean(x)) if x else 0.0
        self._c[k] = v; return v
    def ladder(self, o, c, j):
        """How a cohort of c's age at the close grows over the next j months: the 24 cohorts above it, each from the same age, the time of year taken out."""
        k = ('l', o, c, j)
        if k in self._c: return self._c[k]
        b = self.b; S = self.book_index(o); num = den = 0.0
        for m in range(24):
            sp = o - j - m; src = c - (j + m)
            if sp < b.s0 or src < b.c0: break
            num += b.cr(src, sp + j) / S[mon(sp + j) - 1]; den += b.cr(src, sp) / S[mon(sp) - 1]
        r = num / den if den > 0 else 1.0; self._c[k] = r; return r
    def build_nniy(self, o, goal=None, pace=False):
        """Cohort net new at the close, months ahead 1..HZ. This year's accounts approved by the close: each approval month from what it
        billed at the close, on the ladder. Accounts not approved yet: the plan's count as it stood at the close x dollars per account by age, or (pace)
        the latest cohorts' pace. Both with the whole book's time of year."""
        b, nn = self.b, self.nn; S = self.book_index(o); out = np.zeros(HZ); plans = {}
        for h in range(1, HZ + 1):
            s = o + h; y = year(s); v = 0.0
            for c in range(ym(y, 1), s + 1):
                if c <= o: v += b.cr(c, o) / S[mon(o) - 1] * self.ladder(o, c, h)
                elif pace: v += self.per_cohort(o)[s - c]
                else:
                    if y not in plans: plans[y] = nn.plan_at(y, o, goal)
                    v += plans[y][mon(c) - 1] * self.per_account(o)[s - c]
            out[h - 1] = v * S[mon(s) - 1]
        return out
    def trend(self, o):
        x = np.arange(12); yv = np.array([self.T[s] for s in range(o - 11, o + 1)]); a, c = np.polyfit(x, yv, 1)
        return np.array([c + a * (11 + h) for h in range(1, HZ + 1)])

    def forecasts(self, o, goal=None, methods=('straight', 'seasonal', 'cohort', 'trend', 'cohort_pace')):
        """-> {method: (whole book, net new, existing book)} at the close, months ahead 1..HZ."""
        Y, k = year(o), mon(o); hd = ym(Y + 1, 12) - o - 1; N = {}
        for nm in methods:
            if nm in ('straight', 'seasonal'): N[nm] = self.napkin_nniy(o, nm, goal)
            elif nm == 'cohort': N[nm] = self.build_nniy(o, goal)
            elif nm == 'cohort_pace': N[nm] = self.build_nniy(o, goal, pace=True)
        if any(nm in N for nm in LAY):
            nd = {nm: (N[nm][hd] if nm in N else 0.0) for nm in LAY}
            L = self.eb.legacy_at(o, nd, goal, HZ)
        if 'cohort_pace' in N:
            # every account approved after the close at the pace, the ones joining the existing book too: this year's months still to come
            # (their December revenue: one pace approval month at its age, with December's time of year) and next year's new accounts
            S = self.book_index(o); pc = self.per_cohort(o)
            dov = {m: float(pc[12 - m] * S[11]) for m in range(k + 1, 13)}
            LP = self.eb.legacy_at(o, dict(nd, cohort=N['cohort_pace'][hd]), goal, HZ, dec_override=dov)
        out = {}
        for nm in methods:
            if nm == 'trend': out[nm] = (self.trend(o), None, None)
            elif nm == 'cohort_pace': out[nm] = (N[nm] + LP['cohort'], N[nm], LP['cohort'])
            else: out[nm] = (N[nm] + L[nm], N[nm], L[nm])
        return out

    def rows(self):
        """Every forecast: (method, close, months ahead, target month, forecast, actual, net new forecast, existing book forecast)."""
        if self._rows is not None: return self._rows
        R = []
        for o in range(self.first_close, self.b.close + 1):
            F = self.forecasts(o)
            for nm, (f, fn, fl) in F.items():
                for h in range(1, HZ + 1):
                    if not np.isfinite(f[h - 1]): continue
                    if nm in ('cohort', 'cohort_pace') and (o - self.b.s0) < h: continue    # too little history behind the close for that distance
                    s = o + h
                    R.append((nm, o, h, s, float(f[h - 1]), self.T.get(s), None if fn is None else float(fn[h - 1]), None if fl is None else float(fl[h - 1])))
        self._rows = R; return R

    def by_ahead(self, rows=None):
        rows = rows if rows is not None else self.rows(); M = {}
        for nm, o, h, s, f, a, fn, fl in rows:
            if a: M.setdefault(nm, {}).setdefault(h, []).append(100 * (f / a - 1))
        return {nm: {h: dict(closes=len(v), mean=float(np.mean(v)), sd=float(np.std(v, ddof=1)), typical=float(np.mean(np.abs(v)))) for h, v in d.items() if len(v) >= MIN_CLOSES}
                for nm, d in M.items()}

    def planning_closes(self):
        """The closes each year's plan is made at: the first close, then every plan_month close after it, up to the year before the close's year."""
        out = [self.first_close]; o = ym(year(self.first_close) + 1, self.b.plan_month)
        while year(o) < year(self.b.close): out.append(o); o += 12
        return out

    # ------------------------------------------------------------ the guide's tables
    def grids(self, ch1_three, ch2):
        G = []; IY, NY = year(self.b.close), year(self.b.close) + 1; M13 = [''] + NAMES + ['Year']; nn = self.nn; eb = ch2
        R2 = eb.results(); L = R2['ny']['paths']
        # The whole book next year: Chapter 2's layer plus Chapter 1's net new
        NNV = ch1_three; three = [('straight', 'Straight Line'), ('seasonal', 'Seasonal'), ('cohort', 'Cohort')]
        for vi, (nm, name) in enumerate(three, 1):
            g = Grid(f'3-1-whole-book_chart__v{vi}c1', name, ['series'] + NAMES); g.add('Accounts already on the book', L[nm][0]).add('Net new in year', NNV[nm]); G.append(g)
            g = Grid(f'3-1-whole-book__t{vi}', name, M13)
            g.add('Accounts already on the book', list(L[nm][0]) + [L[nm][0].sum()]).add('Net new in year', list(NNV[nm]) + [NNV[nm].sum()])
            w = L[nm][0] + NNV[nm]; g.add('Whole book', list(w) + [w.sum()]); G.append(g)
        rows = self.rows(); BA = self.by_ahead(rows); CAP = {'straight': 12, 'seasonal': 12}
        BA = {nm: {h: v for h, v in d.items() if h <= CAP.get(nm, 99)} for nm, d in BA.items()}
        four = three + [('trend', 'Trend line')]
        # every projection from the planning closes
        PC = self.planning_closes(); yrs = list(range(year(self.first_close) + 1, NY + 1)); xs = [f'{NAMES[m - 1]} {y}' for y in yrs for m in range(1, 13)]
        idx = {s: i for i, s in enumerate(ym(y, m) for y in yrs for m in range(1, 13))}
        for vi, o in enumerate(PC, 1):
            g = Grid(f'3-2-every-projection__v{vi}c1', f'{FULL[mon(o) - 1]} {year(o)}', ['series'] + xs)
            act = [None] * len(xs)
            for s, i in idx.items():
                if s in self.T: act[i] = self.T[s]
            g.add('Actual', act)
            for nm, name in four:
                v = [None] * len(xs)
                for r in rows:
                    if r[0] == nm and r[1] == o and r[3] in idx: v[idx[r[3]]] = r[4]
                g.add(name, v)
            G.append(g)
        HH = list(range(1, HZ + 1)); col = lambda nm, key: [BA.get(nm, {}).get(h, {}).get(key) for h in HH]
        g = Grid('3-3-typical-miss__v1c1', 'The typical size of the miss, by months ahead', ['series'] + [str(h) for h in HH])
        for nm, name in four: g.add(f'{name} | mean', col(nm, 'typical'))
        G.append(g)
        def band_rows(g, nm, name, with_band=True):
            m_, s_ = col(nm, 'mean'), col(nm, 'sd'); g.add(f'{name} | mean', m_)
            if with_band:
                g.add(f'{name} | lo', [None if a is None else a - b for a, b in zip(m_, s_)]); g.add(f'{name} | hi', [None if a is None else a + b for a, b in zip(m_, s_)])
        for vi, (nm, name) in enumerate(four, 1):
            g = Grid(f'3-3-bands__v{vi}c1', name, ['series'] + [str(h) for h in HH]); band_rows(g, nm, name)
            G.append(g)
        g = Grid('3-7-engine-limit__v1c1', 'The same build, two counts of new accounts', ['series'] + [str(h) for h in HH])
        band_rows(g, 'cohort', 'Plan’s count'); band_rows(g, 'cohort_pace', 'Latest cohorts’ pace'); G.append(g)
        # the year and the quarter, from each planning close
        YQ = {}
        for o in PC:
            y = year(o) + 1; ms = [ym(y, m) for m in range(1, 13)]
            if ms[-1] > self.b.close: continue
            YQ[y] = {}; a_ = np.array([self.T[s] for s in ms])
            for nm, _ in four:
                F = {r[3]: r for r in rows if r[0] == nm and r[1] == o and r[3] in ms}
                f_ = np.array([F[s][4] for s in ms]); rec = dict(year=(f_.sum() / a_.sum() - 1) * 100, quarters=[(f_[3 * q:3 * q + 3].sum() / a_[3 * q:3 * q + 3].sum() - 1) * 100 for q in range(4)])
                if nm != 'trend':
                    an = np.array([self.act_new(s) for s in ms]); fn = np.array([F[s][6] for s in ms]); fl = np.array([F[s][7] for s in ms])
                    rec['new'] = (fn.sum() / an.sum() - 1) * 100; rec['existing'] = (fl.sum() / (a_ - an).sum() - 1) * 100
                YQ[y][nm] = rec
        ys = sorted(YQ); av = lambda vs: float(np.mean(np.abs(vs)))
        g = Grid('3-4-year-and-quarter__t1', 'The whole book, full year', [''] + [str(y) for y in ys] + ['Average size'])
        for nm, name in four: vs = [YQ[y][nm]['year'] for y in ys]; g.add(name, vs + [av(vs)])
        G.append(g)
        g = Grid('3-4-year-and-quarter__t2', 'Net new in year and the existing book, full year', [''] + [str(y) for y in ys] + ['Average size'])
        for lab, nm, key in (('Straight Line and Seasonal: net new', 'straight', 'new'), ('Cohort: net new', 'cohort', 'new'), ('Straight Line: existing book', 'straight', 'existing'),
                             ('Seasonal: existing book', 'seasonal', 'existing'), ('Cohort: existing book', 'cohort', 'existing')):
            vs = [YQ[y][nm][key] for y in ys]; g.add(lab, vs + [av(vs)])
        G.append(g)
        g = Grid('3-4-year-and-quarter__t3', 'The whole book by quarter: average size of the miss', ['', 'Q1', 'Q2', 'Q3', 'Q4', 'Largest single quarter'])
        for nm, name in four:
            g.add(name, [av([YQ[y][nm]['quarters'][q] for y in ys]) for q in range(4)] + [max((YQ[y][nm]['quarters'][q] for y in ys for q in range(4)), key=abs)])
        G.append(g)
        # where the miss comes from: each part's miss, in points of the whole book's month
        SP = {}
        for nm, o, h, s, f, a, fn, fl in rows:
            if nm in LAY and a and h in (1, 3, 6, 12):
                an = self.act_new(s); SP.setdefault(nm, {}).setdefault(h, []).append((100 * (fn - an) / a, 100 * (fl - (a - an)) / a))
        for ti, (cap, j) in enumerate((('Net new in year', 0), ('The existing book', 1)), 1):
            g = Grid(f'3-5-where-the-miss-comes-from__t{ti}', cap, ['', '1 month ahead', '3 months', '6 months', '12 months'])
            for nm, name in three: g.add(name, [float(np.mean([abs(x[j]) for x in SP[nm][h]])) for h in (1, 3, 6, 12)])
            G.append(g)
        # 2026 so far: Chapters 1 and 2's Reforecasts against what billed
        act = nn.nn_row(IY, nn.k); lA = eb.hist[IY]['rev']; ks = [kk for kk, _ in nn.checks() if kk < nn.k]
        CKN = {kk: (f'{kk}+{12 - kk}', f'{FULL[kk]} to {FULL[nn.k - 1]}' if kk + 1 < nn.k else FULL[nn.k - 1]) for kk in ks}
        ch1 = {'straight': lambda kk: nn.sl_reforecast(kk, 'straight'), 'seasonal': lambda kk: nn.sl_reforecast(kk, 'seasonal'),
               'cohort': lambda kk: nn.cohort_forecast(IY, ym(IY, kk))[0].sum(0)}
        K = nn.k
        for ti, (cap, part) in enumerate((('Net new in year', 'new'), ('The existing book', 'existing')), 1):
            g = Grid(f'3-6-this-year-so-far__t{ti}', cap, [''] + [f'{a}: {b_}' for a, b_ in CKN.values()])
            for nm, name in three:
                vals = []
                for kk in ks:
                    if part == 'new': f = ch1[nm](kk); vals.append((f[kk:K].sum() / act[kk:K].sum() - 1) * 100)
                    else: f = R2['reforecast'][kk][nm][0]; vals.append((f[kk:K].sum() / lA[kk:K].sum() - 1) * 100)
                g.add(name, vals)
            G.append(g)
        for vi, kk in enumerate(ks, 1):
            g = Grid(f'3-6-this-year-so-far-chart__v{vi}c1', CKN[kk][0], ['series'] + [f'{NAMES[m - 1]} {IY}' for m in range(1, 13)])
            g.add('Actual', list(act) + [None] * (12 - len(act)))
            for nm, name in three: f = ch1[nm](kk); g.add(name, [None] * (kk - 1) + [act[kk - 1]] + list(f[kk:]))
            G.append(g)
        # the plan's count: Cohort at +5% and +15% instead of the goal (the guide runs it on Power Law)
        PS = {}
        for g_ in (0.05, 0.15):
            mis = {}; yr_m = []
            for o in range(self.first_close, self.b.close + 1):
                F = self.forecasts(o, goal=g_, methods=('cohort',))['cohort']
                for h in range(1, HZ + 1):
                    s = o + h
                    if s > self.b.close or (o - self.b.s0) < h or not self.T.get(s): continue
                    mis.setdefault(h, []).append(100 * (F[0][h - 1] / self.T[s] - 1))
                if o in PC:
                    y = year(o) + 1; ms = [ym(y, m) for m in range(1, 13)]
                    if ms[-1] <= self.b.close:
                        hs = [s - o for s in ms]; fn = sum(F[1][h - 1] for h in hs); an = sum(self.act_new(s) for s in ms); yr_m.append((fn / an - 1) * 100)
            PS[g_] = dict(typical={h: float(np.mean(np.abs(v))) for h, v in mis.items() if len(v) >= MIN_CLOSES}, year=av(yr_m))
        g = Grid('3-7-plan-sensitivity__t1', 'Cohort with three plans for new accounts', ['', '3 months', '12 months', '24 months', 'Net new, full year'])
        g.add('Plan at +5%', [PS[0.05]['typical'][h] for h in (3, 12, 24)] + [PS[0.05]['year']])
        g.add(f'Plan at +{round(self.nn.g * 100)}%, the guide’s', [BA['cohort'][h]['typical'] for h in (3, 12, 24)] + [av([YQ[y]['cohort']['new'] for y in ys])])
        g.add('Plan at +15%', [PS[0.15]['typical'][h] for h in (3, 12, 24)] + [PS[0.15]['year']]); G.append(g)
        self.BA, self.YQ = BA, YQ
        return G
