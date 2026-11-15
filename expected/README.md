# Expected: the guide's own numbers

The guide's Straight Line, Seasonal and Cohort tables, copied out of the guide's published pages exactly as printed, one CSV per table. Chart numbers are copied as the page carries them (two decimals).

`check.py` compares the engine's output for the sample book with these. A printed cell passes when the engine's number rounds to what the guide prints. A chart number passes when it's within 0.01.

`manifest.json` in each chapter folder lists every table: its title, the tab or switch it sits under, and the guide build it was copied from. If the guide is rebuilt, these files are copied again and the check is run against the new build.

**What isn't here.** The guide's fourth method, Power Law, isn't in this repository, so its tables, switches and rows are left out. So is the guide's Chapter 3.7: the guide runs the plan's count against the latest cohorts' pace on Power Law, and this repository runs the same test on Cohort (METHOD.md, Chapter 3). The engine still writes those two 3.7 tables; there is no guide table to check them against.

**Chapter 3's Cohort back-test lines.** Every printed table matches. The guide made these chart lines with its own engine, which adds refinements this repository leaves out; this repository reads the totals the way the guide describes (METHOD.md, Chapter 3). On the sample book that moves these lines by 0.03 points at most, and dollar amounts by 0.07% at most. So on these lines, and only there, `check.py` also passes a cell within 0.06 points (or 0.2%) of the guide's, and reports it apart as close. Anything further out fails.
