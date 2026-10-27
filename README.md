# GeoLift: Is Paid Media to Amazon Prime Members Incremental? (Bayesian, PyMC)

> **Disclaimer: this is a practice / portfolio project.** All data is **simulated**. It is **not** real Amazon data, and it is **not** work done at or for Amazon. "Amazon India festive sale" is only a realistic framing for the case study.

## The business question
**Is paid media to Prime members incremental, or are we paying for sales we'd get anyway?**

Amazon India runs a **regional paid-media campaign** (search, social, display, OTT) ahead of its festive sale, targeted mainly to **Prime-member audiences** (hashed Prime lists via Customer Match / Custom Audiences / Amazon DSP). Ad platforms report strong ROAS, but Prime members are high-intent and shop heavily in the festive sale anyway, so platform ROAS over-credits ads most for exactly this group. **How much extra Prime-member spend (₹) did the campaign actually cause, and was it worth the ad spend?** A smaller non-Prime ad set runs alongside it for comparison.

**Design:** a geo holdout test. 40 Indian cities are paired by size and randomised, so 20 cities run the campaign (treated) and 20 don't (holdout). There are 8 pre-period weeks and 6 campaign weeks. The outcome is weekly **Prime-member customer spend (₹)** per city; the app's segment toggle switches to non-Prime spend.

## What the app does
A Streamlit app with two tabs:
- **Analyse test:** choose the customer segment (**Prime** by default, or non-Prime), upload a city-week panel or use the bundled simulated sample. Pick the campaign start and end dates (and the treated cities if there's no `treated` column), then fit a Bayesian diff-in-diff model in PyMC. Outputs:
  - Lift % in customer spend, with a 94% credible interval and P(lift > 0)
  - **Incremental revenue (₹)** and **iROAS** (incremental revenue ÷ ad spend)
  - Charts: treated-city actual spend vs the no-campaign counterfactual, and the posterior of lift
  - A plain-English readout and decision
  - Convergence diagnostics (r_hat, ESS, divergences)
  - A downloadable results CSV
- **Pre-test planner:** simulated power and minimum detectable effect (MDE) for a given number of cities, weeks and expected lift.

![Actual vs counterfactual](docs/counterfactual.png)
![Lift posterior](docs/lift_posterior.png)

### Sample results (simulated data; true lift Prime 3%, non-Prime 8%)
| segment | lift (94% CI) | P(lift > 0) | incremental revenue | ad spend | iROAS |
|---|---|---|---|---|---|
| **Prime members** (default) | **+3.0% (1.8–4.3%)** | ~100% | ₹1.69 Cr | ₹1.57 Cr | **1.07x (0.63–1.51x)** |
| Non-Prime customers | +6.9% (5.4–8.2%) | ~100% | ₹2.56 Cr | ₹1.05 Cr | 2.43x (1.93–2.86x) |

**Readout:** the campaign does lift Prime spend, but only ~3%. Each ₹1 of Prime-targeted ads returns about ₹1.07 of incremental revenue, which is below a margin-adjusted breakeven, so most Prime festive purchases would have happened anyway. Non-Prime audiences are far more incremental (~2.4x). Recommendation: cut or cap Prime-targeted spend and shift budget toward non-Prime / new-customer audiences.

### Next step
Geo tests are noisy and aggregate. Validate the Prime finding with a **user-level randomised holdout**: upload the Prime member list as a Customer Match / Custom Audience (or use Amazon DSP Prime audiences), randomly exclude e.g. 10% as a holdout, and compare per-member spend between exposed and holdout groups. Use the result as a prior to calibrate a media mix model.

## Input schema (CSV, long format: one row per city per week)
| column | required | description |
|---|---|---|
| `date` | yes | week start date (YYYY-MM-DD) |
| `geo` | yes | city / region name |
| `y` | yes | customer spend in that city-week (₹, > 0); in the sample, Prime-member or non-Prime spend |
| `segment` | optional | customer segment, e.g. `prime` / `non_prime` (one row per city-week-segment). If present, pick the segment in the app (default `prime`) |
| `spend` | optional | campaign ad spend in that city-week (₹). Needed for iROAS (or enter a total in the sidebar) |
| `treated` | optional | 1 = campaign city, 0 = holdout (constant per city). If missing, select the treated cities in the UI |

Validation gives clear errors for an unknown or unselected segment, missing columns, non-numeric or non-positive `y`, duplicate rows, an unbalanced panel, fewer than 4 pre-period weeks (8–12 recommended), and having no treated or no holdout cities.

## Method
log(y[g,t]) = α_g + γ_t + τ · treated_g · post_t + ε, where ε ~ Normal(0, σ)

- α_g: city baselines. γ_t: shared weekly shocks (ZeroSumNormal), which absorb the festive-season ramp that hits all cities.
- τ: log-lift with a weakly informative prior Normal(0, 0.2). Lift = e^τ − 1.
- Counterfactual = actual treated spend ÷ (1 + lift). Incremental revenue = actual − counterfactual. iROAS = incremental revenue ÷ ad spend.
- Sampled with NUTS (2 chains, 300–1000 draws), cached in the app, and runs in seconds.
- Decision rule: iROAS is revenue-based. Compare it to a margin-adjusted breakeven (1 ÷ contribution margin) before scaling.

## Run locally
```bash
git clone https://github.com/kamalkool27/geolift-app.git && cd geolift-app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py      # opens http://localhost:8501
pytest -q                 # validation tests + fast model smoke test
```

## Structure
```
app.py                    Streamlit UI
geolift/data.py           loading + validation
geolift/model.py          PyMC model, metrics, power simulation
geolift/plots.py          charts
data/sample_geo_panel.csv simulated festive-campaign panel (40 cities x 14 weeks x 2 segments)
scripts/make_sample.py    regenerates the simulated sample
tests/                    pytest
```

MIT License.
