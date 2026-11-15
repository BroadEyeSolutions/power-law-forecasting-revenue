"""Chapter 1: Net New In Year. Next year's revenue from new accounts, three ways (Straight Line, Seasonal, Cohort; the guide's fourth, Power Law, isn't in this repository),
each reforecast as the months close. Every grid here is one table in the guide; METHOD.md walks through them step by step.

Words used below, as the guide uses them:
  net new in year (NNIY)  revenue from accounts approved during a year, in the months they bill that year
  PY, IY, NY              the prior year, the year you're in (the close's year), next year
  k                       months closed in IY (10 at an October close)
"""
import numpy as np
from .grids import Grid
from .months import NAMES, FULL, ym, year, mon

CURVE_COHORTS = 12    # Cohort: the age curve is read from the last 12 approval months
SEASON_COHORTS = 24   # Cohort: the time of year is read from the last 24 approval months
SL_CHECKS = (3, 6, 9)  # the 3+9, 6+6 and 9+3; the latest close is added after them

def sl_shares(s1):
    """Straight Line: January at share s1 of the year, every month after up by the same step, twelve months adding to 1.
    The step is (1 - 12 x s1) / 66, because the eleven steps after January add up to 1 + 2 + ... + 11 = 66 steps."""
    d = (1 - 12 * s1) / 66
    return np.array([s1 + i * d for i in range(12)])

def phase(p):
    """Weighted: 1 - p in January rising in equal steps to 1 + p in December (averages 1 over the year)."""
    return np.array([(1 - p) + 2 * p * i / 11 for i in range(12)])

