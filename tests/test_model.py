from geolift.data import load_sample, validate
from geolift.model import fit, simulate_power


def _lift(seg):
    p = validate(load_sample(), "2026-09-21", "2026-10-26", segment=seg)
    return fit(p, draws=200, tune=200, chains=2).summary()


def test_model_recovers_prime_vs_nonprime_lift():
    sp, sn = _lift("prime"), _lift("non_prime")
    assert 0 < sp["lift_pct"][1] < 7 and "iroas" in sp     # true simulated Prime lift 3%
    assert 4 < sn["lift_pct"][1] < 13 and sn["p_lift_gt_0"] > 0.95  # true non-Prime lift 8%
    assert sn["lift_pct"][1] > sp["lift_pct"][1]


def test_power_runs():
    out = simulate_power(40, 8, 6, 0.10, n_sims=50)
    assert 0 <= out["power"] <= 1
