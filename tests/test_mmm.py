import numpy as np
import pytest

from geolift import mmm as M


def test_adstock_and_saturation():
    x = np.zeros(10); x[0] = 1
    a = M.geometric_adstock(x, 0.5, l_max=4)
    assert a.sum() == pytest.approx(1.0) and a[1] == pytest.approx(a[0] * 0.5) and a[5] == 0
    assert M.logistic_saturation(0.0, 2.0) == 0 and M.logistic_saturation(100.0, 2.0) == pytest.approx(1.0)


def test_simulation_shape_and_truth():
    df, truth = M.simulate(n_weeks=156, seed=7)
    assert len(df) == 156 and set(M.CHANNELS + M.CONTROLS + ["date", "y"]) <= set(df.columns)
    assert (df[M.CHANNELS] >= 0).all().all() and (df.y > 0).all()
    for c in M.CHANNELS:
        roi = np.sum(truth["contrib"][c]) / df[c].sum()
        assert roi == pytest.approx(M.TRUE[c]["roi"], rel=1e-6)
    assert df.diwali.sum() > 0 and df.prime_day.sum() > 0 and df.great_indian_festival.sum() > 0


def test_lift_frame_matches_geolift_iroas():
    df, truth = M.simulate()
    lf = M.lift_test_frame(df, truth)
    assert list(lf.columns) == ["channel", "x", "delta_x", "delta_y", "sigma"]
    assert lf.delta_y[0] / lf.delta_x[0] == pytest.approx(M.GEOLIFT_PRIME["iroas"], abs=0.1)


@pytest.fixture(scope="module")
def res():
    return M.load()


def test_prefit_results_recover_truth(res):
    roi = res.roi_table()
    assert (roi.roi_lo <= roi.true_roi).all() and (roi.true_roi <= roi.roi_hi).all()
    assert res.params_table().covered.mean() >= 0.75
    assert res.post["holdout_mape"] < 5 and res.post["r2_train"] > 0.9


def test_calibration_pulls_social_toward_truth(res):
    unc = dict(zip(res.meta["uncalibrated_roi"]["channel"], res.meta["uncalibrated_roi"]["roi_median"]))
    cal = res.roi_table().set_index("channel").roi_median
    true = M.TRUE["social"]["roi"]
    assert abs(cal["social"] - true) < abs(unc["social"] - true)


def test_optimizer_keeps_budget_and_improves(res):
    o = res.optimize(bounds_pct=0.5)
    cur = sum(res.df[c].mean() for c in M.CHANNELS) / M.CR
    assert o.optimal_weekly_cr.sum() == pytest.approx(cur, rel=1e-4)
    assert (o.change_pct.abs() <= 50 + 1e-6).all()
    assert o.attrs["uplift_weekly_cr"][1] > 0


def test_curves_and_unit_economics(res):
    rc = res.response_curves(n=20)
    for c in M.CHANNELS:
        d = rc[rc.channel == c]
        assert np.all(np.diff(d.resp_med) >= -1e-6) and d.mroi.iloc[0] >= d.mroi.iloc[-1]
    ad = res.adstock_curves()
    assert ad.groupby("channel").w_med.sum().between(0.9, 1.1).all()
    ue = res.unit_economics(1500, 0.35, 4000)
    assert (ue.cost_per_incremental_order > 0).all()


@pytest.mark.slow
def test_quick_fit_runs():
    df, truth = M.simulate(n_weeks=104)
    mmm, train, test = M.fit_mmm(df, M.lift_test_frame(df, truth), draws=50, tune=50, chains=1)
    post = M.extract(mmm, df, train, test)
    assert len(post["pred_test"]) == 13 and np.array(post["alpha"]).shape[1] == 4
