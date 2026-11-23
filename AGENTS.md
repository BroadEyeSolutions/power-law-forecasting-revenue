# Instructions for an AI working with this repository

You've been given this repository, or connected to it, by someone who wants their business forecast the way the Broad Eye Solutions guide **Forecasting: Revenue** builds one ([powerlawperformance.com/resources/forecasting-revenue/](https://powerlawperformance.com/resources/forecasting-revenue/)). The repository holds the guide's method (`METHOD.md`), an engine that runs it (`engine/`), the guide's sample book (`data/sample/`), the guide's own printed numbers for that book (`expected/`), empty templates for their book (`templates/`), and an Excel workbook (`workbook/`).

Your job is to reproduce the guide's numbers on the sample book first, and then produce the same tables for their book. The repository carries the guide's Straight Line, Seasonal and Cohort methods and its trend line. The guide's fourth method, Power Law, isn't in it: if the user asks for Power Law, say so and point them to the guide.

## Read in this order

1. This file.
2. `METHOD.md`: every calculation, step by step, with the sample's answer after each.
3. `data/sample/README.md`: what each input file holds.
4. `engine/plf/chapter1.py`, `chapter2.py` and `chapter3.py`, if you can read code. Each function maps to a step in `METHOD.md`.

## Rules

1. **Prove it on the sample book first.** If you can run Python, run `python3 check.py` from the repository root. It runs the engine on `data/sample/` and compares every number with the guide. It writes the engine's tables to `outputs/`. If you mustn't write into the repository, use `python3 check.py --out <a scratch folder>`. Tell the user the count it prints (for example "5,623 cells match the guide, 0 do not"). If anything fails, stop and report what failed. Some cells on Chapter 3's Cohort back-test chart lines are listed separately as close (within 0.06 points). That's expected, and doesn't fail the check (`expected/README.md` says why). Don't work on their data until the sample matches.
2. **Use only what had closed.** Every forecast is made at a close (`close` in `settings.csv`). Never read a month after it.
3. **Follow `METHOD.md` exactly.** Don't swap in a different forecasting method, window, average or smoothing. If the user asks for something the guide doesn't do, say so, and keep it apart from the guide's tables.
4. **Don't round partway through.** The one rounding is the one `METHOD.md` names: this year's new-account count, in Straight Line, is whole accounts.
5. **Name every table by the guide step it reproduces**, for example "Chapter 1, Cohort, Step 4". That way the user can open the guide beside it.

## Putting the user's book in

Ask for, or find, the following, then lay it out like `templates/`.

**Settings** (`settings.csv`: `key,value`)
- `close` (required): their last month-end close, `YYYY-MM`. The guide reads its plan at an October close, the planning point. METHOD.md, "The plan's count", says why the close's month matters.
- `goal` (required): growth wanted from new accounts next year, as a fraction (0.10 = 10%)
- `plan_cvr_change` (default 0.10): Plan 2's change to the conversion rate
- `plan_cost_per_lead_change` (default −0.10): Plans 3 and 4's change to the cost per lead
- `weighted_phase_in` (default 0.10): how far under the plan a weighted change starts in January
- `plan_month` (default 10): the month whose close each year's plan is made at. The guide plans at the October close.

**Plan inputs** (`plan_inputs.csv`): investment and leads by month, for last year in full and this year to the close at least. The guide's sample is illustrative here ($500 and 25 leads a new account). Use the user's real figures.

**Account IDs, not names.** The method needs no customer or merchant names, MIDs, addresses or contact details. Ask the user to remove them, or swap them for anonymous IDs, before they share any file with you.

**The approval month** is the cohort this method uses: the month the account was created in the system the revenue comes from, or the month it first billed if that's earlier. It starts each account's age, so every account needs one.

**The book**, one of two ways:
- **Account rows (best).** `accounts.csv` (account_id, approval_month) and `billing.csv` (account_id, billing_month, revenue, volume: one row per account per month it billed). Put them in a folder with `settings.csv` and `plan_inputs.csv`, then run `python3 engine/forecast.py --data <folder> --out <folder>/outputs --prepare`.
  - The prepare step writes `cohorts.csv`, `cohort_billing.csv`, `book_snapshots.csv` and `book_followon.csv` into that folder, replacing any already there.
  - It sets each account's approval month to the earlier of approval and first billing, so `accounts.csv` can hold the recorded approval month.
  - The engine then writes every table to `--out`. Without `--out` it writes to the repository's `outputs/`, so give each book its own `--out`.
