# Prime subscription study: does a festive free-trial promo create paid Prime members, or just trials?

> **Simulated portfolio project by Kamaleshwaran K.** Every number is **simulated** by `scripts/prime_sub_sim.py`. Not real Amazon data and not work done at or for Amazon. Fee, LTV and spend figures are **illustrative assumptions**.

## 1. Question
A festive Prime sign-up push (free-trial promo across paid social, display and app banners) reliably lifts free trials. The business question is whether it causes **incremental paid subscriptions**: trial-to-paid conversion at day 30 and retained members at day 90.

## 2. Design (geo test, same method as the GeoLift app)
- 40 city geos; 20 randomly get the promo for 6 weeks after an 8-week pre-period; 20 are holdout.
- Outcomes per city-week: free trials started, paid at day 30, still paid at day 90.
- Estimator: log diff-in-diff with geo and week effects, cluster bootstrap over cities (94% intervals). The Bayesian GeoLift model in `geolift/` gives the same read on the same panel.
- Primary metric: **day-90 retained paid members** (decided before the test, so trials can't be cherry-picked).

## 3. Simulated results
| Outcome | Lift | 94% interval |
|---|---|---|
| Free trials | +21.1% | +19.5% to +22.7% |
| Paid at day 30 | +7.2% | +5.5% to +9.0% |
| Retained at day 90 | +3.1% | +1.3% to +4.9% |

- ≈ 3,600 incremental day-90 paid members on ₹4.80 Cr of promo spend → **₹13,300 per incremental member**.
- Assumed LTV ₹11,700 (₹1,499/yr fee + ₹2,400/yr incremental shopping margin × 3 years) → **LTV iROAS ≈ 0.88x**; fee-only payback ≈ 107 months.
- Read: the promo is real, but most extra trials churn. Judged on trials it looks like a win; judged on paid retention it loses money.

## 4. Action taken (simulated)
- **Decision:** do not scale the blanket promo. Cut festive trial-promo budget from ₹4.80 Cr to ₹2.0 Cr (−₹2.8 Cr) and move ₹1.5 Cr into search and OTT (higher ROI in the MMM tab); hold ₹1.3 Cr back.
- **Targeting:** keep the promo only in the top-third cities by day-90 conversion; stop broad paid social trial ads.
- **Trial change:** test a 7-day trial (vs 30-day) with an annual-plan offer at day 5, aimed at intent, not volume.
- **Scorecard change:** the campaign KPI is now day-90 retained paid members and cost per retained member, not trials.
- **Guardrails:** stop if day-30 paid conversion in promo cities drops below holdout, if cancellation complaints rise >10%, or if non-Prime spend falls in test cities.
- **Follow-up test:** 7-day vs 30-day trial geo test next festive window, read at day 90; feed the result into the MMM as a lift calibration.
