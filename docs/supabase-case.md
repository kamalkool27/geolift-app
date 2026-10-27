# Applying the method to a PLG developer product: does Supabase-style dev content drive paid upgrades?

> **Simulated portfolio project.** Uses only public information about Supabase (linked below). Every number in the results is **simulated** by `scripts/supabase_sim.py`; none is real Supabase data, and I have no inside knowledge of Supabase's metrics.

## 1. Why the Amazon approach needs adapting
Supabase is product-led: developers sign up free, build, and upgrade an **organization** to Pro (from $25/month) or Team (from $599/month), with compute and usage billed on top ([pricing](https://supabase.com/pricing)). Growth is driven heavily by developer content: the [blog](https://supabase.com/blog), [YouTube channel](https://www.youtube.com/@Supabase), docs and [Launch Weeks](https://supabase.com/launch-week). The [Senior Data Analyst – Marketing JD](https://jobs.ashbyhq.com/supabase/59083a14-b2b6-4dd8-8037-739aa1ad1e22) asks for exactly this: attribution, incrementality and channel measurement for a PLG funnel.

Three differences from the retail case:
| | Amazon festive case (simulated) | Supabase-style PLG case |
|---|---|---|
| Outcome | customer spend (₹) this week | **paid upgrades / paid MRR**, lagged weeks–months after sign-up |
| Main lever | paid media | organic + amplified **content** (can't "turn off" a blog post) |
| Attribution trap | platform ROAS over-credits Prime buyers | self-reported "how did you hear about us" and last-touch credit the blog/docs page developers visit right before signing up |

## 2. Question and design
**Question:** does promoting developer content (YouTube tutorials + blog posts amplified with paid YouTube/social) cause extra **paid upgrades**, or only extra free sign-ups?

- **Unit:** 30 country/region geos (content itself is global, but *promotion* can be geo-targeted). 15 treated, 15 holdout, randomised.
- **Timing:** 8 pre-weeks, 6 promotion weeks; read upgrades again at +90 days because upgrades lag.
- **Outcomes:** (1) sign-ups, (2) new paid-org upgrades, (3) paid MRR. Upgrades are the decision metric.
- **Estimator:** log diff-in-diff with geo and week effects, cluster bootstrap over geos (the same model as the Amazon app, implemented in numpy for portability). The Bayesian app version takes the same CSV.
- **Value:** incremental upgrades × assumed LTV (avg paid-org MRR $60 × 24 months, an assumption) ÷ promotion spend.

## 3. Simulated results (`python scripts/supabase_sim.py`)
| metric | lift (94% CI) | P(lift > 0) |
|---|---|---|
| Sign-ups | **+12.6%** (+10.5% to +14.7%) | 100% |
| Pro upgrades | **+1.6%** (−1.8% to +5.1%) | 79% |

Incremental upgrades ≈ 22 on $27,000 (₹23.8 L) of promotion → cost per incremental upgrade ≈ $1,213 vs assumed LTV $1,440 → **LTV-based iROAS ≈ 1.19x**, with an interval that includes zero lift.

## 4. Decision
- Content promotion **clearly grows the free funnel** (+12.6% sign-ups) but the **upgrade effect is not yet proven** (P = 79%, below the 90% bar in the [playbook](self-serve-playbook.md)).
- **Don't scale paid amplification on the basis of sign-ups.** Hold spend, re-read upgrades at +90 days, and rerun with more geos or longer (the planner tab shows the power needed for a ~4% upgrade lift).
- Report content's value as a **funnel-stage metric** (sign-ups, activation) separately from its **revenue** impact, so last-touch blog credit doesn't drive the budget.

## 5. What I'd build next at a company like this
1. An **activation-weighted** outcome (sign-ups that create a project and hit the API in week 1) as a faster leading indicator of upgrades.
2. A **PLG MMM** with sign-ups → activation → upgrade stages, calibrated with these content lift tests, using the [recalibration rule](experimentation-roadmap.md#when-to-recalibrate-the-mmm).
3. **Launch Week** measurement via a pre/post synthetic control on non-promoted regions, since launches are global and can't be randomised.

## Sources (public)
- Supabase pricing: https://supabase.com/pricing
- Supabase blog: https://supabase.com/blog
- Supabase YouTube: https://www.youtube.com/@Supabase
- Supabase Launch Week: https://supabase.com/launch-week
- Job description: https://jobs.ashbyhq.com/supabase/59083a14-b2b6-4dd8-8037-739aa1ad1e22
