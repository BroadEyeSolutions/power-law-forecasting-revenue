# Method

Every calculation in the guide **Forecasting: Revenue** (Broad Eye Solutions, [powerlawperformance.com/resources/forecasting-revenue/](https://powerlawperformance.com/resources/forecasting-revenue/)), step by step, in the order the guide builds it. After each step comes the sample book's answer, so you can check your own working against it as you go.

The engine (`engine/plf/`) carries out exactly what is written here, and `check.py` holds it to the guide's printed numbers. This file is the specification. If it and the engine ever disagree, that's a bug: report it.

It covers all three chapters: 1, Net New In Year; 2, Existing Book; 3, Back Testing.

The guide's fourth method, **Power Law** (its section 1.4, which splits every cohort by tier, and the Power Law layer and lines that follow from it), isn't in this repository, so it isn't in this file either. Where the guide runs a test on Power Law (Chapter 3, Every method has limits), this repository runs it on Cohort, and says so.

---

## Conventions

| | |
|---|---|
| **Month** | One whole number: year × 12 + (month − 1). Written `YYYY-MM` in every file. |
| **The close** | The last month-end close (`close` in `settings.csv`). Everything after it is forecast, and nothing after it is ever read. |
| **IY, PY, NY** | The year you're in (the close's year), the year before, and the year after. |
| **k** | Months closed in IY: 10 at an October close. |
| **Approval month** | The month the account was created in the system the revenue comes from, or the month it first billed if that's earlier. Each approval month is a **cohort**: the grouping this method uses, and the start of each account's age. Other groupings every account carries, such as a size tier, can split those cohorts further. This repository groups by approval month only. |
| **Revenue** | What each account billed in the month, as on its statement. |
| **Net new in year (NNIY)** | Revenue from accounts approved during a year, in the months they bill that year. NNIY(y, m) is what year y's January-to-m cohorts billed in month m. |
| **N(c)** | Accounts approved in month c. |
| **CR(c, s)** | Revenue billed in month s by the accounts approved in month c. |
| **Rounding** | None until a number is shown, with one exception: Straight Line counts this year's new accounts as a whole number (1.1, "This year's count"). The plan's count (below) uses the unrounded figure. |
| **The first full year** | The first calendar year with all twelve months of **billing** on the book. On the sample, billing starts January 2020, so it is 2020, even though `cohorts.csv` holds approval months back to 2012 (accounts approved earlier that still billed from 2020). |
| **Units in the output files** | Shares, rates and goals are written as percent numbers (28.77 means 28.77%). The input files use fractions (`goal` 0.10). |

Chapter 1's numbers come from N(c), CR(c, s) and the plan inputs. Chapter 2 adds the book snapshots (Chapter 2, "The book at a close"). Chapter 3 uses everything. A **billing** account billed more than zero that month. `data/sample/README.md` describes those files, and `templates/` has an empty copy of each.

---

## Chapter 1: Net New In Year

### The plan's count (used by Cohort and every Reforecast)

The plan's count for year *y* is set at the close of the **plan month** a year before. That's `plan_month` in `settings.csv`: 10, October, as the guide does. It stays the same inside every Reforecast and at every back-test close.

1. **Year y−1's count:** its new accounts January to the plan month, ÷ year y−2's share of its own accounts in those months.
2. **× (1 + goal)**
3. **Placed in the months the way year y−2 placed them** (the last full year of approvals): month m gets (y−2's accounts in m ÷ y−2's year) of the total.

This count is **not** rounded.

A year whose plan isn't set yet at a close (the year after the close's year) takes its count the same way, from the months closed so far. Two years out takes that × (1 + goal). This is how Chapter 3 makes every method again at every close (`plan_at` in the engine). The guide is written from an October close, the planning point.
- Sample, NY 2027: 2026 January–October had 2,732 accounts. 2025's share of its year in those months was 2,717 ÷ 3,250. So 2026 = 3,267.94, × 1.10 = **3,594.74**, placed by 2025's months (January 277.6, February 326.3, …).
- Sample, IY 2026 (made at the October 2025 close): 2025 January–October ÷ 2024's share, × 1.10, placed by 2024's months.

---

### 1.1 Straight Line

