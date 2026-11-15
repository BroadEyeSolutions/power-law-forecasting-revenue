# Power Law Forecasting: Revenue

**Broad Eye Solutions** · The working files behind the guide **Forecasting: Revenue** at [powerlawperformance.com/resources/forecasting-revenue/](https://powerlawperformance.com/resources/forecasting-revenue/).

The guide builds next year's revenue in three chapters:
1. **Net new in year:** next year's new accounts, built as **Straight Line**, **Seasonal** and **Cohort**, each reforecast as the months close: at the 3+9, the 6+6, the 9+3 and every month.
2. **The existing book:** the accounts already on the book, in the same three, as layers.
3. **Back testing:** the whole book three ways, then every method (and a trend line) made again at every past close, against what billed.

Each layer adds what the one before it left out, and each asks more of your data. The guide adds a fourth method, **Power Law**, which splits every cohort by tier. Power Law isn't in this repository.

This repository gives you three things:
- the same grids, as an Excel workbook and as CSV templates
- an engine that runs every step
- instructions an AI can follow to reproduce the guide's numbers, then make the same tables for your book

## What's here

| | What it is |
|---|---|
| `AI_INSTRUCTIONS.md` | Start here if you're handing this to an AI. It's also copied as `AGENTS.md` and `CLAUDE.md`, so assistants that look for those find it. |
| `METHOD.md` | Every calculation in the guide, step by step, with the sample book's answer after each. |
| `workbook/Forecasting-Revenue_Workbook.xlsx` | The guide's grids as Excel tabs with live formulas:<br>• Chapter 1 (tabs 1.x) and Chapter 2 (tabs 2.x)<br>• the whole book three ways (3.1)<br>Type your numbers on **Inputs** and **Inputs (book)** and every tab follows. The Reforecasts and the back test run in the engine. |
| `templates/` | Empty CSVs, one per input file, with the column names and an example row. |
| `data/sample/` | The guide's sample book, as totals by approval month and billing month, and the book at every close. Sample data: an invented payments portfolio, no client data, closed through October 2026. |
| `engine/` | The engine. `python3 engine/forecast.py` writes every guide table to `outputs/chapter-1/`, `chapter-2/` and `chapter-3/`. |
| `expected/` | The guide's own numbers for the sample book, copied from its Straight Line, Seasonal and Cohort tables. |
| `check.py` | Runs the engine on the sample book and compares every number with `expected/`. |
| `requirements.txt` · `LICENSE` | What Python needs (`pip install -r requirements.txt`), and the licence: MIT. |

**Status:** all three chapters are in. On the sample book, every printed table matches the guide, and chart lines are within 0.03 points. The engine lands on **5,623 of the guide's numbers with none off**:
- Chapter 1: 3,171
- Chapter 2: 1,143
- Chapter 3: 1,309

Another 33 cells, on Chapter 3's Cohort back-test chart lines, are close rather than exact: 0.025 points at most, and dollar amounts within 0.07%. The guide made those lines with ABPRO_'s own engine, which adds refinements this one leaves out.

The workbook's 12,386 formulas match the engine on every table they carry: 3,237 cells in 57 tables.

## Three ways to use it

**In Excel**
1. Open `workbook/Forecasting-Revenue_Workbook.xlsx`.
2. On **Settings**, set the months closed and your goal.
3. On **Inputs**, replace the numbers in the blue cells on yellow.
4. Read the tabs in order. Each block is headed with the guide step it reproduces.

**With Python** (3.9 or later, numpy and pandas; openpyxl for the workbook scripts: `pip install -r requirements.txt`)
```
python3 check.py                                       # the sample book against the guide
python3 engine/forecast.py --data mybook --out mybook/outputs --prepare     # your book: accounts.csv + billing.csv + settings.csv + plan_inputs.csv
```
`--prepare` turns your account rows into the cohort totals and the book at every close, written into `mybook/`. Every table is then written to `mybook/outputs/chapter-1/`, one CSV per guide table.

**With an AI**

Upload or connect this repository and ask it to follow `AI_INSTRUCTIONS.md`. It proves the method on the sample book first, then asks for your files.

## Your data

The guide needs two dates on every revenue number: the account's approval month, and the month it billed. The approval month is the cohort this method uses: the month the account was created in the system the revenue comes from.

- If you have account rows, use `templates/accounts.csv` and `templates/billing.csv` and let `--prepare` do the rest.
- If you don't have account rows, Straight Line and Seasonal still work in the workbook. They need net new revenue by month: what the accounts approved in a year billed in that year's months. Cohort needs the grid by approval month and billing month.

Use account IDs, not names: the method needs no customer or merchant names, MIDs or contact details, so remove them before you share files with anyone, an AI included. A book that bills annually or runs on a fiscal year: see "Books that aren't shaped like the sample" in `AI_INSTRUCTIONS.md`.

No client data is in this repository.

## Licence

MIT: use it, change it and share it, with the copyright notice kept. See `LICENSE`.
