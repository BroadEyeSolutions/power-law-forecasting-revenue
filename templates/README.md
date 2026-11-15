# Templates

Each file has its column names and an example. Replace the example with your own rows, keep the column names, and save as CSV.

**Always**

| File | One row per | Columns |
|---|---|---|
| `settings.csv` | setting | `key`, `value` (the third column is a note). Required: `close`, your last month-end close (YYYY-MM), and `goal`, next year's growth from new accounts (0.10 = 10%). Optional, with defaults: `plan_cvr_change` (0.10), `plan_cost_per_lead_change` (−0.10), `weighted_phase_in` (0.10), `plan_month` (10: each year's plan is made at the October close). |
| `plan_inputs.csv` | month | `month`, `investment`, `leads`: last year in full and this year to the close, at least. |

**Your book, as account rows** (the engine's `--prepare` step builds the four files below from these)

| File | One row per | Columns |
|---|---|---|
| `accounts.csv` | account | `account_id`, `approval_month` |
| `billing.csv` | account, per month it billed | `account_id`, `billing_month`, `revenue` (what it billed that month, as on its statement), `volume` (processing volume, or another monthly size measure; only Chapter 2's Seasonal volume row reads it, so 0 is fine) |

**Or your book, as totals**

| File | One row per | Columns |
|---|---|---|
| `cohorts.csv` | approval month | `approval_month`, `accounts_approved` |
| `cohort_billing.csv` | approval month, billing month | `approval_month`, `billing_month`, `accounts_billing`, `revenue` |
| `book_snapshots.csv` | close, approval month, status | `as_of`, `approval_month`, `status` (`billing`, or `not billing`: in the book, not billing at the close), `accounts`, `revenue`, `billing_accounts`, `volume`, `stay_accounts`, `stay_revenue`. The book at a close: accounts approved by it that billed more than zero that month, or were approved in the last three months. |
| `book_followon.csv` | December close, approval month, status, month | `as_of` (a December), `approval_month`, `status`, `month`, `revenue`, `billing_accounts`, `volume`: what that December's groups billed in each month of the next year |

Months are always `YYYY-MM`. An account's approval month is the cohort this method uses: the month it was created in the system your revenue comes from, or its first billing month if that's earlier. `--prepare` sets it for you; in totals you set it yourself. Use account IDs, not names. Leave out every month after the close.

`book_snapshots.csv` needs these closes: every December, every Reforecast close (March, June and September of the year you're in, if closed), and the current close. `--prepare` writes every month-end close from the book's twelfth month on.