**What you'll need:** four numbers by month, for PY in full and for IY as far as it has closed: investment, leads, new accounts and net new revenue. Plus the goal.

**Step 1: Close out this year, add the goal, draw the line**

| | Formula | Sample |
|---|---|---|
| IY closed | NNIY of IY, January to month k, added up | $2,680,678 |
| The months not closed as a share of PY | PY's months k+1 to 12 ÷ PY's year | 28.8% |
| IY, the full year | closed ÷ (1 − that share) | $3,763,377 |
| IY's open months | IY's full year × PY's share of the year in that month | Nov $504.7K, Dec $578.0K |
| Target, NY | IY's full year × (1 + goal) | $4,139,715 |
| January as a share of IY (s₁) | IY January ÷ IY's full year | 0.58% |
| NY January | target × s₁ | $24,028 |
| Each month after | target × (1 − 12 s₁) ÷ 66 | +$58,354 |
| NY month m | NY January + (m − 1) × the step | December $665,924 |

66 = 1 + 2 + … + 11, the steps the eleven months after January add up to. So the twelve months add up to the target.

**This year's count, leads and investment**
- **IY new accounts, the year:** IY's accounts January to k ÷ PY's share of its accounts in those months, **rounded to whole accounts**. Sample: 3,268.
- **IY leads and investment, the year:** that count × IY's leads (or investment) per new account, January to k. Sample: 81,700 leads, $1,634,000.

**Step 2: Work backwards to the count**
- Revenue per new account = IY's full year ÷ IY's count. Sample: $1,152.
- NY's new accounts = target ÷ revenue per new account. Sample: 3,594.8 (shown as 3,595).

**Step 3: Price it**

The base rates are this year's:
- CVR = IY count ÷ IY leads (sample 4.0%)
- cost per lead = IY investment ÷ IY leads (sample $20)

Each plan changes one thing:

| Plan | Revenue goal | CVR × | Cost per lead × |
|---|---|---|---|
| 1 | goal | 1 | 1 |
| 2 | goal | 1 + `plan_cvr_change` (1.10) | 1 |
| 3 | goal | 1 | 1 + `plan_cost_per_lead_change` (0.90) |
| 4 | flat (0) | 1 | 1 + `plan_cost_per_lead_change` |

For each plan:
- accounts = IY count × (1 + revenue goal)
- leads = accounts ÷ CVR
- budget = leads × cost per lead
- cost per new account = budget ÷ accounts
- against this year = budget ÷ IY investment − 1. Shown as "flat" inside ±0.05%.

Sample budgets: $1,797,400 / $1,634,000 / $1,617,660 / $1,470,600.

**Step 4: Put each plan on the line**
- **Revenue** in month m = plan accounts × revenue per new account × (s₁ + (m − 1)(1 − 12 s₁)/66).
- **Leads** are the plan's leads ÷ 12 every month.
- **Evenly:** accounts = leads × CVR, spend = leads × cost per lead, the same every month.
- **Weighted:** the rate a plan changes is phased in on the schedule wₘ = (1 − p) + 2p(m − 1)/11, with p = `weighted_phase_in` (0.10): 0.90 in January rising to 1.10 in December.
  - A plan that changes CVR (Plan 2): accounts = leads × CVR × wₘ.
  - A plan that changes cost per lead (Plans 3 and 4): spend = leads × cost per lead × (2 − wₘ).
  - Plan 1 changes nothing.
- Cost per new account = spend ÷ accounts.

Sample, Plan 1: revenue $24,028 in January rising to $665,924 in December, 299.57 accounts and $149,783 spend a month.

**Reforecast** (IY made again at the close of month kk: the 3+9, 6+6 and 9+3 that have happened, then the latest close)
1. The year = IY's months closed to kk ÷ PY's share of the year in those months.
2. What's left = the year − closed.
3. Spread what's left over the open months by the straight line from **this close's** January share: s₁′ = IY January ÷ the year. Each open month gets its line value ÷ the sum of the line over the open months.
4. New accounts: closed months as approved, open months the IY plan's count.
5. Spend: closed months as invested, open months the plan's accounts × IY's investment per new account.

Sample years: 3+9 $3.17M, 6+6 $3.40M, 9+3 $3.70M, October $3.76M.

---

