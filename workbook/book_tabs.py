"""Chapter 2 (Existing Book) and Chapter 3's whole book, as workbook tabs. Called by build_workbook.py.
Chapter 2 works the way Chapter 1 does (D77, Nov 14, 2026): Straight Line closes out this year's book by last year's shares, adds this year's new accounts
(Chapter 1's December for them), grows this year's total by how much bigger the book comes in, and draws the months from January's share; Seasonal fills
that year by each month's average share; Cohort runs every approval cohort at its age's ratio of year to December, in Seasonal's shape."""
import numpy as np
from openpyxl.utils import get_column_letter as CL
from plf.months import NAMES, FULL, ym, year, mon, ml
from plf.chapter2 import ExistingBook, co_key, LAY

def build(wb, b, ch, refs, Sheet, register, ST, q, fmts):
    MONEY, MONEY2, CNT, CNT1, PCT1, PCT2, FAC = fmts
    eb = ExistingBook(b, ch); IY, NY, k = ch.IY, ch.NY, ch.k; RT = eb.rates(NY); Ys = sorted(eb.hist)
    MC = lambda m: CL(m + 1); cond = refs['cond']
    # ---------------------------------------------------------------- Inputs (book)
    ib = Sheet(wb, 'Inputs (book)', 'Inputs for Chapter 2: the existing book', 'Totals the engine\'s prepare step makes from account rows (book_snapshots.csv, book_followon.csv). Blue on yellow: type your own.')
    ib.heading('The book entering each year', 'Every account approved before January that billed in December (or was approved in the last three months), at December, then what the same accounts billed each month of the year.')
    cols = ['December revenue', 'Of it, last year’s new accounts', 'Billing accounts', 'Of them, last year’s new', 'December volume'] + [f'{m} revenue' for m in NAMES] + [f'{m} billing accounts' for m in NAMES] + [f'{m} volume' for m in NAMES]
    ib.header(cols, 'Entering'); HR = {}
    for y in Ys:
        h = eb.hist[y]; n = h['closed']; pad = [None] * (12 - n)
        r = ib.row(str(y), [h['start_rev'], h['new_rev'], h['start_acc'], h['new_acc'], h['start_vol']] + list(h['rev']) + pad + list(h['acc']) + pad + list(h['vol']) + pad, MONEY, 'inp'); HR[y] = r
        for c_ in (4, 5) + tuple(range(19, 31)): ib.ws.cell(r, c_).number_format = CNT
    HC = lambda which, m: CL({'rev': 6, 'acc': 18, 'vol': 30}[which] + m)     # column letter of month m's revenue / billing / volume
    hcell = lambda y, which, m: f"{q('Inputs (book)')}!${HC(which, m)}${HR[y]}"
    hrow = lambda y, which: f"{q('Inputs (book)')}!${HC(which, 1)}${HR[y]}:${HC(which, 12)}${HR[y]}"
    IB = lambda a: f"{q('Inputs (book)')}!{a}"
    # the close and last year: each cohort read forward to December, before Step 2 scales it
    o, d = b.close, ym(IY, 12); o1, d1 = ym(IY - 1, k), ym(IY - 1, 12)
    cs = lambda lo, hi: range(lo, hi + 1); rr = lambda C, s: sum(b.cr(c, s) for c in C); aa = lambda C, s: sum(b.ab(c, s) for c in C)
    old, new, old1, new1 = cs(b.c0, ym(IY, 1) - 1), cs(ym(IY, 1), o), cs(b.c0, ym(IY - 1, 1) - 1), cs(ym(IY - 1, 1), o1)
    ib.heading(f'The {FULL[k - 1]} close and last year', 'Chapter 2: each cohort is read forward to December from the close (Cohort, Step 1), then scaled to Straight Line\'s Step 2.')
    ib.header([f'{FULL[k - 1]} revenue', f'{FULL[k - 1]} billing accounts', f'Last year: December revenue', f'Last year: {FULL[k - 1]} revenue', 'Last year: December billing accounts', f'Last year: {FULL[k - 1]} billing accounts'])
    s3o = ib.row('Accounts already on the book (approved before this year)', [rr(old, o), aa(old, o), rr(old1, d1), rr(old1, o1), aa(old1, d1), aa(old1, o1)], MONEY, 'inp')
    s3n = ib.row(f'This year\'s new accounts, approved by {FULL[k - 1]}', [rr(new, o), aa(new, o), rr(new1, d1), rr(new1, o1), aa(new1, d1), aa(new1, o1)], MONEY, 'inp')
    for r_ in (s3o, s3n):
        for c_ in (3, 6, 7): ib.ws.cell(r_, c_).number_format = CNT
    ib.header(['Accounts approved', 'December revenue', 'December billing accounts'], 'Last year\'s cohort of the same month')
    plan_rows = {}
    for m in range(k + 1, 13):
        c1 = ym(IY - 1, m); plan_rows[m] = ib.row(f'{NAMES[m - 1]} {IY - 1}', [b.n(c1), b.cr(c1, d1), b.ab(c1, d1)], MONEY, 'inp')
        ib.ws.cell(plan_rows[m], 2).number_format = CNT; ib.ws.cell(plan_rows[m], 4).number_format = CNT
    ib.header(['Approved', 'Billing in December'], 'Last year\'s new accounts')
    pyn = ib.row(f'Approved in {IY - 1}', [sum(b.n(c) for c in cs(ym(IY - 1, 1), ym(IY - 1, 12))), sum(b.ab(c, d1) for c in cs(ym(IY - 1, 1), ym(IY - 1, 12)))], CNT, 'inp')
    # groups at the close
    ib.heading(f'The book at the {FULL[k - 1]} close, by approval month', 'Billing: the accounts that billed in the close month. Not billing: in the book, not billing at the close.')
    ib.header(['Status', 'Accounts', 'Revenue at the close', 'Billing accounts at the close', 'Age at December (months)'], 'Approved')
    G0 = ib.r
    for gr in sorted(b.SNAP[o], key=lambda x: (x['c'], x['t'])):
        r = ib.row(ml(gr['c']), ['Billing' if gr['t'] < 4 else 'Not billing', gr['n'], gr['rev'], gr['bill'], d - gr['c']], MONEY, 'inp')
        for c_ in (2, 3, 5, 6): ib.ws.cell(r, c_).number_format = CNT if c_ != 2 else '@'
    G1 = ib.r - 1
    GR = lambda col: f"{q('Inputs (book)')}!${col}${G0}:${col}${G1}"
    # rates by age: kept (next December) and the year against December
    def store_block(title, store, keyf, note):
        ib.heading(title, note)
        ib.header(['Start revenue (billing)', 'Next December revenue', 'Billing accounts', 'Still billing next December', 'Not billing: accounts', 'Not billing: next December revenue',
                   'Not billing: billing next December', 'Year revenue (billing)', 'Not billing: year revenue'], 'Key')
        r0_ = ib.r
        for kk in sorted(store, key=lambda x: (str(type(x)), x)):
            v = store[kk]; ib.row(keyf(kk), list(v), MONEY, 'inp')
        r1_ = ib.r - 1; tot = ib.row('All keys (the fallback)', [f'=SUM({CL(j)}{r0_}:{CL(j)}{r1_})' for j in range(2, 11)], MONEY)
        return r0_, r1_, tot
    K0, K1, KT_ = store_block('By age: the years before', RT['co'], lambda kk: str(kk),
                              f'Every year {RT["years"][0]} to {RT["years"][-1]}: each December\'s accounts grouped by age in months (to 24, then in years to 10), what they billed the December after, and what they billed over the year.')
    ib.ws.column_dimensions['A'].width = 52
    # ---------------------------------------------------------------- 2.1 Straight Line
    sl = Sheet(wb, '2.1 Straight Line', 'Chapter 2, Straight Line', 'Chapter 1\'s Step 1 with the book you carry in: close out this year, add the new accounts, draw the line.')
    sl.heading('Step 1: Read every year the book came in')
    sl.header(['December revenue', 'Of it, last year’s new accounts', 'Billing accounts', 'Of them, last year’s new', 'Next December’s revenue', 'Revenue kept', 'Next December’s billing accounts', 'Accounts kept'], 'Entering')
    s1r = {}; X = {}                                   # X: Step 2's math cells, filled in below (Step 1's forecast row reads them)
    for y in Ys:
        dn = eb.hist[y]['closed'] == 12
        vals = [f"={IB('$B$' + str(HR[y]))}", f"={IB('$C$' + str(HR[y]))}", f"={IB('$D$' + str(HR[y]))}", f"={IB('$E$' + str(HR[y]))}"]
        vals += [f"={hcell(y, 'rev', 12)}", f'=F{sl.r}/B{sl.r}', f"={hcell(y, 'acc', 12)}", f'=H{sl.r}/D{sl.r}'] if dn else ([None] * 4 if y != IY else ['@iydec', f'=F{sl.r}/B{sl.r}', '@iyacc', f'=H{sl.r}/D{sl.r}'])
        s1r[y] = sl.row(str(y), [v if not (isinstance(v, str) and v.startswith('@')) else None for v in vals], MONEY)
        for c_, fm in ((4, CNT), (5, CNT), (7, PCT1), (8, CNT), (9, PCT1)): sl.ws.cell(s1r[y], c_).number_format = fm
    done = [y for y in RT['years']]
    avg = sl.row(f'Average, {done[0]} to {done[-1]}', [None] * 5 + [f'=AVERAGE(G{s1r[done[0]]}:G{s1r[done[-1]]})', None, f'=AVERAGE(I{s1r[done[0]]}:I{s1r[done[-1]]})'], PCT1, bold=True)
    register('2-1-straight-line_step-1__t1', sl, s1r[Ys[0]], [str(y) for y in Ys] + [f'Average, {done[0]} to {done[-1]}'], ncols=8, pct=['@cols:5,7'])
    KA = f"$I${avg}"
    # Step 2: revenue, billing accounts, the math
    sl.gap(); sl.heading('Step 2: Close out this year, add the new accounts, draw the line', f'November and December haven\'t closed, so they\'re forecast from how last year\'s book finished. Each year\'s new accounts join the book heading into January.')
    sl.header(NAMES + ['Year'])
    rPY = sl.row('PY (last year)', [f"={hcell(IY - 1, 'rev', m)}" for m in range(1, 13)] + [f'=SUM(B{sl.r}:M{sl.r})'])
    rLN = sl.row('+ Last year’s new', [None] * 11 + [f"={IB('$C$' + str(HR[IY]))}", None])
    rIY = sl.r; sl.row('IY (this year)', [f"={hcell(IY, 'rev', m)}" if m <= k else f'=$N${rIY}*{MC(m)}{rPY}/$N${rPY}' for m in range(1, 13)] + ['@iyR'])
    rJS = sl.row('January as a share of IY', ['@s1'] + [None] * 12, PCT2)
    rTN = sl.row('+ This year’s new', [None] * 11 + [f"={q('1.1 Straight Line')}!$M${refs['rIY']}", None])
    rNY = sl.row('NY (next year)', ['@ny'] * 12 + [f'=SUM(B{sl.r}:M{sl.r})'], bold=True)
    register('2-1-straight-line_step-2__t1', sl, rPY, ['PY (last year)', '+ Last year’s new', 'IY (this year)', 'January as a share of IY', '+ This year’s new', 'NY (next year)'], pct=['January as a share of IY'])
    sl.gap(); sl.header(NAMES, 'Billing accounts')
    aPY = sl.row('PY (last year)', [f"={hcell(IY - 1, 'acc', m)}" for m in range(1, 13)], CNT)
    aLN = sl.row('+ Last year’s new', [None] * 11 + [f"={IB('$E$' + str(HR[IY]))}"], CNT)
    aIY = sl.row('IY (this year)', [f"={hcell(IY, 'acc', m)}" if m <= k else f"={hcell(IY, 'acc', k)}*{MC(m)}{aPY}/${MC(k)}${aPY}" for m in range(1, 13)], CNT1)
    aTN = sl.row('+ This year’s new', [None] * 11 + ['@nnacc'], CNT1)
    aNY = sl.row('NY (next year)', ['@nya'] * 12, CNT1, bold=True)
    register('2-1-straight-line_step-2__t2', sl, aPY, ['PY (last year)', '+ Last year’s new', 'IY (this year)', '+ This year’s new', 'NY (next year)'], ncols=12)
    sl.gap(); sl.heading('The math'); sl.header(['Value', 'How it is worked out'])
    def mrow(key, label, f, fmt, how, bold=False):
        r = sl.row(label, [f], fmt, bold=bold); h = sl.ws.cell(r, 3, how); h.data_type = 's'; h.font = ST['note']; X[key] = r; return r
    openm = ' and '.join(FULL[m] for m in range(k, 12))
    m0 = mrow('pydec', 'PY, December', f'=M{rPY}', MONEY, 'the PY row’s December')
    mrow('lyn', 'Last year’s new accounts, December', f'=M{rLN}', MONEY, 'Chapter 1: PY’s December')
    mrow('iyin', 'IY’s book came in at', f"=B{X['pydec']}+B{X['lyn']}", MONEY, '= PY December + last year’s new accounts')
    mrow('closed', f'IY, January to {FULL[k - 1]} (closed)', f'=SUM(B{rIY}:{MC(k)}{rIY})', MONEY, 'the closed IY cells, added up')
    mrow('open', f'{openm} as a share of PY', f'=SUM({MC(k + 1)}{rPY}:M{rPY})/N{rPY}', PCT1, 'PY: the open months ÷ the year')
    mrow('iyR', 'IY, the full year', f"=B{X['closed']}/(1-B{X['open']})", MONEY, '= closed ÷ (1 − that share)')
    mrow('iydec', 'IY, December', f"=B{X['iyR']}*M{rPY}/N{rPY}", MONEY, '= the full year × PY’s December share')
    mrow('tyn', 'This year’s new accounts, December', f'=M{rTN}', MONEY, 'Chapter 1: IY’s December (tab 1.1)')
    mrow('nyin', 'NY’s book comes in at', f"=B{X['iydec']}+B{X['tyn']}", MONEY, '= IY December + this year’s new accounts')
    mrow('grow', 'Bigger than IY’s book', f"=B{X['nyin']}/B{X['iyin']}-1", PCT1, '= NY’s book ÷ IY’s book − 1 (where Chapter 1 has the goal)')
    mrow('target', 'Target, next year', f"=B{X['iyR']}*(1+B{X['grow']})", MONEY, '= the full year × (1 + that)', True)
    mrow('s1', 'January as a share of IY', f"=B{rIY}/B{X['iyR']}", PCT2, 'IY January ÷ IY, the full year')
    mrow('nyjan', 'NY January', f"=B{X['target']}*B{X['s1']}", MONEY, '= the target × that share')
    mrow('step', 'Each month after', f"=(B{X['target']}-12*B{X['nyjan']})/66", MONEY, '= (the target − 12 × NY January) ÷ 66, so the twelve months add up to the target')
    mrow('nydec', 'NY December', f"=B{X['nyjan']}+11*B{X['step']}", MONEY, '= NY January + 11 steps')
    mrow('iyacc', 'IY billing accounts, December', f'=M{aIY}', CNT1, f'= {FULL[k - 1]}’s count × PY’s December ÷ {FULL[k - 1]}')
    mrow('nnacc', 'This year’s new accounts billing in December', '@nnaccf', CNT1, '= Chapter 1’s count × the share of last year’s new accounts billing in December (working, below)')
    mrow('a0', 'NY’s book comes in with', f"=B{X['iyacc']}+B{X['nnacc']}", CNT1, '= IY December + this year’s new accounts')
    mrow('nyadec', 'NY December, billing accounts', f'=B{sl.r}*{KA}', CNT1, '= that × the average kept (Step 1), one equal step a month')
    sl.ws.cell(X['nyadec'], 2, f"=B{X['a0']}*{KA}")
    register('2-1-straight-line_step-2__t3', sl, m0, ['PY, December', 'Last year’s new accounts, December', 'IY’s book came in at', f'IY, January to {FULL[k - 1]} (closed)', f'{openm} as a share of PY',
             'IY, the full year', 'IY, December', 'This year’s new accounts, December', 'NY’s book comes in at', 'Bigger than IY’s book', 'Target, next year', 'January as a share of IY', 'NY January',
             'Each month after', 'NY December', 'IY billing accounts, December', 'This year’s new accounts billing in December', 'NY’s book comes in with', 'NY December, billing accounts'],
             ncols=1, pct=[f'{openm} as a share of PY', 'Bigger than IY’s book', 'January as a share of IY'])
    sl.gap(); sl.heading('Working: Chapter 1\'s new accounts, and each cohort\'s scale', 'Chapter 1\'s count and last year\'s billing share make this year\'s new accounts billing in December. The rest scales Cohort\'s part-by-part read to Step 2.')
    W = {}
    def wrow(key, label, f, fmt=MONEY):
        W[key] = sl.row(label, [f], fmt); return W[key]
    IYa_, PYa_ = refs['IYa'], refs['PYa']
    wrow('cnt', 'Chapter 1’s count: this year’s new accounts', f"=ROUND(SUMPRODUCT({cond(IYa_)}*{IYa_})/(SUMPRODUCT({cond(PYa_)}*{PYa_})/SUM({PYa_})),0)", CNT)
    wrow('bill', 'Share of last year’s new accounts billing in December', f"={IB('$C$' + str(pyn))}/{IB('$B$' + str(pyn))}", PCT1)
    sl.ws.cell(X['nnacc'], 2, f"=B{W['cnt']}*B{W['bill']}")
    R_OLD = f"{IB('$D$' + str(s3o))}/{IB('$E$' + str(s3o))}"; R_NEW = f"{IB('$D$' + str(s3n))}/{IB('$E$' + str(s3n))}"
    A_OLD = f"{IB('$F$' + str(s3o))}/{IB('$G$' + str(s3o))}"; A_NEW = f"{IB('$F$' + str(s3n))}/{IB('$G$' + str(s3n))}"
    wrow('rold', f'Accounts already on the book: last year’s December over {FULL[k - 1]}', f'={R_OLD}', '0.000')
    wrow('aold', 'The same, billing accounts', f'={A_OLD}', '0.000')
    wrow('rnew', f'This year’s new accounts: last year’s December over {FULL[k - 1]}', f'=IFERROR({R_NEW},0)', '0.000')
    wrow('anew', 'The same, billing accounts', f'=IFERROR({A_NEW},0)', '0.000')
    wrow('oldread', 'Accounts already on the book, read forward to December', f"={IB('$B$' + str(s3o))}*B{W['rold']}")
    wrow('fold', 'Scale: IY December ÷ that', f"=B{X['iydec']}/B{W['oldread']}", '0.0000')
    wrow('oldacc', 'Their billing accounts, read forward to December', f"={IB('$C$' + str(s3o))}*B{W['aold']}", CNT1)
    wrow('faold', 'Scale: IY billing accounts in December ÷ that', f"=B{X['iyacc']}/B{W['oldacc']}", '0.0000')
    wrow('sofar', f'This year’s new accounts approved by {FULL[k - 1]}, read forward to December', f"={IB('$B$' + str(s3n))}*B{W['rnew']}")
    pc = lambda m: f"{q('1.1 Straight Line')}!{MC(m)}${refs['rPIY']}"
    PLAN = '+'.join(f"{pc(m)}*{IB('$C$' + str(plan_rows[m]))}/{IB('$B$' + str(plan_rows[m]))}" for m in range(k + 1, 13)) or '0'
    PLANA = '+'.join(f"{pc(m)}*{IB('$D$' + str(plan_rows[m]))}/{IB('$B$' + str(plan_rows[m]))}" for m in range(k + 1, 13)) or '0'
    wrow('plan', 'Still to be approved, at the plan’s count, read forward to December', f'={PLAN}')
    wrow('tc', 'Chapter 1’s December less the accounts approved so far', f"=B{X['tyn']}-B{W['sofar']}")
    wrow('fplan', 'Scale for the accounts still to be approved', f"=IF(AND(B{W['tc']}>0,B{W['plan']}>0),B{W['tc']}/B{W['plan']},0)", '0.0000')
    wrow('fnew', 'Scale for the accounts approved so far', f"=IF(AND(B{W['tc']}>0,B{W['plan']}>0),1,IF(B{W['sofar']}>0,B{X['tyn']}/B{W['sofar']},1))", '0.0000')
    wrow('newacc', 'This year’s new accounts’ billing accounts, read forward to December', f"={IB('$C$' + str(s3n))}*B{W['anew']}*B{W['fnew']}+({PLANA})*B{W['fplan']}", CNT1)
    wrow('fanew', 'Scale: Chapter 1’s billing accounts in December ÷ that', f"=IF(B{W['newacc']}>0,B{X['nnacc']}/B{W['newacc']},1)", '0.0000')
    # fill Step 2's grid cells that read the math, and Step 1's forecast row
    for m in range(1, 13):
        x = sl.ws.cell(rNY, m + 1, f"=$B${X['nyjan']}+{m - 1}*$B${X['step']}"); x.number_format = MONEY
        x = sl.ws.cell(aNY, m + 1, f"=$B${X['a0']}+{m}/12*($B${X['a0']}*{KA}-$B${X['a0']})"); x.number_format = CNT1
    sl.ws.cell(rIY, 14, f"=B{X['iyR']}").number_format = MONEY; sl.ws.cell(rJS, 2, f"=B{X['s1']}").number_format = PCT2
    sl.ws.cell(aTN, 13, f"=B{X['nnacc']}").number_format = CNT1
    sl.ws.cell(s1r[IY], 6, f"=B{X['iydec']}").number_format = MONEY; sl.ws.cell(s1r[IY], 8, f"=B{X['iyacc']}").number_format = CNT
    sl.gap(); sl.header(NAMES, 'Next year, Straight Line: revenue and billing accounts')
    sl4 = sl.row('Revenue', [f'={MC(m)}{rNY}' for m in range(1, 13)])
    sl.row('Billing accounts', [f'={MC(m)}{aNY}' for m in range(1, 13)], CNT1)
    register('2-1-straight-line_next-year__v1c1', sl, sl4, ['Revenue', 'Billing accounts'], ncols=12, kind='chart')
    sl.note('The Reforecasts make each layer again at every close: they run in the engine (outputs/chapter-2/*_reforecast__*.csv).')
    T = lambda key: f"{q('2.1 Straight Line')}!$B${X[key]}"; WS = lambda key: f"{q('2.1 Straight Line')}!$B${W[key]}"
    # ---------------------------------------------------------------- 2.2 Seasonal
    se = Sheet(wb, '2.2 Seasonal', 'Chapter 2, Seasonal', 'Straight Line\'s year, filled by each month\'s average share of the year.')
    se.heading('Step 1: Read each month as a share of its year', f'Each closed year: what each month billed ÷ its year. {IY} joins for its closed months, against the year it\'s on course for.')
    se.header(NAMES + ['Year'])
    yr_r = []
    for y in done:
        r = se.r; yr_r.append(se.row(str(y), [f"={hcell(y, 'rev', m)}/$N${r}" for m in range(1, 13)] + [f"=SUM({hrow(y, 'rev')})"], PCT1)); se.ws.cell(r, 14).number_format = MONEY
    rI = se.r; rFull = rI + 5; rV = rI + 7                                            # the full years' average and the first year's volume shares (working, below)
    se.row(str(IY), [f"={hcell(IY, 'rev', m)}/$N${rI}" if m <= k else None for m in range(1, 13)] + [f"=SUM({hcell(IY, 'rev', 1)}:{hcell(IY, 'rev', k).split('!')[1]})/SUM($B${rFull}:${MC(k)}${rFull})"], PCT1)
    se.ws.cell(rI, 14).number_format = MONEY
    iav = se.row('Average', [f'=(SUM({MC(m)}{yr_r[0]}:{MC(m)}{yr_r[-1]})+{MC(m)}{rI})/{len(done) + 1}' if m <= k else f'={MC(m)}{rFull}' for m in range(1, 13)], PCT1, bold=True)
    iva = se.row('Processing volume, average', [f'=AVERAGE({MC(m)}{rV}:{MC(m)}{rV + len(done) - 1})' for m in range(1, 13)], PCT1)
    register('2-2-seasonal_step-1__t1', se, yr_r[0], [str(y) for y in done] + [str(IY), 'Average', 'Processing volume, average'], ncols=13, pct=['@cols:' + ','.join(str(j) for j in range(12))])
    se.gap(); se.ws.cell(se.r, 1, 'Working: the full years\' average, and processing volume read the same way').font = ST['head']; se.r += 1
    assert se.r == rFull, (se.r, rFull)
    se.row('Full years, average', [f'=AVERAGE({MC(m)}{yr_r[0]}:{MC(m)}{yr_r[-1]})' for m in range(1, 13)], PCT1)
    se.gap()
    assert se.r == rV, (se.r, rV)
    for y in done: se.row(f'{y} volume', [f"={hcell(y, 'vol', m)}/SUM({hrow(y, 'vol')})" for m in range(1, 13)], PCT1)
    IR = lambda m: f"{q('2.2 Seasonal')}!${MC(m)}${iav}"
    se.gap(); se.heading('Step 2: Fill Straight Line\'s year by the time of year'); se.header(NAMES + ['Year'])
    se2 = se.row('Straight Line', [f"={q('2.1 Straight Line')}!{MC(m)}{rNY}" for m in range(1, 13)] + [f'=SUM(B{se.r}:M{se.r})'])
    se.row('Average share of the year', [f'={IR(m)}' for m in range(1, 13)] + [f'=SUM(B{se.r}:M{se.r})'], PCT1)
    ses = se.row('Seasonal', [f"={T('target')}*{IR(m)}" for m in range(1, 13)] + [f'=SUM(B{se.r}:M{se.r})'], bold=True)
    register('2-2-seasonal_step-2__t1', se, se2, ['Straight Line', 'Average share of the year', 'Seasonal'], pct=['Average share of the year'])
    se.gap(); se.header(NAMES, 'Next year, Seasonal: revenue and billing accounts')
    sec = se.row('Revenue', [f'={MC(m)}{ses}' for m in range(1, 13)])
    se.row('Billing accounts', [f"={q('2.1 Straight Line')}!{MC(m)}{aNY}" for m in range(1, 13)], CNT1)
    register('2-2-seasonal_next-year__v1c1', se, sec, ['Revenue', 'Billing accounts'], ncols=12, kind='chart')
    # ---------------------------------------------------------------- 2.3 Cohort: one line per approval month
    NS = 9                                                                            # the store's numbers per key
    cS0, cB0, cNB = 5, 6, 7                                                           # E, F, G: December revenue, billing accounts, not billing
    cR0 = 8; cER, cEA, cYR = cR0 + NS, cR0 + NS + 1, cR0 + NS + 2                     # H..P store; Q next Dec revenue; R next Dec billing; S the year
    cM0 = cYR + 1; cNYc = cM0 + 12; cA0 = cNYc + 1                                     # T..AE months; AF next year; AG..AR billing by month
    L_ = CL
    def layer_sheet(name, title, sub):
        sh = Sheet(wb, name, title, sub)
        sh.heading('Step 1: One line per approval month',
                   'December = what the cohort billed at the close, read forward to December and scaled to Straight Line\'s Step 2. The year = December × its age\'s ratio of year to December, from the years before. Each month = the year × Seasonal\'s share.')
        sh.header(['Book or plan', 'Age at December', 'Key', 'December revenue', 'Billing accounts', 'Not billing', 'r: start revenue', 'r: next Dec revenue', 'r: billing', 'r: still billing', 'r: not billing',
                   'r: not billing, next Dec revenue', 'r: not billing, billing', 'r: year revenue', 'r: not billing, year revenue', 'Next December revenue', 'Next December billing', 'Year'] + NAMES + ['Next year'] + [f'{m} billing' for m in NAMES], 'Approved')
        r0 = sh.r
        cohorts = sorted({gr['c'] for gr in b.SNAP[o]})
        items = [(c_, 'book') for c_ in cohorts] + [(ym(IY, m), 'plan') for m in range(k + 1, 13)]
        S_, B_, NB_ = L_(cS0), L_(cB0), L_(cNB); RC = lambda j: L_(cR0 + j)
        for c_, t_ in items:
            r = sh.r; age = d - c_
            if t_ == 'plan':
                m = mon(c_); ir_ = plan_rows[m]
                s_ = f"={pc(m)}*{WS('fplan')}*{IB('$C$' + str(ir_))}/{IB('$B$' + str(ir_))}"
                b_ = f"={pc(m)}*{WS('fplan')}*{IB('$D$' + str(ir_))}/{IB('$B$' + str(ir_))}*{WS('fanew')}"; nb_ = f'=IF({S_}{r}=0,{pc(m)}*{WS("fplan")},0)'
                tl = 'Plan'
            else:
                newf = c_ >= ym(IY, 1); lab = ml(c_); tl = 'Book'
                rs_, as_ = (f"{WS('rnew')}*{WS('fnew')}", f"{WS('anew')}*{WS('fnew')}*{WS('fanew')}") if newf else (f"{WS('rold')}*{WS('fold')}", f"{WS('aold')}*{WS('faold')}")
                s_ = f'=SUMIFS({GR("D")},{GR("A")},"{lab}",{GR("B")},"Billing")*{rs_}'
                b_ = f'=SUMIFS({GR("E")},{GR("A")},"{lab}")*{as_}'; nb_ = f'=SUMIFS({GR("C")},{GR("A")},"{lab}",{GR("B")},"Not billing")'
            key = co_key(age); SR = lambda j: f"{q('Inputs (book)')}!${CL(j)}${K0}:${CL(j)}${K1}"; KEYR = f"{q('Inputs (book)')}!$A${K0}:$A${K1}"; FB = lambda j: f"{q('Inputs (book)')}!${CL(j)}${KT_}"
            look = lambda j: f'IFERROR(INDEX({SR(j)},MATCH("{key}",{KEYR},0)),0)'
            rs = [look(j) for j in range(2, 2 + NS)]                                  # the store's numbers; the fallback when the key is missing or has nothing to read
            bad = f'OR(AND({rs[0]}=0,{rs[4]}=0),AND({S_}{r}>0,{rs[0]}<=0),AND({NB_}{r}>0,{rs[4]}<=0))'
            rcells = [f'=IF({bad},{FB(j)},{rs[j - 2]})' for j in range(2, 2 + NS)]
            er = f'=IF({S_}{r}>0,{S_}{r}*{RC(1)}{r}/{RC(0)}{r},0)+IF({NB_}{r}>0,{NB_}{r}*{RC(5)}{r}/{RC(4)}{r},0)'
            ea = f'=IF({B_}{r}>0,{B_}{r}*{RC(3)}{r}/{RC(2)}{r},0)+IF({NB_}{r}>0,{NB_}{r}*{RC(6)}{r}/{RC(4)}{r},0)'
            yr = f'=IF({S_}{r}>0,{S_}{r}*{RC(7)}{r}/{RC(0)}{r},0)+IF({NB_}{r}>0,{NB_}{r}*{RC(8)}{r}/{RC(4)}{r},0)'
            path = [f'=${L_(cYR)}{r}*{IR(m)}' for m in range(1, 13)]
            pacc = [f'=(${B_}{r}+{m}/12*(${L_(cEA)}{r}-${B_}{r}))' for m in range(1, 13)]
            sh.row(ml(c_), [tl, age, str(key), s_, b_, nb_] + rcells + [er, ea, yr] + path + [f'=SUM({L_(cM0)}{r}:{L_(cM0 + 11)}{r})'] + pacc)
            for j in (cB0, cNB, cEA): sh.ws.cell(r, j).number_format = CNT1
        r1 = sh.r - 1
        return sh, r0, r1
    def sum_rows(sh, r0, r1, col, crit_col, crit):
        return f'SUMIFS(${col}${r0}:${col}${r1},${crit_col}${r0}:${crit_col}${r1},{crit})'
    co, c0, c1 = layer_sheet('2.3 Cohort', 'Chapter 2, Cohort', 'Every approval cohort at the ratio of year to December that cohorts of the same age billed in earlier years, in Seasonal\'s shape.')
    # by approval year
    co.gap(); co.heading('Every cohort on its own line, by approval year'); co.header(['December revenue', 'Billing accounts', 'Year against December', 'Next year', 'Next December’s billing accounts'], 'Approved')
    LBL = cA0 + 12 + 1
    co.ws.cell(c0 - 1, LBL, 'Year label').font = ST['head']
    for r in range(c0, c1 + 1):
        co.ws.cell(r, LBL, f'=IF(VALUE(LEFT(A{r},4))>={NY - 9},LEFT(A{r},4),"{NY - 10} and earlier")')
    cyr = co.r; labs = []
    for lab in [f'{NY - 10} and earlier'] + [str(y) for y in range(NY - 9, IY + 1)]:
        crit = f'"{lab}"'; f_ = lambda col: sum_rows(co, c0, c1, L_(col), L_(LBL), crit)
        co.row(lab, [f'={f_(cS0)}', f'={f_(cB0)}', f'=IF(B{co.r}>0,E{co.r}/B{co.r},"")', f'={f_(cNYc)}', f'={f_(cEA)}']); labs.append(lab)
        for c_, fm in ((3, CNT), (4, '0.00"×"'), (6, CNT)): co.ws.cell(co.r - 1, c_).number_format = fm
    co.row('All cohorts', [None] * 3 + [f'=SUM({L_(cNYc)}{c0}:{L_(cNYc)}{c1})', None], bold=True)
    register('2-3-cohort_step-1__t1', co, cyr, labs + ['All cohorts'], ncols=5, skip=[2])
    co.gap(); co.header(NAMES + ['Year'], 'Next year, Cohort: revenue and billing accounts')
    cch = co.row('Revenue', [f'=SUM({L_(cM0 + m - 1)}{c0}:{L_(cM0 + m - 1)}{c1})' for m in range(1, 13)] + [f'=SUM(B{co.r}:M{co.r})'])
    co.row('Billing accounts', [f'=SUM({L_(cA0 + m - 1)}{c0}:{L_(cA0 + m - 1)}{c1})' for m in range(1, 13)], CNT1)
    register('2-3-cohort_next-year__v1c1', co, cch, ['Revenue', 'Billing accounts'], ncols=12, kind='chart')
    # ---------------------------------------------------------------- 2.5 Three layers and 3.1 the whole book
    fl = Sheet(wb, '2.5 Three layers', 'Chapter 2, where the existing book lands you', 'The existing book next year, three layers.')
    fl.heading('Next year, three layers'); fl.header(NAMES + ['Year'])
    LR = {'straight': ("2.1 Straight Line", rNY), 'seasonal': ("2.2 Seasonal", ses), 'cohort': ("2.3 Cohort", cch)}
    TT = {'straight': 'Straight Line', 'seasonal': 'Seasonal', 'cohort': 'Cohort'}
    f0 = fl.r
    for nm in LAY: shn, rr_ = LR[nm]; fl.row(TT[nm], [f"={q(shn)}!{MC(m)}{rr_}" for m in range(1, 13)] + [f'=SUM(B{fl.r}:M{fl.r})'])
    register('2-5-three-layers__t1', fl, f0, [TT[nm] for nm in LAY])
    fl.note('The every-year check and the Reforecasts run in the engine (outputs/chapter-2/).')
    wbk = Sheet(wb, '3.1 Whole book', 'Chapter 3, the whole book three ways', 'Each method\'s existing book (Chapter 2) plus the same method\'s net new in year (Chapter 1).')
    NNR = {'straight': ('1.1 Straight Line', refs['rNY']), 'seasonal': ('1.2 Seasonal', refs['rNS']), 'cohort': ('1.3 Cohort', refs['c0_'])}
    for i, nm in enumerate(LAY, 1):
        wbk.heading(TT[nm]); wbk.header(NAMES + ['Year'])
        shn, rr_ = LR[nm]; nsh, nr_ = NNR[nm]; w0 = wbk.r
        wbk.row('Accounts already on the book', [f"={q(shn)}!{MC(m)}{rr_}" for m in range(1, 13)] + [f'=SUM(B{wbk.r}:M{wbk.r})'])
        wbk.row('Net new in year', [f"={q(nsh)}!{MC(m)}{nr_}" for m in range(1, 13)] + [f'=SUM(B{wbk.r}:M{wbk.r})'])
        wbk.row('Whole book', [f'={MC(m)}{w0}+{MC(m)}{w0 + 1}' for m in range(1, 13)] + [f'=SUM(B{wbk.r}:M{wbk.r})'], bold=True)
        register(f'3-1-whole-book__t{i}', wbk, w0, ['Accounts already on the book', 'Net new in year', 'Whole book'])
        wbk.gap()
    wbk.note('The back test (every method made again at every close since the first, against what billed) runs in the engine: outputs/chapter-3/.')
