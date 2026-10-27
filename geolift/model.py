"""Bayesian diff-in-diff geo-lift model in PyMC (y = weekly customer spend, INR).
log(y[g,t]) = a_geo[g] + g_week[t] + tau * treated[g] * post[t] + eps,  lift = exp(tau) - 1
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az


@dataclass
class GeoLiftResult:
    lift: np.ndarray            # posterior draws of relative lift in customer spend
    weekly: pd.DataFrame        # date, actual, counterfactual, lo, hi, post (treated cities)
    actual: float               # actual customer spend in treated cities during the test (INR)
    spend: float                # campaign ad spend (INR)
    rhat: float
    ess: float
    divergences: int

    def summary(self) -> dict:
        cf = self.actual / (1 + self.lift)
        incr = self.actual - cf
        q = lambda x: np.percentile(x, [3, 50, 97])
        out = {
            "lift_pct": q(self.lift * 100),
            "p_lift_gt_0": float((self.lift > 0).mean()),
            "actual_revenue": self.actual,
            "counterfactual": q(cf),
            "incremental_revenue": q(incr),
            "spend": self.spend,
            "rhat_max": self.rhat, "ess_min": self.ess, "divergences": self.divergences,
        }
        if self.spend > 0:
            out["iroas"] = q(incr / self.spend)   # incremental revenue per INR of ad spend
        return out


def fit(panel: pd.DataFrame, draws: int = 1000, tune: int = 1000, chains: int = 2, seed: int = 1) -> GeoLiftResult:
    geo_idx, geos = pd.factorize(panel["geo"])
    t_idx, dates = pd.factorize(panel["date"], sort=True)
    y = np.log(panel["y"].to_numpy(float))
    D = (panel["treated"] * panel["post"]).to_numpy(float)
    with pm.Model():
        a_geo = pm.Normal("a_geo", y.mean(), 2.0, shape=len(geos))   # city baselines
        g_wk = pm.ZeroSumNormal("g_week", 0.5, shape=len(dates))     # shared weekly shocks (festive season)
        tau = pm.Normal("tau", 0, 0.2)                               # log-lift; weakly informative
        sigma = pm.HalfNormal("sigma", 0.3)
        pm.Normal("obs", a_geo[geo_idx] + g_wk[t_idx] + tau * D, sigma, observed=y)
        pm.Deterministic("lift", pm.math.exp(tau) - 1)
        idata = pm.sample(draws, tune=tune, chains=chains, random_seed=seed,
                          progressbar=False, compute_convergence_checks=False)
    post = idata.posterior
    lift = post["lift"].values.ravel()
    tau_d = post["tau"].values
    rhat = float(np.asarray(az.rhat(tau_d)).max()) if chains > 1 else float("nan")
    ess = float(np.asarray(az.ess(tau_d)).min())
    try:
        divs = int(idata.sample_stats["diverging"].values.sum())
    except Exception:
        divs = 0

    tr = panel[panel.treated == 1]
    wk = tr.groupby("date").agg(actual=("y", "sum"), post=("post", "max")).reset_index()
    qs = np.percentile(lift, [3, 50, 97])
    for name, l in zip(["hi", "counterfactual", "lo"], qs):
        wk[name] = np.where(wk.post == 1, wk.actual / (1 + l), wk.actual)
    tp = tr[tr.post == 1]
    return GeoLiftResult(lift, wk[["date", "actual", "counterfactual", "lo", "hi", "post"]],
                         float(tp.y.sum()), float(tp.spend.sum()), rhat, ess, divs)


def simulate_power(n_geos: int, pre: int, post: int, true_lift: float, noise: float = 0.05,
                   n_sims: int = 300, seed: int = 0) -> dict:
    """Fast power/MDE approximation via simulated DiD on log weekly revenue (50/50 city split)."""
    rng = np.random.default_rng(seed)
    T = pre + post
    hits, ests = 0, []
    nt = n_geos // 2
    for _ in range(n_sims):
        base = rng.normal(np.log(5e6), 0.6, n_geos)[:, None]
        wk = rng.normal(0, 0.1, T)[None, :]
        tr = np.zeros(n_geos); tr[:nt] = 1
        y = base + wk + rng.normal(0, noise, (n_geos, T))
        y[:nt, pre:] += np.log1p(true_lift)
        dg = y[:, pre:].mean(1) - y[:, :pre].mean(1)
        est = dg[tr == 1].mean() - dg[tr == 0].mean()
        se = np.sqrt(dg[tr == 1].var(ddof=1) / nt + dg[tr == 0].var(ddof=1) / (n_geos - nt))
        hits += est / se > 1.645
        ests.append(est)
    sd = float(np.std(ests))
    return {"power": hits / n_sims, "mde_pct": float((np.exp(2.49 * sd) - 1) * 100)}