### 1.2 Seasonal

**Step 1: Read the shape of one year.** IY's months (the closed months, with the open ones from Step 1) ÷ IY's full year.
- Above it, PY's months: IY's open months came from PY's share of the year in those months (1.1 Step 1). Sample: November and December were 28.8% of PY, so IY = $2,680,678 ÷ 71.2% = $3,763,377.
- "Plan, same shares" = target × those shares.
- "Spread evenly" = target ÷ 12.

**Step 2: Read every year together**
1. **Every full year on the book** (the first full year of billing to PY): each month ÷ that year's total.
2. **IY joins for its closed months:**
   - its forecast year = closed ÷ (the full years' average share, summed over months 1 to k)
   - its share = month ÷ that forecast year
   - Sample forecast year: $3,896,157.
3. **Average share:**
   - months 1 to k: (sum of the full years' shares + IY's share) ÷ (number of full years + 1)
   - months k+1 to 12: the full years' average
4. **High to low, points:** (highest − lowest share) × 100, IY included for its closed months.
5. **NY by month** = target × average share. Sample: January $29,239 … December $694,786, adding to $4,139,715.

**Next year's accounts and spend** (all of Chapter 1's next-year charts):
- accounts = Plan 1's accounts × PY's share of its accounts in the month
- spend = accounts ÷ Plan 1's CVR × Plan 1's cost per lead

