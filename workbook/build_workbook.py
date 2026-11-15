"""Builds workbook/Forecasting-Revenue_Workbook.xlsx: the guide's grids as Excel tabs with live formulas.

  python3 workbook/build_workbook.py                   fills the Inputs tab from data/sample
  python3 workbook/build_workbook.py --data mybook     fills it from your own aggregate files

The Inputs tab is the only place numbers are typed (blue on yellow). Every other cell is a formula. The builder also writes
workbook/layout.json, which says where each guide table sits, so check_workbook.py can compare the sheet with the engine.
Chapter 1 (Net New In Year). Chapters 2 and 3 follow.
"""
import argparse, json, os, sys
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.comments import Comment
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'engine')); sys.path.insert(0, HERE)
from plf.book import Book
from plf.chapter1 import NetNewInYear, SL_CHECKS
from plf.months import NAMES, FULL, ym, ml

F = 'Arial'
ST = dict(title=Font(name=F, size=14, bold=True, color='0A2647'), h=Font(name=F, size=11, bold=True, color='0A2647'), lab=Font(name=F, size=10),
          inp=Font(name=F, size=10, color='0000FF'), fx=Font(name=F, size=10, color='000000'), link=Font(name=F, size=10, color='008000'),
          note=Font(name=F, size=9, italic=True, color='53677E'), head=Font(name=F, size=10, bold=True), ans=Font(name=F, size=10, bold=True))
YEL = PatternFill('solid', fgColor='FFF7CC'); FC = PatternFill('solid', fgColor='DBE8FC'); GRY = PatternFill('solid', fgColor='ECEFF3'); ANS = PatternFill('solid', fgColor='E3F2E6')
THIN = Border(bottom=Side(style='thin', color='C3C9D1'))
MONEY = '$#,##0;($#,##0);"-"'; MONEY2 = '$#,##0.00;($#,##0.00);"-"'; CNT = '#,##0;(#,##0);"-"'; CNT1 = '#,##0.0'; PCT1 = '0.0%'; PCT2 = '0.00%'; FAC = '0.00'
q = lambda s: "'" + s + "'"
LAYOUT = []

class Sheet:
    def __init__(self, wb, name, title, sub=''):
        self.ws = wb.create_sheet(name); self.name = name; self.r = 1
        self.ws['A1'] = title; self.ws['A1'].font = ST['title']
        if sub: self.ws['A2'] = sub; self.ws['A2'].font = ST['note']
        self.r = 4; self.ws.column_dimensions['A'].width = 44
        for c in range(2, 30): self.ws.column_dimensions[CL(c)].width = 14.5
    def ref(self, r, c, absolute=True, sheet=True):
        a = f'${CL(c)}${r}' if absolute else f'{CL(c)}{r}'
        return (q(self.name) + '!' + a) if sheet else a
    def rng(self, r, c0, c1, sheet=True):
        a = f'${CL(c0)}${r}:${CL(c1)}${r}'; return (q(self.name) + '!' + a) if sheet else a
    def heading(self, text, note=''):
        self.r += 1; c = self.ws.cell(self.r, 1, text); c.font = ST['h']; self.r += 1
        if note: n = self.ws.cell(self.r, 1, note); n.font = ST['note']; self.r += 1
    def header(self, cols, first='', start=2):
        self.ws.cell(self.r, 1, first).font = ST['head']
        for j, h in enumerate(cols): x = self.ws.cell(self.r, start + j, h); x.font = ST['head']; x.alignment = Alignment(horizontal='left' if str(h).startswith('How') else 'right'); x.border = THIN
        self.r += 1; return self.r - 1
    def row(self, label, vals, fmt=MONEY, kind='fx', start=2, fill=None, bold=False):
        r = self.r; self.ws.cell(r, 1, label).font = ST['ans'] if bold else ST['lab']
        for j, v in enumerate(vals):
            if v is None and kind != 'inp': continue
            x = self.ws.cell(r, start + j, v)
            k = kind if not (isinstance(v, str) and v.startswith('=') and q('Inputs') in v and kind == 'fx' and self.name != 'Inputs') else 'link'
            x.font = ST['ans'] if bold else ST[k]; x.number_format = fmt
            if kind == 'inp': x.fill = YEL
            elif fill: x.fill = fill
        self.r += 1; return r
    def note(self, text):
        self.ws.cell(self.r, 1, text).font = ST['note']; self.r += 1
    def gap(self, n=1): self.r += n

def register(grid, sh, first_row, labels, col=2, ncols=13, pct=(), kind='sheet', skip=(), match='exact'):
    LAYOUT.append(dict(grid=grid, sheet=sh.name, first_row=first_row, col=col, ncols=ncols, labels=labels, pct=list(pct), kind=kind, skip=list(skip), match=match))

MC = lambda m: CL(m + 1)          # month m (1-12) -> column letter B..M
def mcols(f):                     # 12 month formulas from f(m, col letter)
    return [f(m, MC(m)) for m in range(1, 13)]
def cond(rng, k='months_closed', op='<='):  # months of a B:M row up to k
    return f'(COLUMN({rng})-1{op}{k})'

