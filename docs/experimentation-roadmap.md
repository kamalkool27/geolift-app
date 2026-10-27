# Channel experimentation roadmap (4 quarters)

> **Simulated portfolio project.** All figures are simulated and illustrative, not real Amazon data or work.

## How tests are ranked
**Priority score = expected value of information (EVI) ÷ cost.**
- **EVI** ≈ budget at stake × probability the test changes the decision × size of the ROI gap it could reveal.
- **Cost** = media held out (lost revenue in the holdout) + test media + analyst weeks.
- Budget at stake uses the simulated ₹6.68 Cr/week paid-media budget (≈ ₹350 Cr/year).

| rank | qtr | test | design | budget at stake (₹ Cr/yr) | P(changes decision) | EVI (₹ Cr) | cost (₹ Cr) | EVI ÷ cost |
|---|---|---|---|---|---|---|---|---|
| 1 | Q1 | Prime audience user-level holdout | 10% of Prime list excluded via Customer Match / DSP, 6 wks | 80 | 0.5 | 8.0 | 0.4 | **20x** |
| 2 | Q1 | Display go-dark | 10 of 40 cities dark, 6 wks | 60 | 0.6 | 5.4 | 0.3 | **18x** |
| 3 | Q2 | Brand-search holdout | 6-city brand keyword pause, 4 wks | 125 | 0.3 | 7.5 | 0.6 | **12.5x** |
| 4 | Q2 | Social scale-up (does 1.30x hold at +30%?) | geo, 20 vs 20 cities, 6 wks | 100 | 0.3 | 4.5 | 0.5 | 9x |
| 5 | Q3 | OTT/YouTube frequency cap test | geo, 3 frequency cells, 6 wks | 60 | 0.3 | 2.7 | 0.4 | 6.8x |
| 6 | Q3 | Pre-festive vs in-festive timing | geo, flighting test before Diwali | 350 | 0.1 | 3.5 | 0.7 | 5x |
| 7 | Q4 | Festive re-read: repeat geo test on the new mix | same design as original | 350 | 0.15 | 5.2 | 1.2 | 4.4x |

Rules that shape the calendar:
- **No overlapping geo tests** on the same cities; use the planner tab to check power (target ≥80% at the expected lift) before launch.
- **Q4 (festive) is for confirmation, not exploration**: biggest revenue, highest cost of being wrong.
- Every test has a pre-registered decision rule (see [playbook](self-serve-playbook.md)).

## When to recalibrate the MMM
Refit and recalibrate (`scripts/fit_mmm.py` with the new `add_lift_test_measurements`) when **any** of these is true:
1. **A new lift test lands** whose result falls **outside the MMM's 94% ROI interval** for that channel → recalibrate immediately.
2. **Holdout MAPE > 5%** on a rolling 13-week window (currently 1.4%).
3. **Spend mix moves >25%** on any channel vs the training range (curves are extrapolating).
4. **Calendar default:** quarterly refit; full recalibration with all lift tests before each festive budget lock.

If a lift test agrees with the MMM (inside the interval), add it as calibration data anyway; it narrows the interval at no cost.

- **Next festive window:** 7-day vs 30-day Prime trial geo test, read on day-90 paid members ([study](prime-subscription-study.md)).