**Reforecast:** as Straight Line's, except the open months take **the full years' average share** (PY and before, without IY's partial year) instead of the straight line.

---

### 1.3 Cohort

**What you'll need:** both dates on the revenue: approval month and billing month. That's CR(c, s), plus N(c).

**Step 1: Put both years on the grid.** For PY and for IY to the close:
- rows: approval months January–December
- cells: CR(c, s) where s is in the same year and s ≥ c
- the first column: N(c)
- "Billed in the month" (the column totals) is the NNIY row Straight Line started from

**Step 2: Read the age curve** (at the close; ages 0 to 11, where month 1 on the book is age 0)
1. **The 24-month curve:** over the last 24 approval months (close − 23 to the close), at each age a, sum CR(c, c + a) over the cohorts whose month c + a has closed ÷ sum of their N(c).
2. **Step 3's time of year** (next).
3. **The curve:** the same over the last **12** approval months (close − 11 to the close), with each CR(c, c + a) first divided by the time-of-year factor of calendar month c + a.

Sample:
- $110 in month 1, $218 in month 3
- $2,208 over the first 12 months

The guide also shows PY's January accounts (CR ÷ N, by age) and PY's June accounts the same way, as illustrations.

**Step 3: Read the time of year.** Over the same last 24 approval months, ages 0 to 11, every cell that has closed:
1. For each calendar month: billed = sum of CR in cells falling in that calendar month. Age alone says = sum of N(c) × the 24-month curve at that cell's age.
2. Factor = billed ÷ age alone says, then every factor ÷ the average of the twelve, so they average 1.00.

Sample: January 0.91, February 0.88 (−12%), December 1.07 (+7%).

**Step 4: Build next year**
- Cell (approval month m, billing month b ≥ m) = the plan's count for m × the curve at age (b − m) × the time-of-year factor for calendar month b.
- "Cohort build" = the column totals. Sample: **$4,417,021**, from 3,594.7 accounts.
- The guide sets Straight Line's target beside it, filled by this year's shares (1.2 Step 1).

**A cohort's level** (used whenever a cohort has started billing by the close)
- A cohort with at least two closed months in its first twelve runs at its own level: what it billed in those months ÷ what N(c) × curve × time of year said for them.
- With fewer than two closed months, the level is 1.

**Reforecast** (year y at the close; the curve and time of year are read again at that close)

For each approval month m of year y:
- **already approved by the close:** closed cells as billed; open cells N(c) × curve × time of year × the cohort's level
- **not approved yet:** the plan's count × curve × time of year

Sample IY totals: 3+9 $4.05M, 6+6 $3.97M, 9+3 $3.87M, October $3.88M.

---

### 1.5 Where net new in year lands you

NY three ways:

| Method | NY total |
|---|---|
| Straight Line (1.1 Step 1) | $4,139,715 |
| Seasonal (1.2 Step 2) | $4,139,715 |
| Cohort (1.3 Step 4) | $4,417,021 |

The 2026 year as it stood at each close comes from each method's Reforecast. On the three-ways chart, Straight Line's accounts and spend are Plan 1's spread evenly across the months.

### 1.6 Aside: when the better rate arrives

**Plans by month**
- accounts = plan accounts × PY's share of its accounts in the month
- leads = accounts ÷ CVR
- investment = leads × cost per lead
- revenue = the plan's revenue × IY's share of the year (1.2 Step 1)

**Evenly or weighted** (by approval month)
- PY revenue per account = what PY's month-m accounts billed inside PY ÷ N. Its average = PY's NNIY ÷ PY's accounts.
- scale = this year's revenue per new account (1.1 Step 2) ÷ that average
- planned accounts = plan accounts × PY's month share
- leads = planned accounts ÷ CVR
- accounts = leads × CVR × (wₘ, for a plan that changes CVR, if weighted)
- investment = leads × cost per lead × (2 − wₘ, for a plan that changes cost per lead, if weighted)
- revenue = accounts × PY revenue per account × scale

Sample, Plan 2 weighted: 3,591 accounts and $3,985.5K, against evenly's 3,595 and $4,139.7K.


---

## Chapter 2: Existing Book

The accounts already on the book when the year starts, as a layer cake. Each layer starts from the one before. Every rate comes only from years before the year being forecast.

### The book at a close (the prepare step makes these files)

**Who's in the book at close o:** every account approved by o that either billed more than zero in o, or was approved in the last three months (o − approval ≤ 2) and may not have billed yet.

**Status:** each approval month's accounts in the book are split into **billing** (billed more than zero in o) and **not billing** (approved in the last three months, nothing billed in o yet).

**The files:**
- `book_snapshots.csv` holds, for every close, by approval month and status:
  - accounts
  - revenue, billing accounts and volume in o
  - how many of the billing accounts were still billing twelve months later, and their revenue in o
- `book_followon.csv` holds, for every December close, what the same groups billed in each month of the next year.

**The book entering year Y** is its December Y−1 snapshot. Last year's new accounts are in it, because they were approved before January.

### 2.1 Straight Line

Chapter 1's Step 1, with the book you carry in.

**Step 1: Read every year the book came in.** For every year with a December before it:
- the December revenue and billing accounts
- the share of each that came from last year's new accounts
- what the same accounts billed next December

**Revenue kept** = next December ÷ December. **Accounts kept** = next December's billing accounts ÷ December's. This year's own next December hasn't billed: it is Step 2's forecast.

Sample: revenue kept between 84.6% and 87.2%, accounts kept between 74.5% and 76.1%, across 2021–2025. The average of every closed year's accounts kept, 75.3%, carries the billing accounts in Step 2.

**Step 2: Close out this year, add the new accounts, draw the line** (at month k). IY is the book entering this year, PY the book entering last year.

| Number | Formula | Sample |
|---|---|---|
| IY, the months closed | IY's months January to k, added up | $27,597,180 |
| The open months as a share of PY | PY: those months ÷ its year | 16.3% |
| IY, the full year | closed ÷ (1 − that share) | $32,958,209 |
| IY, December | the full year × PY's December share | $2,742,724 |
| This year's new accounts, December | Chapter 1's IY December: their months closed ÷ PY's share of them (Chapter 1's PY), × that PY's December share | $577,966 |
| NY's book comes in at | IY December + this year's new accounts | $3,320,689 |
| Bigger than IY's book | NY's book ÷ what IY's book came in at − 1 | +3.2% (÷ $3,218,096) |
| **Target, next year** | IY's full year × (1 + that) | **$34,008,926** |
| January as a share of IY | IY January ÷ IY's full year | 8.11% |
| NY's months | January = the target × that share; every month after adds (the target − 12 × January) ÷ 66 | $2,756,737, then +$14,062 |
| IY billing accounts, December | month k's × PY's December ÷ month k | 6,910 × 0.960 = 6,634 |
| This year's new accounts billing in December | Chapter 1's count (the months closed ÷ PY's share of them, rounded) × the share of last year's new accounts billing in December | 3,268 × 79.4% (2,581 of 3,250) = 2,595 |
| NY's book comes in with | the two added | 9,229 |
| NY's billing accounts | month m = start + (m/12) × (start × the average accounts kept − start) | 6,954 next December |

Where Chapter 1 has a goal, the existing book has how much bigger it comes in. 66 = 1 + 2 + … + 11.

**Reforecast** (IY at month kk; the December before it has closed, so the start is known)
- The months closed are what billed.
- The year = the months closed ÷ PY's share of those months. What's left goes on the open months by the straight line from this year's January share (Chapter 1's shares, rescaled to the open months).
- Billing accounts: the open months = the line's months × (the latest closed month's billing ÷ the line's).

