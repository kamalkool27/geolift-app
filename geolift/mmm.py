"""Media Mix Model (MMM) for the Amazon India festive-season paid-media case.

PRACTICE project on SIMULATED data. Not real Amazon data.

Target: weekly national Prime-member customer spend (INR).
Channels: search, social, display, ott (OTT/YouTube) weekly ad spend (INR).
Model: PyMC-Marketing MMM, geometric adstock + logistic saturation, Fourier yearly
seasonality, festive/sale event flags and a discount index as controls, calibrated
with the GeoLift Prime test via ``add_lift_test_measurements``.

Everything downstream of the fit (contributions, ROI, response curves, optimizer)
is computed in numpy from posterior draws of the adstock/saturation parameters, so
the app can load pre-fitted results from a small file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

CHANNELS = ["search", "social", "display", "ott"]
CONTROLS = ["diwali", "prime_day", "great_indian_festival", "discount_index"]
L_MAX = 8
CR = 1e7  # 1 crore INR
RESULTS_PATH = Path(__file__).resolve().parent.parent / "data" / "mmm_results.json"

# True data-generating parameters (known so we can check recovery).
# alpha = geometric adstock decay, lam = logistic saturation steepness on max-scaled spend,
# roi = target average ROI over the simulated period (incremental Prime spend / ad spend).
TRUE = {
    "search":  {"alpha": 0.20, "lam": 1.2, "roi": 2.6},
    "social":  {"alpha": 0.40, "lam": 0.8, "roi": 1.08},   # Prime-targeted social: low incrementality (matches GeoLift ~1.07x)
    "display": {"alpha": 0.30, "lam": 2.5, "roi": 0.7},
    "ott":     {"alpha": 0.65, "lam": 1.5, "roi": 1.8},
}

# GeoLift tab's Prime result (README sample): +3.0% lift, iROAS 1.07x (0.63-1.51x) on INR 1.57 Cr over 6 weeks.
GEOLIFT_PRIME = {"iroas": 1.07, "iroas_lo": 0.63, "iroas_hi": 1.51, "spend_cr": 1.57, "weeks": 6}


# ---------------------------------------------------------------- transforms
def geometric_adstock(x: np.ndarray, alpha: float, l_max: int = L_MAX, normalize: bool = True) -> np.ndarray:
    w = alpha ** np.arange(l_max)
    if normalize:
        w = w / w.sum()
    out = np.zeros_like(x, dtype=float)
    for i, wi in enumerate(w):
        out[i:] += wi * x[: len(x) - i]
    return out


def logistic_saturation(x, lam):
    return (1 - np.exp(-lam * x)) / (1 + np.exp(-lam * x))


# ---------------------------------------------------------------- simulation
def simulate(n_weeks: int = 156, seed: int = 7) -> tuple[pd.DataFrame, dict]:
    """~3 years of weekly national data. Returns (df, truth)."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-10-02", periods=n_weeks, freq="W-MON")
    t = np.arange(n_weeks)
    doy = dates.dayofyear.to_numpy()
    month, day = dates.month.to_numpy(), dates.day.to_numpy()

    # event flags (approximate calendar)
    gif = ((month == 10) & (day <= 21)) | ((month == 9) & (day >= 25))           # Great Indian Festival (late Sep-mid Oct)
    diwali = ((month == 10) & (day >= 22)) | ((month == 11) & (day <= 12))        # Diwali weeks
    prime_day = (month == 7) & (day >= 8) & (day <= 21)                           # Prime Day (mid-July)
    discount = np.clip(1 + 0.15 * gif + 0.1 * diwali + 0.12 * prime_day + rng.normal(0, 0.03, n_weeks), 0.9, 1.4)

    # channel spend (INR / week); flighted heavier in festive weeks
    festive = (gif | diwali | prime_day).astype(float)
    base = {"search": 2.0, "social": 1.6, "display": 1.0, "ott": 1.4}
    spend = {}
    for c in CHANNELS:
        s = base[c] * CR * (1 + 1.2 * festive + 0.25 * np.sin(2 * np.pi * doy / 365.25 + rng.uniform(0, 6)))
        s *= rng.lognormal(0, 0.25, n_weeks)
        if c == "ott":
            s *= (rng.uniform(size=n_weeks) > 0.25)  # OTT bursts on/off
        spend[c] = np.clip(s, 0, None)

    # contributions with chosen ROI
    truth = {"channels": {}}
    contrib = {}
    for c in CHANNELS:
        p = TRUE[c]
        xmax = spend[c].max()
        shape = logistic_saturation(geometric_adstock(spend[c] / xmax, p["alpha"]), p["lam"])
        scale = p["roi"] * spend[c].sum() / shape.sum()   # INR contribution per unit of saturated signal
        contrib[c] = scale * shape
        truth["channels"][c] = {**p, "xmax": float(xmax), "scale_inr": float(scale)}

    baseline = 180 * CR * (1 + 0.0015 * t) * (1 + 0.04 * np.sin(2 * np.pi * doy / 365.25) + 0.02 * np.cos(4 * np.pi * doy / 365.25))
    events = baseline * (0.22 * gif + 0.30 * diwali + 0.18 * prime_day) + 25 * CR * (discount - 1)
    y = baseline + events + sum(contrib.values())
    y = y * rng.lognormal(0, 0.015, n_weeks)

    df = pd.DataFrame({"date": dates, "y": y, **spend,
                       "diwali": diwali.astype(float), "prime_day": prime_day.astype(float),
                       "great_indian_festival": gif.astype(float), "discount_index": discount, "t": t.astype(float)})
    truth["contrib"] = {c: contrib[c].tolist() for c in CHANNELS}
    return df, truth


