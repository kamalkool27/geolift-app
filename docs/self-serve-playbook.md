# Self-serve playbook: how a marketer runs a lift test

> **Simulated portfolio project.** Written as an internal playbook for a fictional team; not real Amazon process.

Goal: any channel marketer can request, launch and read a geo lift test without waiting on analytics, while analytics keeps the guardrails.

## 1. Request template (copy into the tracker)
```
Test name:            e.g. "Display go-dark, Q1"
Owner (marketer):     
Question:             Is <channel/audience> incremental at current spend?
Decision it informs:  e.g. "Cut display by 50% if iROAS < 1.0"
Channel / audience:   
Outcome metric:       customer spend (₹) per city-week   [default]
Expected lift:        e.g. 5%   (if unknown, use the MMM ROI to estimate)
Test budget (₹):      
Cities / weeks:       from the Pre-test planner tab (power ≥ 80%)
Start / end dates:    
Conflicts checked:    no other geo test on these cities  [ ]
Decision rule:        written BEFORE launch (see §4)
```

## 2. Steps
1. **Size it:** open the app → *Pre-test planner*. Adjust cities, pre-weeks and test weeks until power ≥ 80% at your expected lift. If MDE > 2× your expected lift, don't run it; ask for a bigger test.
2. **Assign cities:** the app pairs cities by size and randomises. Don't hand-pick.
3. **Launch:** set geo-targeting in the ad platform. Log spend per city-week.
4. **Don't peek** for decisions before the planned end date.
5. **Analyse:** upload the city-week CSV (`date, geo, y, spend, treated`) in *Analyse test* and run.
6. **Read out** using §3 and file the result back into the tracker; analytics adds it to the MMM calibration set.

## 3. Guardrails (analytics enforces)
- ≥ 8 pre-period weeks (minimum 4); ≥ 4 test weeks; ≥ 20 cities total.
- No festive-week start unless the test is specifically about the festive period.
- Model checks must pass: r_hat < 1.01, ESS > 400, 0 divergences. If not, analytics reviews.
- Spend leakage: holdout cities must have < 5% of treated-city spend per capita.
- One change per test; no creative or bid changes mid-test.

## 4. How to read results
| output | what it means |
|---|---|
| Lift % (94% CI) | how much extra customer spend the ads caused |
| P(lift > 0) | probability the campaign helped at all |
| iROAS | ₹ incremental revenue per ₹1 ad spend |
| Counterfactual chart | what treated cities would have done without ads |

## 5. Decision rules (pre-registered defaults)
| result | action |
|---|---|
| P(lift > 0) < 90% | **Inconclusive.** Don't scale. Re-test bigger or accept current spend. |
| iROAS < 1 / contribution margin (breakeven) | **Cut** 25–50% and re-test. |
| iROAS between breakeven and 1.5× breakeven | **Hold** spend; optimise creative/targeting. |
| iROAS > 1.5× breakeven and CI lower bound > breakeven | **Scale** up to +30%, then re-test at the new level. |

Example (simulated, assuming an LTV-adjusted breakeven of 1.5x): Prime iROAS 1.07x → **cut**. Non-Prime 2.43x (CI 1.93–2.86x, > 2.25x) → **scale** carefully and re-test.