### 2.2 Seasonal

**Step 1: Read each month as a share of its year.** For every closed year, each month's revenue ÷ the year. This year joins for its closed months, against the year it's on course for (its closed months ÷ the full years' average share of them). Average by calendar month: the months still open take the full years' average. Processing volume is read the same way, for comparison.

Sample average: February lowest, 7.9% of the year; May highest, 8.8% (the highest month in every year).

**Step 2: Fill Straight Line's year by the time of year.**
- Seasonal = Straight Line's target × each month's average share. The year doesn't change; only the months move.
- Billing accounts: Straight Line's.
- Sample year: **$34,008,926**.

**Reforecast:** the same year as Straight Line's at each close; the open months each take the full years' average share, rescaled to what's left.

### 2.3 Cohort

Every approval month in the book entering next year runs on its own.

**Its December:** month k's revenue × last year's December over month k for the same part (the accounts already on the book; this year's new accounts approved by month k; and, for each month still to be approved, the plan's count at last year's same-month cohort's December revenue per account approved). Then each part is scaled so it adds up to Step 2: the accounts already on the book to IY's December, this year's new accounts (approved and still to come) to Chapter 1's December. Billing accounts the same way. The cohorts add up to Step 2's $3,320,689.

**Age:** months from approval to the December the book enters from.

**Key** (which earlier cohorts it's read against): the age in months under 24. Above that, 24 + 12 × whole years over 24, capped at 120.

**The rates by key**, summed over every earlier year's December book, grouped by key:
- r0 to r3, for billing accounts: their December revenue (r0), next December revenue (r1), count (r2), and how many still billed next December (r3)
- r4 to r6, for not-billing accounts: count (r4), next December revenue (r5), and how many billed next December (r6)
- r7 and r8: what the billing accounts (r7) and the not-billing accounts (r8) billed over the year

**A group's year and billing accounts**, with s its December revenue (billing accounts), b its billing accounts and n its not-billing accounts:
- the year = s × r7/r0 + n × r8/r4
- billing accounts next December = b × r3/r2 + n × r6/r4
- If the key has no rows, or nothing to read for what the group holds (r0 = 0 with s > 0, or r4 = 0 with n > 0), it reads every key added together instead.

**A group's months:** month m = its year × Seasonal's average share for month m. Billing accounts: start + (m/12) × (next December − start).

Sample: **$33,902,893**. Next year's youngest cohort (this year's new accounts) is expected to bill 9.80 times its December; every older year's cohort 10.18 to 10.52 times.

**Reforecast:** each cohort's open months = its path × (its closed revenue ÷ its path's same months). Billing accounts are rescaled by the latest closed month.

### Where the existing book lands you

**Three layers of next year:** Straight Line $34.01M, Seasonal $34.01M, Cohort $33.90M.

**The check:** every closed year forecast from its own actual December, with the rates of the years before it, against what billed.
- Every layer's year came within 1.4% of what billed.
- Straight Line's months were off by 4.0% on average, Seasonal's by 0.9% and Cohort's by 0.7%.

---

## Chapter 3: Back Testing

### The whole book, three ways

For each method: Chapter 2's layer for next year + Chapter 1's net new in year for next year.

| Method | Whole book next year (sample) |
|---|---|
| Straight Line | $38,148,641 |
| Seasonal | $38,148,641 |
| Cohort | $38,319,915 |

### How the back test works

**The closes.** Stand at every month-end close from the first with 24 months of statements behind it (December 2021 on the sample) to the latest. At each one, make each method's forecast for the whole book using only what had closed that day.