def lift_test_frame(df: pd.DataFrame, truth: dict, rng_seed: int = 3) -> pd.DataFrame:
    """Translate the GeoLift Prime test into a social-channel lift measurement.

    The geo test added ~INR 1.57 Cr of Prime-targeted (mostly social/Meta Custom Audience) spend over
    6 weeks; holdout cities got none. Scaled nationally, that is a step from x=0 (holdout) to delta_x
    = the typical festive weekly social spend (treated). delta_y is the true response of that step (consistent with iROAS ~1.07x), with the test's
    standard error as sigma.
    """
    c = truth["channels"]["social"]
    festive = df[(df.diwali + df.great_indian_festival) > 0]
    # geo holdout = ads OFF (x=0) vs ads ON at the festive weekly level (delta_x)
    x = 0.0
    delta_x = float(festive["social"].mean())
    # steady-state response (adstock normalised -> steady state equals x/xmax)
    f = lambda v: c["scale_inr"] * logistic_saturation(v / c["xmax"], c["lam"])
    delta_y = float(f(x + delta_x) - f(x))
    se = delta_y * (GEOLIFT_PRIME["iroas_hi"] - GEOLIFT_PRIME["iroas_lo"]) / (2 * 1.88 * GEOLIFT_PRIME["iroas"])
    return pd.DataFrame({"channel": ["social"], "x": [x], "delta_x": [delta_x], "delta_y": [delta_y], "sigma": [se]})


# ---------------------------------------------------------------- fit
def build_mmm():
    from pymc_marketing.mmm import MMM, GeometricAdstock, LogisticSaturation
    return MMM(date_column="date", channel_columns=CHANNELS, target_column="y",
               control_columns=CONTROLS + ["t"], adstock=GeometricAdstock(l_max=L_MAX),
               saturation=LogisticSaturation(), yearly_seasonality=2)


def fit_mmm(df: pd.DataFrame, lift: pd.DataFrame | None, holdout_weeks: int = 13,
            draws: int = 400, tune: int = 600, chains: int = 2, seed: int = 11):
    """Fit on all but the last `holdout_weeks` and return (mmm, train, test)."""
    df = df.copy()
    df["t"] = df["t"] / df["t"].max()
    df["discount_index"] = df["discount_index"] - 1.0
    train, test = df.iloc[:-holdout_weeks], df.iloc[-holdout_weeks:]
    X = train.drop(columns="y")
    mmm = build_mmm()
    mmm.build_model(X, train["y"])
    if lift is not None:
        mmm.add_lift_test_measurements(lift)
    mmm.fit(X, train["y"], draws=draws, tune=tune, chains=chains, random_seed=seed,
            progressbar=False, target_accept=0.9)
    return mmm, train, test


def _post(mmm, name):
    post = mmm.idata.posterior if hasattr(mmm.idata, "posterior") else mmm.idata["posterior"]
    da = post[name]
    da = da.stack(sample=("chain", "draw")).transpose("sample", ...)
    return np.asarray(da.values)


