# The sample book

The guide's book. **Sample data: an invented payments portfolio, no client data** (built so every total adds up and the method can be shown, for you to replace with your own book), closed through **October 2026**. Every number in the guide's Straight Line, Seasonal and Cohort tables comes from these files.

| File | Rows | What it holds |
|---|---|---|
| `settings.csv` | 6 | close 2026-10, goal 10%, the plan levers from Chapter 1, Straight Line, Step 3, and the plan month (October) |
| `plan_inputs.csv` | 82 | investment and leads by month, January 2020 to October 2026. **Illustrative:** $500 and 25 leads for every new account. |
| `cohorts.csv` | 178 | accounts approved by month. Months before 2020 are accounts approved earlier that still billed from January 2020. |
| `cohort_billing.csv` | 11,275 | revenue and accounts billing, by approval month and billing month, January 2020 to October 2026 |
| `book_snapshots.csv` | 10,294 | Chapter 2's book at every month-end close from December 2020, by approval month, billing or not billing: accounts, revenue, billing accounts, volume, and the billing accounts still billing a year later |
| `book_followon.csv` | 9,740 | every December's book, by approval month, billing or not billing, in each month of the next year |

These are totals by approval month, made from account rows that aren't included. The engine's own prepare step made them, so a book you prepare from account rows comes out in the same shape. In a sample book some of those totals are groups of one or two accounts.