**The split between net new and the existing book.** For a target month in year y:
- net new = accounts approved in year y
- existing book = accounts approved before year y

**The four methods, as run**

| Method | Net new | Existing book | Reaches |
|---|---|---|---|
| Straight Line | Chapter 1's Straight Line at the close. The rest of the year = (the months closed ÷ PY's share of them − closed), on the straight line from this close's January share. Next year = that year × (1 + goal), on the same line. | Chapter 2's Straight Line layer at the close | December of next year |
| Seasonal | The same totals. The rest of the year goes by the full years' average shares. Next year goes by the average shares with the year in progress in them (at a December close, every full year). | Chapter 2's Seasonal layer | December of next year |
| Cohort | The back test's own build at the close (below): this year's accounts approved by the close on the ladder, the rest at the plan's count as it stood then (see "The plan's count"). | Chapter 2's Cohort layer | 24 months |
| Trend line | None: a least-squares straight line through the whole book's last twelve monthly totals, carried forward. | | 24 months |

**Cohort net new at a close (`build_nniy` in the engine).** This reads the book in four ways that differ from Chapter 1's build. Chapter 1's Cohort is what a plan needs: a year from the curve. The back test asks what each build would have said at every past close, month by month, so it reads the accounts it can see from where they stand that day.

1. **The time of year.** The whole book's own index at the close, *I*. For every month with six closed months before it and five after, take that month ÷ the average of those twelve months. Average by calendar month, then scale the twelve to average 1.00. A calendar month with no reading yet stays at 1.00.
2. **This year's accounts approved by the close: the ladder.** Each approval month *c* of the close's year grows from what it billed at the close, on the path the 24 cohorts above it followed from the same age:
   - growth over *j* months = Σ over the 24 cohorts above (cohort *c − j − m* at month *o − j − m*, *m* = 0 to 23) of (billed *j* months later ÷ *I*) ÷ Σ of (billed that month ÷ *I*)
   - forecast for month *o + j* = billed at the close ÷ *I*(close month) × growth × *I*(month *o + j*)
   - Stop at the first statement month. No growth to read: 1.
3. **Accounts not approved yet.** The plan's count for their month (as it stood at the close) × dollars per account at their age × *I*. Dollars per account at age *a* (0 = the approval month): over the approval months *o − 23 − a* to *o − a* (from the first statement month on), Σ (billed at age *a* ÷ *I*) ÷ Σ accounts approved.
4. **The latest cohorts' pace** (the build's limit, below). In place of 3: each month not approved yet bills what one approval month of the last 24 billed at that age, on average, ÷ *I*, then × *I* for the target month. The accounts approved by the close are the same as in 2.

The guide made Chapter 3's Cohort lines with ABPRO_'s own engine, which adds refinements this repository leaves out. On the sample book these reads land within 0.03 points of those lines, and `check.py` reports those cells apart as close. Every printed table matches.

**How Chapter 2's layers run at a close (`legacy_at` in the engine)**
- **The year of the close:** the layer's Reforecast.
- **The next year:** from December, estimated at the close as in Straight Line's Step 2 (this year's book closed out, plus this year's new accounts; each cohort's part read from the close and scaled to it), or as closed if the close is a December.
- **Two years out:** each group's December a year on, aged a year (Straight Line and Seasonal: one group, at their December plus that method's net new forecast for the same December, and a year = the year before's × that start ÷ the year before's start). Next year's new accounts join as one young group, at the same method's net new forecast for that December.
- The rates come only from years whose December had closed.

**Which forecasts count.** A Cohort forecast (on the plan's count or at the latest cohorts' pace) counts only where the close had at least as many months of statements behind it as it reaches ahead. A distance is reported only where 12 or more closes stand behind it. Straight Line and Seasonal are shown to 12 months.

**Read each method by months ahead**
- miss = forecast ÷ what billed − 1
- **typical miss** = the average size of the miss, whichever way
- **band** = the average miss ± one standard deviation (sample standard deviation, n − 1)

**The year and the quarter.** From each planning close (the first close, then each plan-month close, for the year after it), each method's full year and quarters against what billed. Net new and the existing book are also shown separately.

**Where the miss comes from.** Each part's miss in points of the whole book's month: (part forecast − part actual) ÷ whole book actual.