class NetNewInYear:
    def __init__(self, book):
        b = self.b = book
        self.IY, self.k = year(b.close), mon(b.close); self.PY, self.NY = self.IY - 1, self.IY + 1
        self.g = b.goal
        self.first_year = year(b.s0) if mon(b.s0) == 1 else year(b.s0) + 1   # the first full year on the book
        self._model = {}

    # ------------------------------------------------------------ the two building blocks
    def nn(self, y, m):
        """Net new in year: what the accounts approved in year y (January to month m) billed in month m."""
        return sum(self.b.cr(ym(y, a), ym(y, m)) for a in range(1, m + 1))
    def nn_row(self, y, last=12): return np.array([self.nn(y, m) for m in range(1, last + 1)])
    def acc_row(self, y, last=12): return np.array([self.b.n(ym(y, m)) for m in range(1, last + 1)])
    def inv_row(self, y, last=12): return np.array([self.b.inv.get(ym(y, m), 0.0) for m in range(1, last + 1)])
    def leads_row(self, y, last=12): return np.array([self.b.leads.get(ym(y, m), 0.0) for m in range(1, last + 1)])

    def plan_at(self, y, close, goal=None):
        """The count of new accounts for year y, as the plan stood at the close (Chapter 3 makes every method again at every close).
        A year whose plan was set by the close (its October before): plan_accounts. The year after the close's year: that year's count so far,
        divided by the year before's share of its count in the same months, x (1 + goal), placed the way the year before placed its accounts. Two years out:
        that x (1 + goal)."""
        g = self.g if goal is None else goal; Y, k = year(close), mon(close)
        if y <= Y: return self.plan_accounts(y, g)
        p1 = self.acc_row(Y - 1); est = self.acc_row(Y, k).sum() / (p1[:k].sum() / p1.sum()); plan1 = p1 * est * (1 + g) / p1.sum()
        return plan1 if y == Y + 1 else plan1 * (1 + g) ** (y - Y - 1)

    def plan_accounts(self, y, goal=None):
        """The plan's count for year y, set at the plan_month close (October) a year before: year y-1's new accounts through that month,
        divided by year y-2's share of its accounts in those months (= year y-1's count), times (1 + goal), placed in the months
        the way year y-2 placed them (the last full year of approvals)."""
        P = self.b.plan_month; p = self.acc_row(y - 2); ytd = self.acc_row(y - 1, P).sum(); est = ytd / (p[:P].sum() / p.sum())
        return p * est * (1 + (self.g if goal is None else goal)) / p.sum()

    # ------------------------------------------------------------ Straight Line
    def straight_line_numbers(self):
        """Step 1 to 3's numbers: this year closed out, the target, the line, the count and its price."""
        k = self.k; PYr, IYr = self.nn_row(self.PY), self.nn_row(self.IY, k)
        est = lambda closed, py: closed.sum() / (py[:k].sum() / py.sum())        # the months closed / PY's share of them = the year
        PYa, PYi, PYl = self.acc_row(self.PY), self.inv_row(self.PY), self.leads_row(self.PY)
        IYa, IYi, IYl = self.acc_row(self.IY, k), self.inv_row(self.IY, k), self.leads_row(self.IY, k)
        R = dict(PYr=PYr, IYr=IYr, PYa=PYa, PYi=PYi, PYl=PYl, IYa=IYa, IYi=IYi, IYl=IYl)
        R['iyR'] = est(IYr, PYr)
        # This year's count is whole accounts: the months closed ÷ PY's share of them, rounded. Its leads and investment are that count at
        # this year's rates so far (leads and investment per new account, January to the close).
        R['iyA'] = float(round(est(IYa, PYa))); R['iyL'] = R['iyA'] * IYl.sum() / IYa.sum(); R['iyI'] = R['iyA'] * IYi.sum() / IYa.sum()
        R['closed'] = IYr.sum(); R['open_share'] = PYr[k:].sum() / PYr.sum()
        R['iy_months'] = np.concatenate([IYr, R['iyR'] * PYr[k:] / PYr.sum()])   # the months not closed take PY's share of the year
        R['target'] = R['iyR'] * (1 + self.g)
        R['s1'] = IYr[0] / R['iyR']; R['w'] = sl_shares(R['s1']); R['ny'] = R['target'] * R['w']
        R['rpa'] = R['iyR'] / R['iyA']; R['need'] = R['target'] / R['rpa']
        R['rate'] = R['iyA'] / R['iyL']; R['cpl'] = R['iyI'] / R['iyL']; R['cpa'] = R['iyI'] / R['iyA']
        plans = [('This year (IY)', 0.0, '', 1.0, 1.0, True), ('Plan 1', self.g, 'nothing', 1.0, 1.0, False),
                 ('Plan 2', self.g, f'CVR {self.b.cvr_change * 100:+.0f}%', 1 + self.b.cvr_change, 1.0, False),
                 ('Plan 3', self.g, f'cost {self.b.cpl_change * 100:+.0f}%'.replace('-', '−'), 1.0, 1 + self.b.cpl_change, False),
                 ('Plan 4', 0.0, f'cost {self.b.cpl_change * 100:+.0f}%'.replace('-', '−'), 1.0, 1 + self.b.cpl_change, False)]
        R['plans'] = []
        for head, gg, ch, rm, cm, base in plans:
            acc = R['iyA'] * (1 + gg); rate = R['rate'] * rm; leads = acc / rate; cpl = R['cpl'] * cm; bud = leads * cpl
            R['plans'].append(dict(head=head, gg=gg, ch=ch, rm=rm, cm=cm, base=base, acc=acc, rate=rate, leads=leads, cpl=cpl, bud=bud, cpa=bud / acc,
                                   rev=R['iyR'] * (1 + gg), vs=bud / R['iyI'] - 1))
        R['pysh'] = PYa / PYa.sum(); R['rsh'] = R['iy_months'] / R['iyR']
        return R

    def straight_line(self):
        R = self.straight_line_numbers(); k = self.k; G = []
        M13 = [''] + NAMES + ['Year']
        for cap, y, a, i, l, r, n in (('PY', self.PY, R['PYa'], R['PYi'], R['PYl'], R['PYr'], 12), ('IY', self.IY, R['IYa'], R['IYi'], R['IYl'], R['IYr'], k)):
            pad = [None] * (12 - n); yr = (lambda row, e: row.sum() if cap == 'PY' else e)
            g = Grid(f'1-1-straight-line_needs__t{1 if cap == "PY" else 2}', f'{cap}: four numbers by month', M13)
            g.add('Investment', list(i) + pad + [yr(i, R['iyI'])]).add('Leads', list(l) + pad + [yr(l, R['iyL'])])
            g.add('New accounts', list(a) + pad + [yr(a, R['iyA'])]).add('Net new revenue', list(r) + pad + [yr(r, R['iyR'])])
            G.append(g)
        g = Grid('1-1-straight-line_step-1__t1', 'Close out this year, add the goal, draw the line', M13)
        g.add('PY (last year)', list(R['PYr']) + [R['PYr'].sum()]).add('IY (this year)', list(R['iy_months']) + [R['iyR']])
        g.add('January as a share of IY', [R['s1'] * 100] + [None] * 12).add('NY (next year)', list(R['ny']) + [R['target']]); G.append(g)
        cl = f'{FULL[k]} and {FULL[11]}' if k == 10 else 'The months not closed'
        g = Grid('1-1-straight-line_step-1__t2', 'The math', ['', 'Value', 'How it is worked out'])
        g.add(f'IY, January to {FULL[k - 1]} (closed)', [R['closed'], 'the closed IY cells, added up'])
        g.add(f'{cl} as a share of PY', [R['open_share'] * 100, 'PY: those months ÷ the year'])
        g.add('IY, the full year', [R['iyR'], '= closed ÷ (1 − that share)']).add('Goal', [self.g * 100, 'set by the company'])
        g.add('Target, next year', [R['target'], '= the full year × (1 + the goal)']).add('January as a share of IY', [R['s1'] * 100, 'IY January ÷ IY, the full year'])
        g.add('NY January', [R['ny'][0], '= the target × that share']).add('Each month after', [R['target'] * (R['w'][1] - R['w'][0]), '= (the target − 12 × NY January) ÷ 66'])
        g.add('NY December', [R['ny'][11], '= NY January + 11 steps']); G.append(g)
        g = Grid('1-1-straight-line_step-2__t1', 'The revenue target, worked back to a count', ['', 'This year (IY)', 'Next year (plan)', 'How next year is worked out'])
        g.add('Net new revenue', [R['iyR'], R['target'], f'= this year × (1 + {self.g * 100:.0f}%), the goal'])
        g.add('Revenue per new account', [R['rpa'], R['rpa'], 'held at this year’s average (revenue ÷ accounts)'])
        g.add('New accounts', [R['iyA'], R['need'], '= the target ÷ revenue per account']); G.append(g)
        P = R['plans']
        g = Grid('1-1-straight-line_step-3__t1', 'The count, priced four ways', [''] + [p['head'] for p in P])
        g.add('Revenue goal', [None if p['base'] else (p['gg'] * 100 if p['gg'] else 'flat') for p in P])
        g.add('What changes', [None if p['base'] else p['ch'] for p in P]).add('New accounts', [p['acc'] for p in P])
        g.add('CVR (leads to accounts)', [p['rate'] * 100 for p in P]).add('Leads (accounts ÷ CVR)', [p['leads'] for p in P])
        g.add('Cost per lead', [p['cpl'] for p in P]).add('Budget (leads × cost per lead)', [p['bud'] for p in P])
        g.add('Cost per new account (budget ÷ accounts)', [p['cpa'] for p in P])
        g.add('Budget against this year', [None if p['base'] else ('flat' if abs(p['vs']) < 5e-4 else p['vs'] * 100) for p in P]); G.append(g)
        # Step 4: each plan on Step 1's line, evenly or weighted
        wph = phase(self.b.phase_in); vi = 0
        for p in P[1:]:
            for how in ('Evenly', 'Weighted'):
                vi += 1; wtd = how == 'Weighted'
                ld = np.full(12, p['leads'] / 12); cv = p['rate'] * (wph if (wtd and p['rm'] != 1) else 1); cp = p['cpl'] * ((2 - wph) if (wtd and p['cm'] != 1) else 1)
                ac = ld * cv; sp = ld * cp; rv = p['acc'] * R['rpa'] * R['w']
                G.append(self._chart(f'1-1-straight-line_step-4__v{vi}c1', f'{p["head"]}, {how.lower()}', rv, ac, sp))
        # Reforecast: IY at each close
        for vi, (kk, label) in enumerate(self.checks(), 1):
            rv = self.sl_reforecast(kk, 'straight'); ac = self.accounts_at(kk)
            G.append(self._chart(f'1-1-straight-line_reforecast__v{vi}c1', label, rv, ac, self.spend_at(kk, ac)))
        return G

    def checks(self):
        """The closes the Reforecast shows: the 3+9, 6+6 and 9+3 that have happened, then the latest close."""
        out = [(c, f'{c}+{12 - c}') for c in SL_CHECKS if c < self.k]
        return out + [(self.k, f'Every month: {FULL[self.k - 1]}')]

    def accounts_at(self, kk):
        """IY's new accounts as they stood at the close of month kk: the months closed, then the plan's count."""
        return np.concatenate([self.acc_row(self.IY, kk), self.plan_accounts(self.IY)[kk:]])
    def spend_at(self, kk, ac):
        """Spend: what was invested in the months closed; the months still open at IY's cost per new account."""
        R = self.straight_line_numbers()
        return np.concatenate([self.inv_row(self.IY, kk), ac[kk:] * R['cpa']])

    def sl_reforecast(self, kk, how):
        """IY made again at the close of month kk. The year = the months closed ÷ PY's share of them. What's left goes on the months
        still open: on the straight line from January's share (Straight Line), or by each month's average share of the year, every
        full year on the book (Seasonal)."""
        PYr = self.nn_row(self.PY); act = self.nn_row(self.IY, kk); est = act.sum() / (PYr[:kk].sum() / PYr.sum()); rest = est - act.sum()
        w = sl_shares(act[0] / est) if how == 'straight' else self.full_year_shares(self.IY)[0].mean(0)
        return np.concatenate([act, rest * w[kk:] / w[kk:].sum()])

    def _chart(self, name, title, rv, ac, sp, extra=None):
        g = Grid(name, title, ['series'] + NAMES); g.add('Revenue', rv); g.add('New accounts', ac)
        for nm, vals in (extra or []): g.add(nm, vals)
        g.add('Spend', sp); g.add('Cost per new account', np.asarray(sp) / np.asarray(ac)); return g

    # ------------------------------------------------------------ Seasonal
    def full_year_shares(self, before):
        """Each full year on the book before year `before`: its months as shares of its year, and its total."""
        yrs = list(range(self.first_year, before)); S = np.array([self.nn_row(y) / self.nn_row(y).sum() for y in yrs])
        return S, yrs, [float(self.nn_row(y).sum()) for y in yrs]

    def seasonal_shares(self):
        """Step 2: every January together, every February together. The year in progress joins the average for its closed months,
        measured against the year it is forecast to finish (its closed months ÷ the full years' average share of those months)."""
        k = self.k; S, yrs, tot = self.full_year_shares(self.IY); full = S.mean(0)
        part = self.nn_row(self.IY, k); est = part.sum() / full[:k].sum(); psh = part / est
        avg = full.copy(); avg[:k] = (S[:, :k].sum(0) + psh) / (len(yrs) + 1)
        lo, hi = S.min(0), S.max(0); lo[:k] = np.minimum(lo[:k], psh); hi[:k] = np.maximum(hi[:k], psh)
        return dict(S=S, yrs=yrs, tot=tot, psh=psh, est=est, avg=avg, lo=lo, hi=hi)

    def seasonal(self):
        R = self.straight_line_numbers(); Q = self.seasonal_shares(); G = []; M13 = [''] + NAMES + ['Year']
        g = Grid('1-2-seasonal_step-1__t1', 'The year’s number, filled into twelve months', M13)
        sh = R['rsh'] * 100
        g.add('Last year (PY)', list(R['PYr']) + [R['PYr'].sum()])   # the guide, Nov 14: last year's revenue above this year's
        g.add('This year (IY)', list(R['iy_months']) + [R['iyR']]).add('Share of the year', list(sh) + [100])
        g.add('Plan, same shares', list(R['target'] * R['rsh']) + [R['target']]).add('Share of the year', list(sh) + [100])
        g.add('Plan, spread evenly', [R['target'] / 12] * 12 + [R['target']]).add('Share of the year', [100 / 12] * 12 + [100]); G.append(g)
        g = Grid('1-2-seasonal_step-2__t1', 'Each month’s share of the year', M13)
        for y, s, t in zip(Q['yrs'], Q['S'], Q['tot']): g.add(str(y), list(s * 100) + [t])
        g.add(str(self.IY), list(Q['psh'] * 100) + [None] * (12 - self.k) + [Q['est']])
        g.add('Average', list(Q['avg'] * 100) + [None]).add('High to low, points', list((Q['hi'] - Q['lo']) * 100) + [None]); G.append(g)
        ny = R['target'] * Q['avg']
        g = Grid('1-2-seasonal_step-2__t2', 'Next year’s months from the average: Straight Line’s year', M13); g.add('Net new revenue', list(ny) + [ny.sum()]); G.append(g)
        am, sp = self.plan1_months(R)
        G.append(self._chart('1-2-seasonal_next-year__v1c1', 'Seasonal, next year', ny, am, sp))
        for vi, (kk, label) in enumerate(self.checks(), 1):
            ac = self.accounts_at(kk); G.append(self._chart(f'1-2-seasonal_reforecast__v{vi}c1', label, self.sl_reforecast(kk, 'seasonal'), ac, self.spend_at(kk, ac)))
        return G

    def plan1_months(self, R):
        """Plan 1's new accounts placed in the months the way PY placed them, and their spend at Plan 1's rates."""
        p = R['plans'][1]; am = p['acc'] * R['pysh']; return am, am / p['rate'] * p['cpl']

    # ------------------------------------------------------------ Cohort
    def model(self, close):
        """The age curve (dollars per approved account by month on the book, the time of year taken out) and the time-of-year
        factor (by calendar month, averaging 1.00), as read at the close."""
        if close in self._model: return self._model[close]
        b = self.b
        def raw_curve(c0, c1, seas=None):
            num = np.zeros(12); den = np.zeros(12)
            for c in range(c0, c1 + 1):
                for a in range(12):
                    s = c + a
                    if s > close: break
                    num[a] += b.cr(c, s) / (seas[mon(s) - 1] if seas is not None else 1.0); den[a] += b.n(c)
            return num / np.where(den > 0, den, np.nan)
        c24 = raw_curve(close - (SEASON_COHORTS - 1), close)
        a_ = np.zeros(12); p_ = np.zeros(12)
        for c in range(close - (SEASON_COHORTS - 1), close + 1):
            for a in range(12):
                s = c + a
                if s > close: break
                a_[mon(s) - 1] += b.cr(c, s); p_[mon(s) - 1] += b.n(c) * c24[a]
        seas = a_ / p_; seas = seas / seas.mean()
        curve = raw_curve(close - (CURVE_COHORTS - 1), close, seas)
        self._model[close] = (curve, seas); return curve, seas

    def level(self, c, close, curve, seas):
        """A cohort already billing runs at its own level: what it has billed (first twelve months) ÷ what the curve said. 1 until it has two months."""
        ks = [a for a in range(12) if c + a <= close]
        if len(ks) < 2: return 1.0
        pred = sum(self.b.n(c) * curve[a] * seas[mon(c + a) - 1] for a in ks)
        return float(sum(self.b.cr(c, c + a) for a in ks) / pred) if pred > 0 else 1.0

    def cohort_forecast(self, y, close, plan=None):
        """Year y by approval month (rows) and billing month (columns), as forecast at the close: billed months as billed; the rest
        accounts x the curve x the time of year (x the cohort's level, for cohorts already approved). Not approved yet: the plan's count."""
        curve, seas = self.model(close); plan = self.plan_accounts(y) if plan is None else plan; grid = np.zeros((12, 12)); n = np.zeros(12)
        for m in range(1, 13):
            c = ym(y, m); known = c <= close
            n[m - 1] = self.b.n(c) if known else plan[m - 1]; lv = self.level(c, close, curve, seas) if known else 1.0
            for bm in range(m, 13):
                s = c + (bm - m)
                grid[m - 1, bm - 1] = self.b.cr(c, s) if s <= close else n[m - 1] * curve[bm - m] * seas[bm - 1] * lv
        return grid, n

    def triangle(self, y, last):
        t = np.full((12, 12), np.nan); a = np.full(12, np.nan)
        for m in range(1, last + 1):
            c = ym(y, m); a[m - 1] = self.b.n(c)
            for bm in range(m, last + 1): t[m - 1, bm - 1] = self.b.cr(c, ym(y, bm))
        return a, t

    def _tri_grid(self, name, title, a, t, last, total_label, tail='Year', cohort_label='Approved'):
        g = Grid(name, title, [cohort_label, 'Accounts'] + NAMES + [tail])
        for m in range(12):
            if m >= last: g.add(NAMES[m], [None] * 14); continue
            g.add(NAMES[m], [a[m]] + [None if np.isnan(v) else v for v in t[m]] + [np.nansum(t[m])])
        if total_label:
            col = [np.nansum(t[:, j]) if j < last else None for j in range(12)]
            g.add(total_label, [np.nansum(a[:last])] + col + [np.nansum(t)])
        return g

    def cohort(self):
        G = []; close = self.b.close; R = self.straight_line_numbers()
        a, t = self.triangle(self.PY, 12)
        g = self._tri_grid('1-3-cohort_needs__t1', 'Two dates on every revenue number', a, t, 12, None, cohort_label='Approved in'); g.rows = g.rows[:2]; G.append(g)
        G.append(self._tri_grid('1-3-cohort_step-1-py__t1', 'Last year, one line for each month’s new accounts', a, t, 12, 'Billed in the month'))
        ai, ti = self.triangle(self.IY, self.k)
        G.append(self._tri_grid('1-3-cohort_step-1-iy__t1', 'This year on the same grid, as far as it has closed', ai, ti, self.k, 'Billed in the month', tail='So far'))
        curve, seas = self.model(close)
        jan = t[0, :] / a[0]; jun = t[5, 5:] / a[5]
        g = Grid('1-3-cohort_step-2__t1', 'What a new account bills, by its month on the book', [''] + [str(i) for i in range(1, 13)] + ['First 12 months'])
        g.add('PY January accounts', list(jan) + [jan.sum()]).add('PY June accounts', list(jun) + [None] * (12 - len(jun)) + [None])
        g.add('The curve', list(curve) + [curve.sum()]); G.append(g)
        g = Grid('1-3-cohort_step-3__t1', 'The time of year', [''] + NAMES + ['Average'])
        g.add('Time-of-year factor', list(seas) + [1.0]).add('Against an average month', list((seas - 1) * 100) + [None]); G.append(g)
        grid, n = self.cohort_forecast(self.NY, close)
        g = Grid('1-3-cohort_step-4__t1', 'Next year: accounts × the curve × the time of year', ['Approved', 'Accounts'] + NAMES + ['Year'])
        for m in range(12): g.add(NAMES[m], [n[m]] + [None] * m + list(grid[m, m:]) + [grid[m].sum()])
        g.add('Cohort build', [n.sum()] + list(grid.sum(0)) + [grid.sum()])
        nap = R['target'] * R['rsh']; g.add('Straight Line, this year’s shares', [n.sum()] + list(nap) + [nap.sum()]); G.append(g)
        am, sp = self.plan1_months(R)
        G.append(self._chart('1-3-cohort_next-year__v1c1', 'Cohort, next year', grid.sum(0), am, sp))
        for vi, (kk, label) in enumerate(self.checks(), 1):
            ac = self.accounts_at(kk); G.append(self._chart(f'1-3-cohort_reforecast__v{vi}c1', label, self.cohort_forecast(self.IY, ym(self.IY, kk))[0].sum(0), ac, self.spend_at(kk, ac)))
        self._cohort_ny = grid.sum(0); return G

    # ------------------------------------------------------------ where it lands, and the aside
    def three_ways(self):
        R = self.straight_line_numbers(); Q = self.seasonal_shares(); close = self.b.close
        sl = R['target'] * R['w']; se = R['target'] * Q['avg']; co = self.cohort_forecast(self.NY, close)[0].sum(0)
        G = []; g = Grid('1-5-three-ways__t1', 'Next year, three ways', [''] + NAMES + ['Year'])
        for nm, v in (('Straight Line', sl), ('Seasonal', se), ('Cohort', co)): g.add(nm, list(v) + [v.sum()])
        G.append(g)
        g = Grid('1-5-three-ways_this-year-at-each-close__t1', f'Net new in {self.IY}, three ways, as it stood at each close', [''] + [lab for _, lab in self.checks()])
        g.add('Straight Line', [self.sl_reforecast(kk, 'straight').sum() for kk, _ in self.checks()])
        g.add('Seasonal', [self.sl_reforecast(kk, 'seasonal').sum() for kk, _ in self.checks()])
        g.add('Cohort', [self.cohort_forecast(self.IY, ym(self.IY, kk))[0].sum() for kk, _ in self.checks()])
        G.append(g)
        am, sp = self.plan1_months(R)
        G.append(self._chart('1-5-three-ways_chart__v1c1', 'Straight Line', sl, np.full(12, am.sum() / 12), np.full(12, sp.sum() / 12)))
        G.append(self._chart('1-5-three-ways_chart__v2c1', 'Seasonal', se, am, sp))
        G.append(self._chart('1-5-three-ways_chart__v3c1', 'Cohort', co, am, sp))
        return G

    def aside(self):
        """When the better rate arrives: Step 3's plans month by month, then with the change scheduled evenly or weighted."""
        R = self.straight_line_numbers(); G = []; M13 = [''] + NAMES + ['Year']
        for i, p in enumerate(R['plans'][1:], 1):
            am = p['acc'] * R['pysh']; lm = am / p['rate']; im = lm * p['cpl']; rv = p['rev'] * R['rsh']
            g = Grid(f'1-6-aside_plans-by-month__t{i}', f'{p["head"]}, month by month', M13)
            g.add('Investment', list(im) + [im.sum()]).add('Cost per lead', [p['cpl']] * 13).add('Leads', list(lm) + [lm.sum()])
            g.add('CVR', [p['rate'] * 100] * 13).add('New accounts', list(am) + [am.sum()]).add('Net new revenue', list(rv) + [rv.sum()])
            g.add('Share of the year', list(R['rsh'] * 100) + [100]); G.append(g)
        a, t = self.triangle(self.PY, 12); rev = np.nansum(t, 1); per = rev / a; avg = rev.sum() / a.sum(); scale = R['rpa'] / avg
        w = phase(self.b.phase_in); ti = 0
        for p in R['plans'][1:]:
            em = p['acc'] * a / a.sum(); lm = em / p['rate']; im = lm * p['cpl']
            for how in ('even', 'weighted'):
                ti += 1; ws = w if (how == 'weighted' and p['rm'] != 1) else np.ones(12); wc = (2 - w) if (how == 'weighted' and p['cm'] != 1) else np.ones(12)
                am = em * ws; rv = am * per * scale; iw = im * wc
                g = Grid(f'1-6-aside_evenly-or-weighted__t{ti}', f'{p["head"]}, {how}', ['Approval month'] + NAMES + ['Year'])
                g.add('Investment', list(iw) + [iw.sum()]).add('Cost per lead', list(p['cpl'] * wc) + [iw.sum() / lm.sum()]).add('Leads', list(lm) + [lm.sum()])
                g.add('CVR', list(p['rate'] * ws * 100) + [p['rate'] * 100]).add('New accounts', list(am) + [am.sum()])
                g.add('PY revenue per account', list(per) + [avg]).add('Net new revenue', list(rv) + [rv.sum()]); G.append(g)
        return G

    def all_grids(self):
        return self.straight_line() + self.seasonal() + self.cohort() + self.three_ways() + self.aside()