def extract(mmm, df: pd.DataFrame, train: pd.DataFrame, test: pd.DataFrame, n_keep: int = 400) -> dict:
    """Pull posterior draws + holdout predictions into a plain, JSON-able dict."""
    alpha = _post(mmm, "adstock_alpha")
    lam = _post(mmm, "saturation_lam")
    beta = _post(mmm, "saturation_beta")
    idx = np.linspace(0, len(alpha) - 1, min(n_keep, len(alpha))).astype(int)
    # scales used by the model (max-abs) — recompute from training data
    xmax = {c: float(train[c].abs().max()) for c in CHANNELS}
    ymax = float(train["y"].abs().max())
    # holdout prediction
    Xt = test.drop(columns="y")
    pred = _predict(mmm, Xt, ymax, include_last=True)
    mape = float(np.mean(np.abs(pred - test["y"].to_numpy()) / test["y"].to_numpy()) * 100)
    # in-sample fit
    fitted = _predict(mmm, train.drop(columns="y"), ymax)
    r2 = float(1 - np.sum((train.y - fitted) ** 2) / np.sum((train.y - train.y.mean()) ** 2))
    try:
        import arviz as az
        post = mmm.idata.posterior if hasattr(mmm.idata, "posterior") else mmm.idata["posterior"]
        rhat = float(max(float(np.nanmax(np.asarray(az.rhat(post[v]).to_array().values if hasattr(az.rhat(post[v]), 'to_array') else az.rhat(post[v]))))
                         for v in ["adstock_alpha", "saturation_lam", "saturation_beta"]))
    except Exception:
        rhat = float("nan")
    try:
        ss = mmm.idata.sample_stats if hasattr(mmm.idata, "sample_stats") else mmm.idata["sample_stats"]
        div = int(np.asarray(ss["diverging"].values).sum())
    except Exception:
        div = -1
    return {"alpha": alpha[idx].tolist(), "lam": lam[idx].tolist(), "beta": beta[idx].tolist(),
            "xmax": xmax, "ymax": ymax, "holdout_mape": mape, "r2_train": r2, "rhat_max": rhat, "divergences": div,
            "pred_test": pred.tolist(), "fitted_train": fitted.tolist(), "n_train": len(train), "n_test": len(test)}


def _predict(mmm, X: pd.DataFrame, ymax: float, include_last: bool = False) -> np.ndarray:
    pp = mmm.sample_posterior_predictive(X, extend_idata=False, combined=True, progressbar=False,
                                         include_last_observations=include_last)
    da = pp["y"] if "y" in pp else pp[list(pp.data_vars)[0]]
    arr = np.asarray(da.values)
    # mean over sample dim (whichever is not the date dim)
    date_axis = [i for i, s in enumerate(arr.shape) if s == len(X)][0]
    out = arr.mean(axis=tuple(i for i in range(arr.ndim) if i != date_axis))
    return out * ymax if out.mean() < 100 else out   # model predicts on max-abs scaled target