**2026 so far.** Chapters 1 and 2's Reforecasts at the 3+9, 6+6 and 9+3, against what billed through the latest close. These use Chapter 1's own builds, not the back test's.

**The plan's count.** Cohort run again with the goal at 5% and at 15%, both for the net new count and inside Chapter 2's start (the accounts still to be approved). The guide runs this on Power Law. Sample, typical miss at 3, 12 and 24 months, then the average size of net new's full-year miss:
- goal at 5%: 1.3%, 3.7%, 1.6%; 6.8%
- goal at 10%, the guide's: 1.3%, 4.0%, 2.5%; 8.1%
- goal at 15%: 1.4%, 4.3%, 4.3%; 10.7%

**The latest cohorts' pace** (the limit of the build). Cohort with every account approved after the close at the latest cohorts' pace, instead of the plan's count. The guide runs this on Power Law.
- In net new: each month not approved yet, as in read 4 above.
- In the existing book: this year's months still to come join it at December revenue = what one approval month of the last 24 billed at their December age, on average, ÷ *I*, × *I*(December), in place of the plan's count in Chapter 2's start. Next year's new accounts join it two years out at this run's own net new forecast for that December.

Sample: at 24 months the plan's count runs 2.0% high on average and the latest pace 7.1% low. The typical miss at 24 months is 2.5% on the plan's count and 7.1% at the pace; at 12 months, 4.0% and 3.4%.

**Sample, typical miss on the whole book's month**

| Months ahead | 1 | 3 | 12 |
|---|---|---|---|
| Straight Line | 3.6% | 3.7% | 6.0% |
| Seasonal | 1.4% | 2.0% | 5.0% |
| Cohort | 0.6% | 1.3% | 4.0% |
| Trend line | 6.2% | 7.4% | 7.5% |

The trend line is 12.1% at 18 months. At 24 months Cohort misses by 2.5%.

---

## Which output file is which guide table

`engine/forecast.py` writes one CSV per guide table to `outputs/chapter-<n>/`, named `<chapter>-<section>-<method>_<step>__t<n>` for a table (`__v<n>c1` for a chart's numbers). The guide's copy of the same table is in `expected/chapter-<n>/` under the same name, and each `manifest.json` gives every table's title, tab and switch.

| File prefix | Guide |
|---|---|
| `1-1-straight-line_needs` · `_step-1` · `_step-2` · `_step-3` · `_step-4` · `_reforecast` | Chapter 1, Straight Line |
| `1-2-seasonal_step-1` · `_step-2` · `_next-year` · `_reforecast` | Chapter 1, Seasonal |
| `1-3-cohort_needs` · `_step-1-py` · `_step-1-iy` · `_step-2` · `_step-3` · `_step-4` · `_next-year` · `_reforecast` | Chapter 1, Cohort |
| `1-5-three-ways` · `_this-year-at-each-close` · `_chart` | Chapter 1, Where net new in year lands you |
| `1-6-aside_plans-by-month` · `_evenly-or-weighted` | Chapter 1, Aside |
| `2-0-existing-book_chart` · `2-1-straight-line_step-1` · `_step-2` · `_step-1-chart` · `_next-year` · `_reforecast` | Chapter 2, Straight Line |
| `2-2-seasonal_step-1` · `_step-2` · `_next-year` · `_reforecast` | Chapter 2, Seasonal |
| `2-3-cohort_step-1` · `_next-year` · `_reforecast` | Chapter 2, Cohort |
| `2-5-three-layers` · `_check` · `_this-year-at-each-close` | Chapter 2, Where the existing book lands you |
| `3-1-whole-book` · `_chart` | Chapter 3, The whole book, three ways |
| `3-2-every-projection` | Chapter 3, Every projection against what billed |
| `3-3-typical-miss` · `3-3-bands` | Chapter 3, The strength of each method |
| `3-4-year-and-quarter` · `3-5-where-the-miss-comes-from` · `3-6-this-year-so-far` · `_chart` | Chapter 3, The year and the quarter; Where the miss comes from; 2026 so far |
| `3-7-engine-limit` · `3-7-plan-sensitivity` | Chapter 3, Every method has limits (run on Cohort here, so not in `expected/`) |