- **Totals already made.** `cohorts.csv` and `cohort_billing.csv` (Chapter 1), plus `book_snapshots.csv` and `book_followon.csv` (Chapters 2 and 3), in the shapes in `templates/`. Then run `python3 engine/forecast.py --data <folder> --out <folder>/outputs`. In this case you make the approval month the earlier of approval and first billing yourself. `book_snapshots.csv` needs these closes (`as_of`): every December, every Reforecast close (March, June and September of IY if they have closed), and the current close.

**Check the book before you run it**
- **Revenue is in dollars** (or their currency), not cents.
- **One row per account per billing month.**
- **The approval month is the earlier of approval and first billing.**
- **No month after the close.** This year's open months are left out, not filled with zeros.
- **Enough history.** In practice, two full years before this one (IY−2 and PY) plus IY to the close:
  - Seasonal reads every full year of billing on the book.
  - The IY plan's count, which every Reforecast uses, needs IY−2's approvals in full.
  - The 3+9 Reforecast reads 24 approval months back from March of IY, which is April of IY−2.

**Books that aren't shaped like the sample**
- **A fiscal year.** The engine's years run January to December, and there's no fiscal-year setting yet. Run it on calendar years and tell the user so. If their goal is set for a fiscal year, use it as the calendar year's goal and say so, unless they give you one for the calendar year.
- **Billing that isn't monthly.** Revenue is what each account billed in the month. If customers pay for a year (or a quarter) up front, one month carries the whole payment. Spread each payment over the months it covers before you run it, leave out the part that covers months after the close, and tell the user you did.
- **Accounts bought or moved in.** Accounts bought from another company, or moved in from another system, aren't net new: they were won somewhere else. Their recorded approval month is often the month they were moved in, which would count them as that month's new accounts. Give them an approval month before the book's first billing month (or their real original months, if the user has them), so they sit in the existing book from the month they joined, and tell the user you did. Two things then look off, and both are expected. In Chapter 2's Straight Line, Step 2 ("NY's book comes in at: IY December + this year's new accounts"), the book that came in after the purchase is bigger than the December before it plus that year's new accounts, by what the bought accounts billed that December. And the back test misses low at closes before the purchase, because no close before it could know it was coming.
- **Less history than the list above.** If the engine can't make a table from the history there is, report which tables and why. Don't fill in missing years.

**No code?** If you can't run Python, work through `METHOD.md` by hand from the same files. Or set the Excel workbook's **Settings** tab (months closed, the year you're in, the goal), fill its **Inputs** tab (blue cells on yellow) and read its tabs. The workbook carries every Chapter 1 table except the Cohort Reforecast, which only the engine runs.

## What to give the user

- **Next year's new accounts three ways** (Chapter 1): Straight Line, Seasonal and Cohort, by month and in total.
- **The existing book three layers** (Chapter 2), and **the whole book three ways** (Chapter 3: the two added).
- **The back test** (Chapter 3): each method's typical miss and band by months ahead, and its year and quarter misses on the user's own history, with the trend line beside them. That's how the user sees which method to trust for their book, and how far ahead.
- **This year as it stands:** each method's Reforecast at the 3+9, 6+6 and 9+3 that have closed, and at the latest close.
- **The steps behind them:** the target, the count and its price (Straight Line Steps 1–3), the average shares (Seasonal Step 2), and the age curve and time-of-year factors (Cohort Steps 2 and 3).
- **What you assumed:** the close, the goal, and any data you had to fix.

The output CSVs write shares, rates and goals as percent numbers (28.77 = 28.77%). The workbook (Chapters 1 and 2, and the whole book) holds them as Excel percentages. The Reforecasts and the back test run only in the engine.

## Checks on their numbers

These hold on any book. If one fails, something in the input is wrong.

- **Straight Line's next year** adds up to this year's full year × (1 + goal), and its months rise by the same step each month.
- **Seasonal's average shares** add up to 100%.
- **The time-of-year factors** average 1.00.
- **The Cohort build's accounts** equal the plan's count (this year's **unrounded** count × (1 + goal); Straight Line's is rounded), and every row of its grid starts in its own approval month.
- **In every Reforecast**, the closed months equal what billed.
- **Chapter 2's Straight Line** adds up to its target (this year's full year × next year's book ÷ this year's book), and **Seasonal's** year equals Straight Line's.
- **The whole book** for each method equals its existing book plus its net new, month by month.

## What this repository doesn't do

- **It runs only the guide's method.** Anything outside the guide, such as account close dates or pipeline-fed new accounts, isn't in the engine, and shouldn't be added to it in the user's name.