# ---------------------------------------------------------------- analysis (numpy only)
@dataclass
class MMMResults:
    df: pd.DataFrame
    truth: dict
    post: dict
    lift: pd.DataFrame
    meta: dict = field(default_factory=dict)

    @property
    def draws(self):
        return {k: np.asarray(self.post[k]) for k in ["alpha", "lam", "beta"]}

    def contributions(self) -> dict[str, np.ndarray]:
        """Posterior draws of weekly INR contribution per channel: {c: (S, T)}."""
        d = self.draws
        out = {}
        for j, c in enumerate(CHANNELS):
            x = self.df[c].to_numpy() / self.post["xmax"][c]
            out[c] = np.stack([self.post["ymax"] * d["beta"][s, j] *
                               logistic_saturation(geometric_adstock(x, d["alpha"][s, j]), d["lam"][s, j])
                               for s in range(len(d["alpha"]))])
        return out

    def roi_table(self) -> pd.DataFrame:
        con = self.contributions()
        rows = []
        for c in CHANNELS:
            roi = con[c].sum(1) / self.df[c].sum()
            lo, med, hi = np.percentile(roi, [3, 50, 97])
            true_roi = np.sum(self.truth["contrib"][c]) / self.df[c].sum()
            rows.append({"channel": c, "spend_cr": self.df[c].sum() / CR, "roi_median": med, "roi_lo": lo, "roi_hi": hi,
                         "true_roi": true_roi, "incr_revenue_cr": np.median(con[c].sum(1)) / CR,
                         "p_roi_gt_1": float((roi > 1).mean())})
        return pd.DataFrame(rows)

    def params_table(self) -> pd.DataFrame:
        d = self.draws
        rows = []
        for j, c in enumerate(CHANNELS):
            for p in ["alpha", "lam"]:
                lo, med, hi = np.percentile(d[p][:, j], [3, 50, 97])
                rows.append({"channel": c, "param": p, "true": self.truth["channels"][c][p],
                             "median": med, "lo": lo, "hi": hi,
                             "covered": bool(lo <= self.truth["channels"][c][p] <= hi)})
        return pd.DataFrame(rows)

    def response(self, c: str, weekly_spend: np.ndarray) -> np.ndarray:
        """Steady-state weekly INR response draws (S, len(spend)) to a constant weekly spend."""
        j = CHANNELS.index(c)
        d = self.draws
        x = np.asarray(weekly_spend)[None, :] / self.post["xmax"][c]
        return self.post["ymax"] * d["beta"][:, [j]] * logistic_saturation(x, d["lam"][:, [j]])

    def response_curves(self, n: int = 60, mult: float = 2.0) -> pd.DataFrame:
        rows = []
        for c in CHANNELS:
            cur = self.df[c].mean()
            grid = np.linspace(0, mult * self.df[c].max(), n)
            r = self.response(c, grid)
            eps = 0.01 * cur
            mr = (self.response(c, grid + eps) - r) / eps
            for i, g in enumerate(grid):
                rows.append({"channel": c, "spend": g, "resp_med": np.median(r[:, i]), "resp_lo": np.percentile(r[:, i], 3),
                             "resp_hi": np.percentile(r[:, i], 97), "mroi": np.median(mr[:, i]), "current": cur})
        return pd.DataFrame(rows)

    def marginal_roi_now(self) -> pd.DataFrame:
        rows = []
        for c in CHANNELS:
            cur = self.df[c].mean()
            eps = 0.01 * cur
            mr = (self.response(c, [cur + eps]) - self.response(c, [cur]))[:, 0] / eps
            rows.append({"channel": c, "avg_weekly_spend_cr": cur / CR, "mroi_median": np.median(mr),
                         "mroi_lo": np.percentile(mr, 3), "mroi_hi": np.percentile(mr, 97)})
        return pd.DataFrame(rows)

    def adstock_curves(self) -> pd.DataFrame:
        d = self.draws
        rows = []
        for j, c in enumerate(CHANNELS):
            for lag in range(L_MAX):
                w = d["alpha"][:, j] ** lag / np.sum(d["alpha"][:, [j]] ** np.arange(L_MAX), axis=1)
                tw = TRUE[c]["alpha"] ** lag / np.sum(TRUE[c]["alpha"] ** np.arange(L_MAX))
                rows.append({"channel": c, "lag": lag, "w_med": np.median(w), "w_lo": np.percentile(w, 3),
                             "w_hi": np.percentile(w, 97), "w_true": tw})
        return pd.DataFrame(rows)

    def optimize(self, total_weekly: float | None = None, bounds_pct: float = 0.5) -> pd.DataFrame:
        """Reallocate a fixed weekly budget across channels to maximise expected steady-state response.
        Each channel is limited to +/- bounds_pct of its current average weekly spend."""
        cur = np.array([self.df[c].mean() for c in CHANNELS])
        total = cur.sum() if total_weekly is None else float(total_weekly)
        d = self.draws
        bm = d["beta"].mean(0); lm = d["lam"].mean(0)
        xm = np.array([self.post["xmax"][c] for c in CHANNELS])

        def resp(z):  # z in crore
            return self.post["ymax"] / CR * np.sum(bm * logistic_saturation(z * CR / xm, lm))

        z0 = cur / CR * total / cur.sum()
        res = minimize(lambda z: -resp(z), z0, method="SLSQP",
                       bounds=[(max(0, (1 - bounds_pct) * v / CR), (1 + bounds_pct) * v / CR) for v in cur],
                       constraints=[{"type": "eq", "fun": lambda z: z.sum() - total / CR}])
        opt = res.x * CR
        rows = []
        for j, c in enumerate(CHANNELS):
            rc = self.response(c, [cur[j]])[:, 0]; ro = self.response(c, [opt[j]])[:, 0]
            rows.append({"channel": c, "current_weekly_cr": cur[j] / CR, "optimal_weekly_cr": opt[j] / CR,
                         "change_pct": (opt[j] / cur[j] - 1) * 100, "resp_current_cr": np.median(rc) / CR,
                         "resp_optimal_cr": np.median(ro) / CR})
        out = pd.DataFrame(rows)
        # uplift distribution
        tot_c = sum(self.response(c, [cur[j]])[:, 0] for j, c in enumerate(CHANNELS))
        tot_o = sum(self.response(c, [opt[j]])[:, 0] for j, c in enumerate(CHANNELS))
        up = tot_o - tot_c
        out.attrs["uplift_weekly_cr"] = [float(np.percentile(up, q)) / CR for q in (3, 50, 97)]
        out.attrs["p_uplift_gt_0"] = float((up > 0).mean())
        out.attrs["total_weekly_cr"] = total / CR
        return out

    def unit_economics(self, aov: float = 1500.0, margin: float = 0.25, ltv: float = 4000.0) -> pd.DataFrame:
        """Growth-metric framing: incremental orders, incremental CAC-style cost per incremental order and payback.
        aov = avg order value (INR), margin = contribution margin, ltv = contribution LTV of an incremental customer (INR)."""
        roi = self.roi_table()
        rows = []
        for _, r in roi.iterrows():
            inc_orders = r.incr_revenue_cr * CR / aov
            cpo = r.spend_cr * CR / inc_orders  # cost per incremental order
            margin_roi = r.roi_median * margin
            rows.append({"channel": r.channel, "incremental_orders_lakh": inc_orders / 1e5,
                         "cost_per_incremental_order": cpo, "margin_roi": margin_roi,
                         "ltv_to_icac": ltv / cpo,
                         "payback_orders": cpo / (aov * margin),  # incremental orders' margin needed to repay the ad cost
                         "profitable_on_margin": margin_roi >= 1})
        return pd.DataFrame(rows)


