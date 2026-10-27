"""Prime subscription geo-incrementality simulation (SIMULATED DATA, portfolio project).
Not real Amazon data and not work done at or for Amazon.

Question: does a festive Prime free-trial promo campaign cause incremental PAID Prime
subscriptions (trial->paid, retained at 30/90 days), or just extra free trials?
Design: 40 city geos, 20 get the promo for 6 weeks after 8 pre-weeks.
Estimator: log diff-in-diff with geo + week effects, cluster bootstrap over geos (numpy only).
Run: python scripts/prime_sub_sim.py
"""
import numpy as np

rng = np.random.default_rng(11)
G, PRE, POST = 40, 8, 6
T = PRE + POST
PRIME_FEE_YR = 1499.0        # ₹/yr annual plan (illustrative assumption)
MEMBER_YEARS = 3.0           # assumed avg paid tenure (illustrative)
MARGIN_SPEND = 2400.0        # ₹ incremental contribution/yr from extra shopping (illustrative)
LTV = (PRIME_FEE_YR + MARGIN_SPEND) * MEMBER_YEARS
SPEND_PER_GEO_WEEK = 4.0e5   # ₹ promo spend per treated city-week (illustrative)
TRUE = {"trials": 0.20, "paid_d30": 0.06, "retained_d90": 0.04}

base = rng.lognormal(np.log(3000), 0.5, G)
rates = {"trials": 1.0, "paid_d30": 0.35, "retained_d90": 0.28}
week = rng.normal(0, 0.03, T).cumsum() + np.linspace(0, 0.1, T)
treated = np.zeros(G, int); treated[rng.permutation(G)[:G // 2]] = 1
post = (np.arange(T) >= PRE).astype(int)

def panel(lifts):
    eff = treated[:, None] * post[None, :]
    return {k: base[:, None] * rates[k] * np.exp(week[None, :] + rng.normal(0, 0.05, (G, T)))
               * (1 + lifts[k] * eff) for k in rates}

def did(y, idx):
    ly = np.log(y[idx]); tr = treated[idx]
    d = ly - ly[:, :PRE].mean(1, keepdims=True)
    gap = d[tr == 1].mean(0) - d[tr == 0].mean(0)
    return np.exp(gap[PRE:].mean()) - 1

def estimate(y, B=2000):
    pt = did(y, np.arange(G))
    bs = np.array([did(y, rng.integers(0, G, G)) for _ in range(B)])
    return pt, np.percentile(bs, [3, 97]), (bs > 0).mean()

if __name__ == "__main__":
    p = panel(TRUE)
    print("SIMULATED DATA - Prime festive free-trial promo geo test (not real Amazon data)\n")
    for k, y in p.items():
        pt, ci, pr = estimate(y)
        print(f"{k:13s} lift {pt:+.1%} (94% CI {ci[0]:+.1%} to {ci[1]:+.1%}) P(lift>0)={pr:.0%}")
    y = p["retained_d90"]; pt, ci, _ = estimate(y)
    tot = y[treated == 1][:, PRE:].sum(); inc = tot - tot / (1 + pt)
    spend = SPEND_PER_GEO_WEEK * treated.sum() * POST
    print(f"\nincremental 90-day paid members ≈ {inc:,.0f}; spend ₹{spend/1e7:.2f} Cr")
    print(f"cost per incremental paid member ₹{spend/inc:,.0f} vs LTV ₹{LTV:,.0f} (assumed)")
    print(f"LTV iROAS ≈ {inc*LTV/spend:.2f}x; fee-only payback ≈ {spend/inc/PRIME_FEE_YR*12:.1f} months")
