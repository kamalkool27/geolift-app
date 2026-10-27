# Decision memo: reallocate festive paid media away from Prime-targeted social and display

> **Simulated portfolio project.** All data is simulated. This is not real Amazon data and not work done at or for Amazon. The memo shows how I would write up the findings for a marketing leadership audience.

**To:** VP Marketing, India (fictional) · **From:** Marketing Analytics · **Decision needed by:** budget lock for the next festive flight

## 1. Recommendation
Move **₹1.55 Cr/week** (23% of the ₹6.68 Cr weekly paid-media budget) **out of social and display and into search and OTT**, and **cap Prime-targeted spend** at the current level until a user-level holdout confirms the geo result. Total budget stays flat. Modelled gain: **≈ +₹2.4 Cr/week of incremental Prime-member spend** (94% CI ₹0.5–4.2 Cr; P > 0 ≈ 99%), roughly +20% on the same budget.

| channel | now (₹ Cr/wk) | proposed (₹ Cr/wk) | change | calibrated ROI |
|---|---|---|---|---|
| Search | 2.41 | 3.61 | +50% | 2.96x |
| OTT / YouTube | 1.19 | 1.53 | +28% | 2.10x |
| Social | 1.91 | 0.95 | −50% | 1.30x (platform/uncalibrated MMM said 3.30x) |
| Display | 1.18 | 0.59 | −50% | 0.54x |
| **Total** | **6.68** | **6.68** | 0 | |

Moves are capped at ±50% per flight because the response curves outside the observed spend range are extrapolation.

## 2. Evidence
1. **Geo holdout (40 cities, 20 treated, 8 pre + 6 test weeks):** Prime-member spend lifted **+3.0%** (94% CI 1.8–4.3%), **iROAS 1.07x**. Non-Prime lifted **+6.9%**, **iROAS 2.43x**. Prime members buy in the festive sale anyway, so ads to them are mostly non-incremental.
2. **Media mix model (≈3 years weekly, PyMC-Marketing, adstock + saturation):** calibrated with the geo test. Holdout MAPE **1.4%** on the last 13 weeks.
3. **Calibration changed the answer:** without the lift test, the MMM credited social with **3.30x** ROI. Anchored to the experiment, it is **1.30x**. That is the single biggest budget-relevant finding.

## 3. Risks and how we manage them
| risk | mitigation |
|---|---|
| Geo test is aggregate; Prime vs non-Prime split could be confounded by city mix | User-level randomised holdout on the Prime audience (next test #1) |
| Search ROI may be partly brand demand we'd capture organically | Brand-search holdout in 6 cities (next test #2) |
| Response curves extrapolate beyond observed spend | ±50% cap; re-read MMM after 4 weeks |
| Social cut hurts upper-funnel reach that shows up later | Track new-customer share and 90-day repeat; reverse if new-customer acquisition drops >10% |
| ROI is revenue-based, not profit | Compare to margin-adjusted breakeven (1 ÷ contribution margin) before scaling search further |

## 4. Next tests (see [experimentation roadmap](experimentation-roadmap.md))
1. User-level Prime holdout (10% of Prime list excluded) — confirms or kills the Prime cap.
2. Brand-search geo holdout — checks how much of search's 2.96x is truly incremental.
3. Display go-dark in 10 cities — confirms the 0.54x before cutting further.

**Ask:** approve the reallocation for the next flight, plus ₹0.3 Cr/week of test budget for tests 1–3.