def build(data, out):
    b = Book(data); ch = NetNewInYear(b); k, IY, PY = ch.k, ch.IY, ch.PY
    wb = Workbook(); wb.remove(wb.active)
    # ---------------------------------------------------------------- Read me
    rd = Sheet(wb, 'Read me', 'Forecasting: Revenue — the workbook', 'Broad Eye Solutions · the grids from the guide at powerlawperformance.com/resources/forecasting-revenue/')
    for line in ['How to use it',
                 '1. Settings: set the months closed in the year you are in (10 = closed through October) and the goal.',
                 '2. Inputs: replace the sample numbers in the blue cells on yellow. Leave the months that have not closed empty.',
                 '3. Read the tabs in order. Each block is one table in the guide, with the guide step in its heading. Every number outside Inputs is a formula.',
                 '', 'What the colours mean',
                 'Blue on yellow: a number you type (Inputs, Settings).   Black: a formula.   Green: a formula that reads another tab.',
                 'Light blue fill: forecast.   Light green fill: the answer the step is after.', '',
                 'What a spreadsheet can and cannot carry',
                 'The Inputs tab takes totals: by month and by approval month. Turning account rows into those totals is the engine\'s prepare step',
                 '(engine/forecast.py --prepare). The Cohort Reforecast rebuilds the age curve and the time of year at every close, so it runs in the',
                 'engine (outputs/chapter-1/1-3-cohort_reforecast__*.csv), not in this workbook. The guide\'s fourth method, Power Law, isn\'t in this workbook.', '',
                 f'Sample data: an invented payments portfolio, no client data, closed through {FULL[k - 1]} {IY}. Investment and leads are illustrative: $500 and 25 leads a new account.',
                 'Tabs 1.x: Chapter 1 (Net New In Year). Tabs 2.x: Chapter 2 (Existing Book), from the Inputs (book) tab. Tab 3.1: the whole book three ways. The Chapter 2 Reforecasts and Chapter 3\'s back test run in the engine.']:
        rd.ws.cell(rd.r, 1, line).font = ST['h'] if line in ('How to use it', 'What the colours mean', 'What a spreadsheet can and cannot carry') else ST['lab']; rd.r += 1
    rd.ws.column_dimensions['A'].width = 140
    # ---------------------------------------------------------------- Settings
    se = Sheet(wb, 'Settings', 'Settings', 'The levers every tab reads.')
    se.header(['Value', 'What it is'], 'Setting')
    SETS = [('months_closed', 'Months closed in the year you are in', k, '0', f'The close: {ml(b.close)}. 10 = closed through October.'),
            ('iy_year', 'The year you are in (IY)', IY, '0', 'PY is the year before, NY the year after.'),
            ('goal', 'Goal: growth wanted from new accounts', b.goal, PCT1, 'Next year = this year x (1 + goal).'),
            ('cvr_change', 'Plan 2: change to the conversion rate', b.cvr_change, PCT1, 'Straight Line, Step 3.'),
            ('cpl_change', 'Plans 3 and 4: change to the cost per lead', b.cpl_change, PCT1, 'Straight Line, Step 3.'),
            ('phase_in', 'Weighted: how far under the plan January starts', b.phase_in, PCT1, 'December ends the same amount over it.')]
    for nm, lab, v, fmt, why in SETS:
        r = se.row(lab, [v], fmt, 'inp'); se.ws.cell(r, 3, why).font = ST['note']
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"{q('Settings')}!$B${r}")
    se.ws.column_dimensions['C'].width = 70
    # ---------------------------------------------------------------- Inputs
    inp = Sheet(wb, 'Inputs', 'Inputs', 'Type your numbers here. Months that have not closed stay empty. Totals by month; the engine\'s prepare step makes them from account rows.')
    P = {}
    nyrs = list(range(ch.first_year, IY + 1))
    inp.heading('Net new revenue by month, every year', 'Revenue from the accounts approved in a year, in the months they bill that year. Seasonal, Step 2 reads every row.')
    inp.header(NAMES + ['So far'], 'Year')
    P['nn'] = {}
    for y in nyrs:
        last = 12 if y < IY else k; v = list(ch.nn_row(y, last)) + [None] * (12 - last)
        r = inp.row(str(y), v, MONEY, 'inp'); inp.ws.cell(r, 14, f'=SUM(B{r}:M{r})').number_format = MONEY; P['nn'][y] = r
    inp.heading('New accounts by approval month, every year', 'Accounts approved in each month. The plan\'s count reads the last full year.')
    inp.header(NAMES + ['So far'], 'Year')
    P['acc'] = {}
    for y in nyrs:
        last = 12 if y < IY else k; v = list(ch.acc_row(y, last)) + [None] * (12 - last)
        r = inp.row(str(y), v, CNT, 'inp'); inp.ws.cell(r, 14, f'=SUM(B{r}:M{r})').number_format = CNT; P['acc'][y] = r
    inp.heading('Investment and leads, PY and IY', 'Straight Line\'s other two numbers. Illustrative in the sample.')
    inp.header(NAMES + ['So far'], '')
    P['inv'] = {}; P['leads'] = {}
    for y in (PY, IY):
        last = 12 if y < IY else k
        r = inp.row(f'{"PY" if y == PY else "IY"} investment ({y})', list(ch.inv_row(y, last)) + [None] * (12 - last), MONEY, 'inp'); inp.ws.cell(r, 14, f'=SUM(B{r}:M{r})').number_format = MONEY; P['inv'][y] = r
        r = inp.row(f'{"PY" if y == PY else "IY"} leads ({y})', list(ch.leads_row(y, last)) + [None] * (12 - last), CNT, 'inp'); inp.ws.cell(r, 14, f'=SUM(B{r}:M{r})').number_format = CNT; P['leads'][y] = r
    # cohort grid: the last 24 approval months, by billing month
    W0 = b.close - 23; win = [W0 + i for i in range(24)]
    inp.heading('Revenue by approval month and billing month: the last 24 approval months', 'Rows: the month the accounts were approved. Columns: the month they billed. The last row and column are the close. Cohort reads it.')
    inp.header(['Accounts approved'] + [ml(s) for s in win], 'Approved')
    P['grid0'] = inp.r
    for c in win:
        inp.row(ml(c), [b.n(c)] + [b.cr(c, s) if s >= c else None for s in win], MONEY, 'inp')
        inp.ws.cell(inp.r - 1, 2).number_format = CNT
    P['grid1'] = inp.r - 1
    DG = f"{q('Inputs')}!$C${P['grid0']}:$Z${P['grid1']}"; DN = f"{q('Inputs')}!$B${P['grid0']}:$B${P['grid1']}"
    close = b.close; seas = None
    I = lambda key, y, col='$B', col2='$M': f"{q('Inputs')}!{col}${P[key][y]}:{col2}${P[key][y]}"
    PYr, IYr, PYa, IYa, Y2a = I('nn', PY), I('nn', IY), I('acc', PY), I('acc', IY), I('acc', IY - 2)
    PYi, IYi, PYl, IYl = I('inv', PY), I('inv', IY), I('leads', PY), I('leads', IY)
    ic = lambda key, y, m: f"{q('Inputs')}!{MC(m)}${P[key][y]}"
    # ---------------------------------------------------------------- 1.1 Straight Line
    sl = Sheet(wb, '1.1 Straight Line', 'Chapter 1, Straight Line', 'This year\'s totals and a goal, drawn as a straight line through the months.')
    sl.heading('Step 1: Close out this year, add the goal, draw the line')
    h1 = sl.header(NAMES + ['Year'])
    MR = h1 + 7   # the math table's first value row (fixed below)
    S = {}
    rPY = sl.row('PY (last year)', mcols(lambda m, c: f"={ic('nn', PY, m)}") + [f'=SUM(B{sl.r}:M{sl.r})'])
    rIY = sl.r; sl.row('IY (this year)', mcols(lambda m, c: f"=IF({m}<=months_closed,{ic('nn', IY, m)},$N${rIY}*{c}{rPY}/$N${rPY})") + [None], fill=None)
    rJS = sl.row('January as a share of IY', [None] + [None] * 12, PCT2)
    rNY = sl.row('NY (next year)', [None] * 13, fill=FC)
    sl.gap(); sl.heading('The math'); sl.header(['Value', 'How it is worked out'])
    def mrow(label, f, fmt, how, bold=False):
        r = sl.row(label, [f], fmt, bold=bold); h = sl.ws.cell(r, 3, how); h.data_type = 's'; h.font = ST['note']; return r
    S['closed'] = mrow(f'IY, January to the close (closed)', f"=SUMPRODUCT({cond(IYr)}*{IYr})", MONEY, 'the closed IY cells, added up')
    S['open'] = mrow('The months not closed as a share of PY', f"=1-SUMPRODUCT({cond(PYr)}*{PYr})/SUM({PYr})", PCT1, 'PY: those months ÷ the year')
    S['iyR'] = mrow('IY, the full year', f"=B{S['closed']}/(1-B{S['open']})", MONEY, '= closed ÷ (1 − that share)')
    S['goal'] = mrow('Goal', '=goal', PCT1, 'Settings')
    S['target'] = mrow('Target, next year', f"=B{S['iyR']}*(1+B{S['goal']})", MONEY, '= the full year × (1 + the goal)', True)
    S['s1'] = mrow('January as a share of IY', f"={ic('nn', IY, 1)}/B{S['iyR']}", PCT2, 'IY January ÷ IY, the full year')
    S['nyjan'] = mrow('NY January', f"=B{S['target']}*B{S['s1']}", MONEY, '= the target × that share')
    S['step'] = mrow('Each month after', f"=B{S['target']}*(1-12*B{S['s1']})/66", MONEY, '= (the target − 12 × NY January) ÷ 66, so the twelve months add up to the target')
    S['nydec'] = mrow('NY December', f"=B{S['nyjan']}+11*B{S['step']}", MONEY, '= NY January + 11 steps')
    sl.note('66 = 1 + 2 + … + 11: the steps the eleven months after January add up to.')
    # fill Step 1's formula cells that read the math table
    for m in range(1, 13):
        x = sl.ws.cell(rNY, m + 1, f"=$B${S['nyjan']}+{m - 1}*$B${S['step']}"); x.number_format = MONEY; x.fill = FC; x.font = ST['fx']
        if m > k: sl.ws.cell(rIY, m + 1).fill = FC
    for (rr_, cc_, f_, fm_) in ((rIY, 14, f"=B{S['iyR']}", MONEY), (rJS, 2, f"=B{S['s1']}", PCT2), (rNY, 14, f'=SUM(B{rNY}:M{rNY})', MONEY)):
        x = sl.ws.cell(rr_, cc_, f_); x.number_format = fm_; x.font = ST['fx']
    sl.ws.cell(rNY, 14).fill = ANS; sl.ws.cell(rNY, 14).font = ST['ans']
    register('1-1-straight-line_step-1__t1', sl, rPY, ['PY (last year)', 'IY (this year)', 'January as a share of IY', 'NY (next year)'], pct=['January as a share of IY'])
    sl.gap(); sl.heading('This year\'s count, leads and investment', 'The count is whole accounts: closed ÷ PY\'s share of those months. Leads and investment: the count at this year\'s rates so far.')
    sl.header(['Value'])
    S['accC'] = sl.row('IY new accounts, closed months', [f"=SUMPRODUCT({cond(IYa)}*{IYa})"], CNT)
    S['accSh'] = sl.row('PY\'s share of its new accounts in those months', [f"=SUMPRODUCT({cond(PYa)}*{PYa})/SUM({PYa})"], PCT1)
    S['iyA'] = sl.row('IY new accounts, the year', [f"=ROUND(B{S['accC']}/B{S['accSh']},0)"], CNT, bold=True)
    S['iyL'] = sl.row('IY leads, the year', [f"=B{S['iyA']}*SUMPRODUCT({cond(IYl)}*{IYl})/B{S['accC']}"], CNT)
    S['iyI'] = sl.row('IY investment, the year', [f"=B{S['iyA']}*SUMPRODUCT({cond(IYi)}*{IYi})/B{S['accC']}"], MONEY)
    sl.gap(); sl.heading('Step 2: Work backwards to the count')
    sl.header(['This year (IY)', 'Next year (plan)'])
    r1 = sl.row('Net new revenue', [f"=B{S['iyR']}", f"=B{S['target']}"])
    S['rpa'] = sl.row('Revenue per new account', [f"=B{r1}/B{S['iyA']}", f"=B{sl.r}"])
    S['need'] = sl.r; sl.row('New accounts', [f"=B{S['iyA']}", f"=C{r1}/C{S['rpa']}"], CNT); sl.ws.cell(S['need'], 3).fill = ANS
    register('1-1-straight-line_step-2__t1', sl, r1, ['Net new revenue', 'Revenue per new account', 'New accounts'], ncols=2)
    sl.gap(); sl.heading('Step 3: Price it', 'Each plan changes one thing. The multiplier rows are the levers.')
    sl.header(['This year (IY)', 'Plan 1', 'Plan 2', 'Plan 3', 'Plan 4'])
    gg = sl.row('Revenue goal', [None, '=goal', '=goal', '=goal', 0], PCT1)
    rm = sl.row('CVR multiplier', [1, 1, '=1+cvr_change', 1, 1], FAC)
    cm = sl.row('Cost per lead multiplier', [1, 1, 1, '=1+cpl_change', '=1+cpl_change'], FAC)
    acc_ = sl.row('New accounts', [f"=$B${S['iyA']}"] + [f"=$B${S['iyA']}*(1+{c}{gg})" for c in 'CDEF'], CNT)
    cvr = sl.row('CVR (leads to accounts)', [f"=$B${S['iyA']}/$B${S['iyL']}*{c}{rm}" for c in 'BCDEF'], PCT1)
    lds = sl.row('Leads (accounts ÷ CVR)', [f'={c}{acc_}/{c}{cvr}' for c in 'BCDEF'], CNT)
    cpl = sl.row('Cost per lead', [f"=$B${S['iyI']}/$B${S['iyL']}*{c}{cm}" for c in 'BCDEF'], MONEY2)
    bud = sl.row('Budget (leads × cost per lead)', [f'={c}{lds}*{c}{cpl}' for c in 'BCDEF'], MONEY, fill=None)
    cpa = sl.row('Cost per new account (budget ÷ accounts)', [f'={c}{bud}/{c}{acc_}' for c in 'BCDEF'], MONEY2)
    vs = sl.row('Budget against this year', [None] + [f'={c}{bud}/$B${bud}-1' for c in 'CDEF'], PCT1)
    prev = sl.row('Net new revenue in the plan', [f"=$B${S['iyR']}"] + [f"=$B${S['iyR']}*(1+{c}{gg})" for c in 'CDEF'])
    for c in 'CDEF': sl.ws[f'{c}{bud}'].fill = ANS
    register('1-1-straight-line_step-3__t1', sl, acc_, ['New accounts', 'CVR (leads to accounts)', 'Leads (accounts ÷ CVR)', 'Cost per lead', 'Budget (leads × cost per lead)',
             'Cost per new account (budget ÷ accounts)'], ncols=5, pct=['CVR (leads to accounts)'])
    PL = {'Plan 1': 'C', 'Plan 2': 'D', 'Plan 3': 'E', 'Plan 4': 'F'}
    sl.gap(); sl.heading('Step 4: Put each plan on the line', 'Evenly: the change is there from January. Weighted: a changed rate is phased in, 10% under the plan in January to 10% over in December.')
    sl.header(NAMES + ['Year'])
    rW = sl.row('Straight line: each month\'s share of the year', mcols(lambda m, c: f"=$B${S['s1']}+{m - 1}*(1-12*$B${S['s1']})/66") + [f'=SUM(B{sl.r}:M{sl.r})'], PCT2)
    rPh = sl.row('Weighted schedule', mcols(lambda m, c: f'=(1-phase_in)+2*phase_in*{m - 1}/11') + [None], FAC)
    vi = 0
    for p, c in PL.items():
        for how in ('Evenly', 'Weighted'):
            vi += 1; sl.gap(); sl.ws.cell(sl.r, 1, f'{p}, {how.lower()}').font = ST['head']; sl.r += 1
            wt = how == 'Weighted'
            r0 = sl.row('Revenue', mcols(lambda m, cc: f"=${c}${acc_}*$B${S['rpa']}*{cc}${rW}") + [f'=SUM(B{sl.r}:M{sl.r})'], fill=FC)
            ra = sl.row('New accounts', mcols(lambda m, cc: f"=${c}${lds}/12*${c}${cvr}" + (f"*IF(${c}${rm}<>1,{cc}${rPh},1)" if wt else '')) + [f'=SUM(B{sl.r}:M{sl.r})'], CNT1)
            rs = sl.row('Spend', mcols(lambda m, cc: f"=${c}${lds}/12*${c}${cpl}" + (f"*IF(${c}${cm}<>1,2-{cc}${rPh},1)" if wt else '')) + [f'=SUM(B{sl.r}:M{sl.r})'])
            sl.row('Cost per new account', mcols(lambda m, cc: f'={cc}{rs}/{cc}{ra}') + [f'=N{rs}/N{ra}'], MONEY2)
            register(f'1-1-straight-line_step-4__v{vi}c1', sl, r0, ['Revenue', 'New accounts', 'Spend', 'Cost per new account'], ncols=12, kind='chart')
    # the IY plan's count (for the Reforecast accounts)
    sl.gap(); sl.heading('IY\'s plan count (made a year ago)', f'{IY - 2}\'s months × ({IY - 1}\'s count, closed months ÷ {IY - 2}\'s share of them) × (1 + goal). The Reforecast\'s open months use it.')
    sl.header(NAMES + ['Year'])
    rEC = sl.row(f'{IY - 1} new accounts, the year (estimated at the close a year ago)', [f"=SUMPRODUCT({cond(PYa)}*{PYa})/(SUMPRODUCT({cond(Y2a)}*{Y2a})/SUM({Y2a}))"], CNT1)
    rPIY = sl.row('IY plan, new accounts', mcols(lambda m, c: f"={ic('acc', IY - 2, m)}*$B${rEC}*(1+goal)/SUM({Y2a})") + [f'=SUM(B{sl.r}:M{sl.r})'], CNT1)
    S['cpaIY'] = sl.row('IY investment per new account', [f"=B{S['iyI']}/B{S['iyA']}"], MONEY2)
    def reforecast(sh, prefix, how, fullmean_row=None):
        out = []
        checks = [(c_, f'{c_}+{12 - c_}') for c_ in SL_CHECKS if c_ < k] + [(None, f'Every month: {FULL[k - 1]}')]
        sh.gap(); sh.heading('Reforecast: IY as it stood at each close', 'The year = the months closed ÷ PY\'s share of them. What is left goes on the months still open.' + (' On the straight line from January\'s share.' if how == 'straight' else ' By each month\'s average share of the year (every full year).'))
        for vi_, (kk, lab) in enumerate(checks, 1):
            sh.gap(); sh.ws.cell(sh.r, 1, lab).font = ST['head']; sh.r += 1
            K_ = sh.row('Months closed at this close', [kk if kk else '=months_closed'], '0', 'inp' if kk else 'fx'); KK = f'$B${K_}'
            cl_ = sh.row('Closed so far', [f"=SUMPRODUCT({cond(IYr, KK)}*{IYr})"])
            es_ = sh.row('The year', [f"=B{cl_}/(SUMPRODUCT({cond(PYr, KK)}*{PYr})/SUM({PYr}))"])
            hdr = sh.header(NAMES + ['Year'])
            if how == 'straight':
                ww = sh.row('Straight line from January\'s share', mcols(lambda m, c: f"={ic('nn', IY, 1)}/$B${es_}+{m - 1}*(1-12*{ic('nn', IY, 1)}/$B${es_})/66"), PCT2)
            else:
                ww = sh.row('Average share of the year', mcols(lambda m, c: f"={q('1.2 Seasonal')}!{c}${fullmean_row}"), PCT2)
            r0 = sh.row('Revenue', mcols(lambda m, c: f"=IF({m}<={KK},{ic('nn', IY, m)},($B${es_}-$B${cl_})*{c}{ww}/SUMPRODUCT({cond(sh.rng(ww, 2, 13, False), KK, '>')}*${CL(2)}${ww}:${CL(13)}${ww}))") + [f'=SUM(B{sh.r}:M{sh.r})'], fill=FC)
            ra = sh.row('New accounts', mcols(lambda m, c: f"=IF({m}<={KK},{ic('acc', IY, m)},{q('1.1 Straight Line')}!{c}${rPIY})") + [f'=SUM(B{sh.r}:M{sh.r})'], CNT1)
            rs = sh.row('Spend', mcols(lambda m, c: f"=IF({m}<={KK},{ic('inv', IY, m)},{c}{ra}*{q('1.1 Straight Line')}!$B${S['cpaIY']})") + [f'=SUM(B{sh.r}:M{sh.r})'])
            sh.row('Cost per new account', mcols(lambda m, c: f'={c}{rs}/{c}{ra}') + [f'=N{rs}/N{ra}'], MONEY2)
            register(f'{prefix}_reforecast__v{vi_}c1', sh, r0, ['Revenue', 'New accounts', 'Spend', 'Cost per new account'], ncols=12, kind='chart'); out.append(r0)
        return out
    rf_sl = reforecast(sl, '1-1-straight-line', 'straight')
    # ---------------------------------------------------------------- 1.2 Seasonal
    sn = Sheet(wb, '1.2 Seasonal', 'Chapter 1, Seasonal', 'The same year, with each month carrying its usual share of it.')
    L = lambda r, c='$B': f"{q('1.1 Straight Line')}!{c}${r}"
    sn.heading('Step 1: Read the shape of one year'); sn.header(NAMES + ['Year'])
    a0 = sn.row('Last year (PY)', mcols(lambda m, c: f"={q('1.1 Straight Line')}!{c}{rPY}") + [f"={q('1.1 Straight Line')}!$N${rPY}"])
    a1 = sn.row('This year (IY)', mcols(lambda m, c: f"={q('1.1 Straight Line')}!{c}{rIY}") + [f"={L(S['iyR'])}"])
    rSh = sn.row('Share of the year', mcols(lambda m, c: f'={c}{a1}/$N${a1}') + [f'=SUM(B{sn.r}:M{sn.r})'], PCT1)
    rPS = sn.row('Plan, same shares', mcols(lambda m, c: f"={L(S['target'])}*{c}{rSh}") + [f'=SUM(B{sn.r}:M{sn.r})'], fill=FC)
    sn.row('Share of the year', mcols(lambda m, c: f'={c}{rPS}/$N${rPS}') + [f'=SUM(B{sn.r}:M{sn.r})'], PCT1)
    rEv = sn.row('Plan, spread evenly', mcols(lambda m, c: f"={L(S['target'])}/12") + [f'=SUM(B{sn.r}:M{sn.r})'], fill=FC)
    sn.row('Share of the year', mcols(lambda m, c: f'={c}{rEv}/$N${rEv}') + [f'=SUM(B{sn.r}:M{sn.r})'], PCT1)
    register('1-2-seasonal_step-1__t1', sn, a0, ['Last year (PY)', 'This year (IY)', 'Share of the year', 'Plan, same shares', 'Share of the year', 'Plan, spread evenly', 'Share of the year'],
             pct=['Share of the year'])
    sn.gap(); sn.heading('Step 2: Read every year together', 'Each month as a share of its year. IY joins the average for its closed months, measured against the year it is forecast to finish.')
    sn.header(NAMES + ['Year'])
    fy = [y for y in nyrs if y < IY]; yr_rows = []
    for y in fy:
        yr_rows.append(sn.row(str(y), mcols(lambda m, c: f"={ic('nn', y, m)}/SUM({I('nn', y)})") + [f"=SUM({I('nn', y)})"], PCT1)); sn.ws.cell(sn.r - 1, 14).number_format = MONEY
    Y0, Y1 = yr_rows[0], yr_rows[-1]
    rIYs = sn.r; rFM = rIYs + 3
    sn.row(str(IY), mcols(lambda m, c: f'=IF({m}<=months_closed,{ic("nn", IY, m)}/$N${rIYs},"")') + [f"=SUMPRODUCT({cond(IYr)}*{IYr})/SUMPRODUCT({cond(sn.rng(rFM, 2, 13, False))}*$B${rFM}:$M${rFM})"], PCT1)
    sn.ws.cell(rIYs, 14).number_format = MONEY; sn.ws.cell(rIYs, 14).fill = FC
    rAv = sn.row('Average', mcols(lambda m, c: f'=IF({m}<=months_closed,(SUM({c}{Y0}:{c}{Y1})+{c}{rIYs})/{len(fy) + 1},{c}{rFM})'), PCT1, bold=True)
    rHL = sn.row('High to low, points', mcols(lambda m, c: f'=IF({m}<=months_closed,MAX({c}{Y0}:{c}{Y1},{c}{rIYs})-MIN({c}{Y0}:{c}{Y1},{c}{rIYs}),MAX({c}{Y0}:{c}{Y1})-MIN({c}{Y0}:{c}{Y1}))*100'), '0.0')
    assert sn.r == rFM
    sn.row('Full years\' average (the Reforecast reads it)', mcols(lambda m, c: f'=AVERAGE({c}{Y0}:{c}{Y1})'), PCT1)
    register('1-2-seasonal_step-2__t1', sn, Y0, [str(y) for y in fy] + [str(IY), 'Average', 'High to low, points'], ncols=12, pct=[str(y) for y in fy] + [str(IY), 'Average'])
    sn.gap(); sn.header(NAMES + ['Year'], 'Next year\'s months from the average: Straight Line\'s year')
    rNS = sn.row('Net new revenue', mcols(lambda m, c: f"={L(S['target'])}*{c}{rAv}") + [f'=SUM(B{sn.r}:M{sn.r})'], fill=FC)
    register('1-2-seasonal_step-2__t2', sn, rNS, ['Net new revenue'])
    sn.gap(); sn.heading('Next year, Seasonal: revenue and new accounts', 'New accounts: Plan 1\'s count, placed in the months the way PY placed them. Spend at Plan 1\'s rates.')
    sn.header(NAMES + ['Year'])
    nr0 = sn.row('Revenue', mcols(lambda m, c: f'={c}{rNS}') + [f'=SUM(B{sn.r}:M{sn.r})'], fill=FC)
    rAm = sn.row('New accounts', mcols(lambda m, c: f"={L(acc_, '$C')}*{ic('acc', PY, m)}/SUM({PYa})") + [f'=SUM(B{sn.r}:M{sn.r})'], CNT1)
    rSp = sn.row('Spend', mcols(lambda m, c: f"={c}{rAm}/{L(cvr, '$C')}*{L(cpl, '$C')}") + [f'=SUM(B{sn.r}:M{sn.r})'])
    sn.row('Cost per new account', mcols(lambda m, c: f'={c}{rSp}/{c}{rAm}') + [f'=N{rSp}/N{rAm}'], MONEY2)
    register('1-2-seasonal_next-year__v1c1', sn, nr0, ['Revenue', 'New accounts', 'Spend', 'Cost per new account'], ncols=12, kind='chart')
    rf_se = reforecast(sn, '1-2-seasonal', 'seasonal', rFM)
    # ---------------------------------------------------------------- 1.3 Cohort
    co = Sheet(wb, '1.3 Cohort', 'Chapter 1, Cohort', 'The year rebuilt from each month\'s new accounts, followed as they bill.')
    o = 12 - k  # PY January's row/column in the 24-month grid is 13 - k (1-based) = o + 1
    co.heading('Step 1: Put both years on the grid — last year (PY)', 'Rows: approval month. Columns: billing month. Read from the Inputs grid.')
    co.header(['Accounts'] + NAMES + ['Year'], 'Approved')
    pyg = co.r
    for m in range(1, 13):
        co.row(NAMES[m - 1], [f'=INDEX({DN},{o + m})'] + [f'=IF({bm}>={m},INDEX({DG},{o + m},{o + bm}),"")' for bm in range(1, 13)] + [f'=SUM(C{co.r}:N{co.r})'])
        co.ws.cell(co.r - 1, 2).number_format = CNT
    pyT = co.row('Billed in the month', [f'=SUM(B{pyg}:B{pyg + 11})'] + [f'=SUM({CL(j)}{pyg}:{CL(j)}{pyg + 11})' for j in range(3, 16)], bold=True); co.ws.cell(pyT, 2).number_format = CNT
    register('1-3-cohort_step-1-py__t1', co, pyg, NAMES + ['Billed in the month'], ncols=14)
    co.gap(); co.heading('Step 1 (continued): this year (IY), as far as it has closed'); co.header(['Accounts'] + NAMES + ['So far'], 'Approved')
    iyg = co.r; o2 = 24 - k
    for m in range(1, 13):
        co.row(NAMES[m - 1], [f'=IF({m}<=months_closed,INDEX({DN},{o2 + m}),"")'] + [f'=IF(AND({m}<=months_closed,{bm}>={m},{bm}<=months_closed),INDEX({DG},{o2 + m},{o2 + bm}),"")' for bm in range(1, 13)]
               + [f'=IF({m}<=months_closed,SUM(C{co.r}:N{co.r}),"")'])
        co.ws.cell(co.r - 1, 2).number_format = CNT
    co.row('Billed in the month', [f'=SUM(B{iyg}:B{iyg + 11})'] + [f'=IF({j - 2}<=months_closed,SUM({CL(j)}{iyg}:{CL(j)}{iyg + 11}),"")' for j in range(3, 15)] + [f'=SUM(O{iyg}:O{iyg + 11})'], bold=True)
    co.ws.cell(co.r - 1, 2).number_format = CNT
    register('1-3-cohort_step-1-iy__t1', co, iyg, NAMES[:k] + ['Billed in the month'] if k == 12 else NAMES + ['Billed in the month'], ncols=14)
    # working grids
    co.gap(); co.heading('Working: the last 24 approval months, read by month on the book', 'Each row slid left so it starts at month 1. Steps 2 and 3 read these grids.')
    AG0 = co.r + 1; co.header(['Accounts'] + [f'Month {a + 1}' for a in range(12)], 'Approved'); AG0 = co.r
    for r in range(1, 25):
        co.row(ml(W0 + r - 1), [f'=INDEX({DN},{r})'] + [f'=IF({r + a}<=24,INDEX({DG},{r},{r + a}),"")' for a in range(12)]); co.ws.cell(co.r - 1, 2).number_format = CNT
    AG1 = co.r - 1
    co.gap(); co.header([''] + [f'Month {a + 1}' for a in range(12)], 'Calendar month of each cell'); CA0 = co.r
    for r in range(1, 25): co.row(ml(W0 + r - 1), [None] + [f'=IF({r + a}<=24,MOD(months_closed-24+{r - 1}+{a},12)+1,"")' for a in range(12)], '0')
    CA1 = co.r - 1
    co.gap(); co.header([''] + [f'Month {a + 1}' for a in range(12)], 'Age alone says (accounts × the 24-month curve)'); EG0 = co.r
    rC24 = EG0 + 24
    for r in range(1, 25): co.row(ml(W0 + r - 1), [None] + [f'=IF({r + a}<=24,$B{AG0 + r - 1}*{CL(a + 3)}${rC24},"")' for a in range(12)])
    co.row('The 24-month curve (time of year left in)', [None] + [f'=SUM({CL(a + 3)}{AG0}:{CL(a + 3)}{AG1})/SUMPRODUCT(({CL(a + 3)}{AG0}:{CL(a + 3)}{AG1}<>"")*$B${AG0}:$B${AG1})' for a in range(12)], MONEY2)
    co.gap(); co.header(NAMES + ['Average'], 'The time of year, worked out')
    rA = co.row('Billed in that calendar month', [f'=SUMIF($C${CA0}:$N${CA1},{m},$C${AG0}:$N${AG1})' for m in range(1, 13)])
    rP = co.row('Age alone says', [f'=SUMIF($C${CA0}:$N${CA1},{m},$C${EG0}:$N${EG0 + 23})' for m in range(1, 13)])
    rR = co.row('Billed ÷ age alone', [f'={MC(m)}{rA}/{MC(m)}{rP}' for m in range(1, 13)] + [f'=AVERAGE(B{co.r}:M{co.r})'], FAC)
    rSe = co.row('Time-of-year factor (set to average 1.00)', [f'={MC(m)}{rR}/$N${rR}' for m in range(1, 13)] + [f'=AVERAGE(B{co.r}:M{co.r})'], FAC, bold=True)
    co.gap(); co.header([''] + [f'Month {a + 1}' for a in range(12)], 'The last 12 approval months, time of year taken out'); DS0 = co.r
    for r in range(13, 25): co.row(ml(W0 + r - 1), [None] + [f'=IF({r + a}<=24,{CL(a + 3)}{AG0 + r - 1}/INDEX($B${rSe}:$M${rSe},{CL(a + 3)}{CA0 + r - 1}),"")' for a in range(12)])
    DS1 = co.r - 1
    rCv = co.row('The curve', [None] + [f'=SUM({CL(a + 3)}{DS0}:{CL(a + 3)}{DS1})/SUMPRODUCT(({CL(a + 3)}{DS0}:{CL(a + 3)}{DS1}<>"")*$B${AG0 + 12}:$B${AG1})' for a in range(12)], MONEY2, bold=True)
    co.gap(); co.heading('Step 2: Read the age curve', 'Dollars per approved account. Month 1 is the month of approval.')
    co.header([str(i) for i in range(1, 13)] + ['First 12 months'])
    s2 = co.row('PY January accounts', [f'={CL(a + 3)}{pyg}/$B${pyg}' for a in range(12)] + [f'=SUM(B{co.r}:M{co.r})'], MONEY2)
    co.row('PY June accounts', [f'={CL(a + 8)}{pyg + 5}/$B${pyg + 5}' for a in range(7)], MONEY2)
    co.row('The curve', [f'={CL(a + 3)}{rCv}' for a in range(12)] + [f'=SUM(B{co.r}:M{co.r})'], MONEY2, bold=True)
    register('1-3-cohort_step-2__t1', co, s2, ['PY January accounts', 'PY June accounts', 'The curve'])
    co.gap(); co.heading('Step 3: Read the time of year'); co.header(NAMES + ['Average'])
    s3 = co.row('Time-of-year factor', [f'={MC(m)}{rSe}' for m in range(1, 13)] + [f'=AVERAGE(B{co.r}:M{co.r})'], FAC)
    co.row('Against an average month', [f'={MC(m)}{s3}-1' for m in range(1, 13)], '+0%;−0%;0%')
    register('1-3-cohort_step-3__t1', co, s3, ['Time-of-year factor', 'Against an average month'], pct=['Against an average month'])
    co.gap(); co.heading('Step 4: Build next year', 'Next year\'s count (this year\'s, closed months ÷ PY\'s share, × (1 + goal)) placed the way PY placed its accounts, × the curve × the time of year.')
    co.header(['Accounts'] + NAMES + ['Year'], 'Approved')
    rEst = co.r + 14
    ny0 = co.r
    for m in range(1, 13):
        co.row(NAMES[m - 1], [f"={ic('acc', PY, m)}*$B${rEst}*(1+goal)/SUM({PYa})"] + [f'=IF({bm}>={m},$B{co.r}*INDEX($C${rCv}:$N${rCv},{bm - m + 1})*INDEX($B${rSe}:$M${rSe},{bm}),"")' for bm in range(1, 13)] + [f'=SUM(C{co.r}:N{co.r})'], fill=None)
        co.ws.cell(co.r - 1, 2).number_format = CNT1
    rCB = co.row('Cohort build', [f'=SUM(B{ny0}:B{ny0 + 11})'] + [f'=SUM({CL(j)}{ny0}:{CL(j)}{ny0 + 11})' for j in range(3, 16)], bold=True, fill=FC); co.ws.cell(rCB, 2).number_format = CNT1
    co.row('Straight Line, this year\'s shares', [f'=B{rCB}'] + [f"={q('1.2 Seasonal')}!{MC(m)}{rPS}" for m in range(1, 13)] + [f'=SUM(C{co.r}:N{co.r})']); co.ws.cell(co.r - 1, 2).number_format = CNT1
    assert co.r == rEst
    co.row('IY new accounts, the year (unrounded)', [f"=SUMPRODUCT({cond(IYa)}*{IYa})/(SUMPRODUCT({cond(PYa)}*{PYa})/SUM({PYa}))"], CNT1)
    register('1-3-cohort_step-4__t1', co, ny0, NAMES + ['Cohort build', 'Straight Line, this year’s shares'], ncols=14)
    co.gap(); co.heading('Next year, Cohort: revenue and new accounts'); co.header(NAMES + ['Year'])
    c0_ = co.row('Revenue', [f'={CL(m + 2)}{rCB}' for m in range(1, 13)] + [f'=SUM(B{co.r}:M{co.r})'], fill=FC)
    cA = co.row('New accounts', [f"={q('1.2 Seasonal')}!{MC(m)}{rAm}" for m in range(1, 13)] + [f'=SUM(B{co.r}:M{co.r})'], CNT1)
    cS = co.row('Spend', [f"={q('1.2 Seasonal')}!{MC(m)}{rSp}" for m in range(1, 13)] + [f'=SUM(B{co.r}:M{co.r})'])
    co.row('Cost per new account', [f'={MC(m)}{cS}/{MC(m)}{cA}' for m in range(1, 13)] + [f'=N{cS}/N{cA}'], MONEY2)
    register('1-3-cohort_next-year__v1c1', co, c0_, ['Revenue', 'New accounts', 'Spend', 'Cost per new account'], ncols=12, kind='chart')
    co.note('The Cohort Reforecast reads the curve and the time of year again at every close: it runs in the engine (outputs/chapter-1/1-3-cohort_reforecast__*.csv).')
    # ---------------------------------------------------------------- 1.5 Three ways
    fw = Sheet(wb, '1.5 Three ways', 'Chapter 1, where net new in year lands you', 'Three forecasts of the same year.')
    fw.heading('Next year, three ways'); fw.header(NAMES + ['Year'])
    f0 = fw.row('Straight Line', [f"={q('1.1 Straight Line')}!{MC(m)}{rNY}" for m in range(1, 13)] + [f'=SUM(B{fw.r}:M{fw.r})'])
    fw.row('Seasonal', [f"={q('1.2 Seasonal')}!{MC(m)}{rNS}" for m in range(1, 13)] + [f'=SUM(B{fw.r}:M{fw.r})'])
    fw.row('Cohort', [f"={q('1.3 Cohort')}!{MC(m)}{c0_}" for m in range(1, 13)] + [f'=SUM(B{fw.r}:M{fw.r})'])
    register('1-5-three-ways__t1', fw, f0, ['Straight Line', 'Seasonal', 'Cohort'])
    fw.gap(); fw.heading(f'Net new in {IY}, as it stood at each close', 'Straight Line and Seasonal from their Reforecasts. Cohort: outputs/chapter-1/1-5-three-ways_this-year-at-each-close__t1.csv.')
    labs = [l_ for _, l_ in ch.checks()]; fw.header(labs)
    fc = fw.row('Straight Line', [f"={q('1.1 Straight Line')}!$N${r}" for r in rf_sl])
    fw.row('Seasonal', [f"={q('1.2 Seasonal')}!$N${r}" for r in rf_se])
    register('1-5-three-ways_this-year-at-each-close__t1', fw, fc, ['Straight Line', 'Seasonal'], ncols=len(labs))
    # ---------------------------------------------------------------- 1.6 Aside
    asd = Sheet(wb, '1.6 Aside', 'Chapter 1, aside: when the better rate arrives', 'Step 3\'s plans month by month, then with the change scheduled evenly or weighted.')
    for i, (p, c) in enumerate(PL.items(), 1):
        asd.heading(f'{p}, month by month'); asd.header(NAMES + ['Year'])
        Lc = lambda r: f"{q('1.1 Straight Line')}!${c}${r}"
        a0 = asd.r
        rI = asd.r; asd.row('Investment', [f'={MC(m)}{rI + 2}*{Lc(cpl)}' for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'])
        asd.row('Cost per lead', [f'={Lc(cpl)}'] * 13, MONEY2)
        asd.row('Leads', [f'={MC(m)}{rI + 4}/{Lc(cvr)}' for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'], CNT)
        asd.row('CVR', [f'={Lc(cvr)}'] * 13, PCT1)
        asd.row('New accounts', [f"={Lc(acc_)}*{ic('acc', PY, m)}/SUM({PYa})" for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'], CNT)
        asd.row('Net new revenue', [f"={Lc(prev)}*{q('1.2 Seasonal')}!{MC(m)}{rSh}" for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'])
        asd.row('Share of the year', [f"={q('1.2 Seasonal')}!{MC(m)}{rSh}" for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'], PCT1)
        register(f'1-6-aside_plans-by-month__t{i}', asd, a0, ['Investment', 'Cost per lead', 'Leads', 'CVR', 'New accounts', 'Net new revenue', 'Share of the year'], pct=['CVR', 'Share of the year'])
        asd.gap()
    asd.heading('PY: revenue inside the year by approval month', 'The aside prices each month\'s accounts at what PY\'s accounts approved that month billed inside PY.')
    asd.header(NAMES + ['Year'])
    pr = asd.row('PY revenue per account', [f"={q('1.3 Cohort')}!$O${pyg + m - 1}/{q('1.3 Cohort')}!$B${pyg + m - 1}" for m in range(1, 13)] + [f"={q('1.3 Cohort')}!$O${pyT}/{q('1.3 Cohort')}!$B${pyT}"], MONEY)
    sc = asd.row('Scale to this year\'s average account', [f"={L(S['rpa'])}/N{pr}"], FAC)
    ti = 0
    for p, c in PL.items():
        Lc = lambda r: f"{q('1.1 Straight Line')}!${c}${r}"
        for how in ('even', 'weighted'):
            ti += 1; asd.gap(); asd.heading(f'{p}, {"evenly" if how == "even" else "weighted"}'); asd.header(NAMES + ['Year'], 'Approval month')
            wt = how == 'weighted'; ws = (lambda m: f"IF({Lc(rm)}<>1,{q('1.1 Straight Line')}!{MC(m)}${rPh},1)") if wt else (lambda m: '1')
            wc = (lambda m: f"IF({Lc(cm)}<>1,2-{q('1.1 Straight Line')}!{MC(m)}${rPh},1)") if wt else (lambda m: '1')
            e0 = asd.r
            asd.row('Investment', [f'={MC(m)}{e0 + 2}*{Lc(cpl)}*{wc(m)}' for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'])
            asd.row('Cost per lead', [f'={Lc(cpl)}*{wc(m)}' for m in range(1, 13)] + [f'=N{e0}/N{e0 + 2}'], MONEY2)
            asd.row('Leads', [f"={Lc(acc_)}*{ic('acc', PY, m)}/SUM({PYa})/{Lc(cvr)}" for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'], CNT)
            asd.row('CVR', [f'={Lc(cvr)}*{ws(m)}' for m in range(1, 13)] + [f'={Lc(cvr)}'], PCT2)
            asd.row('New accounts', [f'={MC(m)}{e0 + 2}*{MC(m)}{e0 + 3}' for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'], CNT)
            asd.row('PY revenue per account', [f'={MC(m)}${pr}' for m in range(1, 13)] + [f'=$N${pr}'], MONEY)
            asd.row('Net new revenue', [f'={MC(m)}{e0 + 4}*{MC(m)}{e0 + 5}*$B${sc}' for m in range(1, 13)] + [f'=SUM(B{asd.r}:M{asd.r})'])
            register(f'1-6-aside_evenly-or-weighted__t{ti}', asd, e0, ['Investment', 'Cost per lead', 'Leads', 'CVR', 'New accounts', 'PY revenue per account', 'Net new revenue'], pct=['CVR'])
    inp.ws.column_dimensions['B'].width = 18
    import book_tabs
    if b.SNAP:
        book_tabs.build(wb, b, ch, dict(rPIY=rPIY, rNY=rNY, rNS=rNS, c0_=c0_, rIY=rIY, IYa=IYa, PYa=PYa, cond=cond), Sheet, register, ST, q, (MONEY, MONEY2, CNT, CNT1, PCT1, PCT2, FAC))
    for ws_ in wb.worksheets: ws_.sheet_view.showGridLines = False; ws_.freeze_panes = 'B4' if ws_.title not in ('Read me',) else None
    wb.save(out)
    json.dump(dict(workbook=os.path.basename(out), tables=LAYOUT), open(os.path.join(HERE, 'layout.json'), 'w'), indent=1)
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default=os.path.join(ROOT, 'data', 'sample'))
    ap.add_argument('--out', default=os.path.join(HERE, 'Forecasting-Revenue_Workbook.xlsx')); a = ap.parse_args()
    print('wrote', build(a.data, a.out))
