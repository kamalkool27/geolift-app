import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def counterfactual_chart(weekly):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(weekly.date, weekly.actual, label="Treated cities: actual customer spend", color="#ff9900", lw=2)
    p = weekly[weekly.post == 1]
    ax.plot(p.date, p.counterfactual, ls="--", color="#232f3e", label="Counterfactual (no ads)")
    ax.fill_between(p.date, p.lo, p.hi, color="#232f3e", alpha=0.15, label="94% CI")
    ax.axvline(p.date.min(), color="gray", ls=":")
    ax.set_ylabel("Weekly customer spend (INR)"); ax.legend(fontsize=8); fig.autofmt_xdate(); fig.tight_layout()
    return fig


def lift_posterior_chart(lift):
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.hist(lift * 100, 60, color="#ff9900", alpha=0.85)
    ax.axvline(0, color="red", ls="--", label="no effect")
    ax.axvline(np.median(lift) * 100, color="#232f3e", label="median")
    ax.set_xlabel("Lift in customer spend (%)"); ax.set_title("Posterior of lift"); ax.legend(); fig.tight_layout()
    return fig