# ---------------------------------------------------------------- persistence
def run_pipeline(draws: int = 400, tune: int = 600, chains: int = 2, seed: int = 7, calibrate: bool = True) -> MMMResults:
    df, truth = simulate(seed=seed)
    lift = lift_test_frame(df, truth)
    mmm, train, test = fit_mmm(df, lift if calibrate else None, draws=draws, tune=tune, chains=chains)
    post = extract(mmm, df, train, test)
    return MMMResults(df, truth, post, lift, {"draws": draws, "tune": tune, "chains": chains, "calibrated": calibrate})


def save(res: MMMResults, path: Path = RESULTS_PATH):
    blob = {"df": res.df.assign(date=res.df.date.dt.strftime("%Y-%m-%d")).to_dict(orient="list"),
            "truth": res.truth, "post": res.post, "lift": res.lift.to_dict(orient="list"), "meta": res.meta}
    Path(path).write_text(json.dumps(blob))


def load(path: Path = RESULTS_PATH) -> MMMResults:
    b = json.loads(Path(path).read_text())
    df = pd.DataFrame(b["df"]); df["date"] = pd.to_datetime(df["date"])
    return MMMResults(df, b["truth"], b["post"], pd.DataFrame(b["lift"]), b.get("meta", {}))


def run_and_save(draws: int = 1000, tune: int = 1000, chains: int = 4, path: Path = RESULTS_PATH) -> MMMResults:
    """Fit calibrated + uncalibrated models; save the calibrated posterior and the uncalibrated ROI for comparison."""
    unc = run_pipeline(draws=draws, tune=tune, chains=chains, calibrate=False)
    res = run_pipeline(draws=draws, tune=tune, chains=chains, calibrate=True)
    res.meta["uncalibrated_roi"] = unc.roi_table()[["channel", "roi_median", "roi_lo", "roi_hi"]].to_dict(orient="list")
    res.meta["uncalibrated_mape"] = unc.post["holdout_mape"]
    save(res, path)
    return res
