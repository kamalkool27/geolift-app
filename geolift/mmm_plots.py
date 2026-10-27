"""Matplotlib charts for the MMM tab."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .mmm import CHANNELS, CR

COL = {"search": "#1f77b4", "social": "#d62728", "display": "#7f7f7f", "ott": "#2ca02c"}


def contribution_chart(res):
    con = res.contributions()
    fig, ax = plt.subplots(figsize=(10, 3.6))
    stack = [np.median(con[c], 0) / CR for c in CHANNELS]
    ax.stackplot(res.df.date, stack, labels=CHANNELS, colors=[COL[c] for c in CHANNELS], alpha=0.8)
    ax.set_ylabel("INR Cr / week"); ax.set_title("Incremental Prime-member spend driven by each channel (posterior median)")
    ax.legend(loc="upper left", ncol=4, fontsize=8); fig.tight_layout(); return fig


def fit_chart(res):
    p = res.post
    n = p["n_train"]
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(res.df.date, res.df.y / CR, color="k", lw=1, label="actual")
    ax.plot(res.df.date[:n], np.array(p["fitted_train"]) / CR, color="tab:blue", lw=1, label="fitted (train)")
    ax.plot(res.df.date[n:], np.array(p["pred_test"]) / CR, color="tab:orange", lw=2, label=f"forecast (holdout, MAPE {p['holdout_mape']:.1f}%)")
    ax.axvline(res.df.date.iloc[n], ls="--", color="grey")
    ax.set_ylabel("INR Cr / week"); ax.set_title("Model fit and out-of-sample backtest"); ax.legend(fontsize=8)
    fig.tight_layout(); return fig


def roi_chart(roi):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    y = np.arange(len(roi))
    ax.errorbar(roi.roi_median, y, xerr=[roi.roi_median - roi.roi_lo, roi.roi_hi - roi.roi_median], fmt="o", color="k", capsize=4, label="MMM (94% CI)")
    ax.scatter(roi.true_roi, y, marker="x", color="tab:red", s=60, label="true (simulation)")
    ax.axvline(1, ls="--", color="grey"); ax.set_yticks(y, roi.channel); ax.set_xlabel("ROI (incremental revenue / spend)")
    ax.legend(fontsize=8); fig.tight_layout(); return fig


def response_chart(curves):
    fig, axes = plt.subplots(1, 4, figsize=(12, 3), sharey=False)
    for ax, c in zip(axes, CHANNELS):
        d = curves[curves.channel == c]
        ax.plot(d.spend / CR, d.resp_med / CR, color=COL[c])
        ax.fill_between(d.spend / CR, d.resp_lo / CR, d.resp_hi / CR, color=COL[c], alpha=0.2)
        ax.axvline(d.current.iloc[0] / CR, ls="--", color="k", lw=1)
        ax.set_title(c); ax.set_xlabel("weekly spend (Cr)")
    axes[0].set_ylabel("weekly incremental spend (Cr)"); fig.suptitle("Response (saturation) curves; dashed = current avg spend", fontsize=10)
    fig.tight_layout(); return fig


def adstock_chart(ad):
    fig, axes = plt.subplots(1, 4, figsize=(12, 2.8), sharey=True)
    for ax, c in zip(axes, CHANNELS):
        d = ad[ad.channel == c]
        ax.bar(d.lag, d.w_med, color=COL[c], alpha=0.7, label="posterior")
        ax.errorbar(d.lag, d.w_med, yerr=[d.w_med - d.w_lo, d.w_hi - d.w_med], fmt="none", color="k", lw=0.8)
        ax.plot(d.lag, d.w_true, "rx", label="true"); ax.set_title(c); ax.set_xlabel("weeks after spend")
    axes[0].set_ylabel("share of effect"); axes[0].legend(fontsize=7); fig.suptitle("Adstock carry-over (geometric decay)", fontsize=10)
    fig.tight_layout(); return fig
