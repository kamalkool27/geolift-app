"""Supabase-style PLG content-incrementality simulation (SIMULATED DATA, portfolio project).

Question: does geo-targeted promotion of developer content (YouTube tutorials + blog posts
amplified via paid social/YouTube) cause extra Free -> Pro upgrades, or just extra sign-ups?

Design: 30 country/region geos, 15 get content promotion for 6 weeks after 8 pre-weeks.
Outcomes per geo-week: new sign-ups, new paid org upgrades (Pro, $25/mo base, public pricing).
Estimator: log diff-in-diff with geo + week fixed effects, cluster bootstrap over geos (numpy only).
Run: python scripts/supabase_sim.py
"""
import numpy as np

rng = np.random.default_rng(7)
G, PRE, POST = 30, 8, 6
T = PRE + POST
USD_INR = 88.0                      # assumption for ₹ display
PRO_MRR = 60.0                      # assumed avg paid-org MRR: $25 Pro base + compute/usage (illustrative)
MONTHS_LTV = 24                     # assumed average paid lifetime (months), illustrative
TRUE_SIGNUP_LIFT, TRUE_UPGRADE_LIFT = 0.12, 0.04   # content drives sign-ups far more than upgrades

base_signups = rng.lognormal(np.log(900), 0.6, G)
upg_rate = rng.uniform(0.012, 0.025, G)
week = rng.normal(0, 0.04, T).cumsum() + np.linspace(0, 0.15, T)
treated = np.zeros(G, int); treated[rng.permutation(G)[:G // 2]] = 1
post = (np.arange(T) >= PRE).astype(int)
spend_per_geo_week = 300.0           # USD of promotion per treated geo-week (illustrative)

def panel(lift_s, lift_u):
    eff = treated[:, None] * post[None, :]
    s = base_signups[:, None] * np.exp(week[None, :] + rng.normal(0, 0.06, (G, T))) * (1 + lift_s * eff)
    # upgrades come from the existing free base too, not only this week's sign-ups
    u = base_signups[:, None] * upg_rate[:, None] * np.exp(week[None, :] + rng.normal(0, 0.08, (G, T))) * (1 + lift_u * eff)
    return s, u

def did(y, idx):
    ly = np.log(y[idx]); tr = treated[idx]
    d = ly - ly[:, :PRE].mean(1, keepdims=True)          # remove geo baseline
    gap = d[tr == 1].mean(0) - d[tr == 0].mean(0)        # remove shared weekly shocks
    return np.exp(gap[PRE:].mean()) - 1

def estimate(y, B=2000):
    pt = did(y, np.arange(G))
    bs = np.array([did(y, rng.integers(0, G, G)) for _ in range(B)])
    bs = bs[np.isfinite(bs)]
    return pt, np.percentile(bs, [3, 97]), (bs > 0).mean()

if __name__ == "__main__":
    s, u = panel(TRUE_SIGNUP_LIFT, TRUE_UPGRADE_LIFT)
    print("SIMULATED DATA - Supabase-style PLG content test (not real Supabase data)\n")
    for name, y in [("sign-ups", s), ("Pro upgrades", u)]:
        pt, ci, p = estimate(y)
        print(f"{name:13s} lift {pt:+.1%}  (94% CI {ci[0]:+.1%} to {ci[1]:+.1%})  P(lift>0)={p:.0%}")
    pt, ci, _ = estimate(u)
    base_upg = u[treated == 1][:, PRE:].sum() / (1 + pt)
    inc_upg = u[treated == 1][:, PRE:].sum() - base_upg
    spend = spend_per_geo_week * treated.sum() * POST
    ltv = PRO_MRR * MONTHS_LTV
    inc_value = inc_upg * ltv
    print(f"\nincremental upgrades ≈ {inc_upg:.0f}; promo spend ${spend:,.0f} (₹{spend*USD_INR/1e5:.1f} L)")
    print(f"cost per incremental upgrade ${spend/inc_upg:,.0f} vs Pro LTV ${ltv:.0f} (assumed)")
    print(f"LTV-based iROAS ≈ {inc_value/spend:.2f}x  (₹{inc_value*USD_INR/1e5:.1f} L value on ₹{spend*USD_INR/1e5:.1f} L spend)")
