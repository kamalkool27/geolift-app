from geolift.data import load_sample, validate
from geolift.model import fit, simulate_power

def test_model_smoke_recovers_lift():
    p = validate(load_sample(), "2026-09-21", "2026-10-26")
    r = fit(p, draws=200, tune=200, chains=2)
    s = r.summary()
    assert 0 < s["lift_pct"][1] < 20 and s["p_lift_gt_0"] > 0.9 and "iroas" in s

def test_power_runs():
    out = simulate_power(40, 8, 6, 0.10, n_sims=50)
    assert 0 <= out["power"] <= 1
