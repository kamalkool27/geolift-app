"""Streamlit 'Media Mix Model' tab (PRACTICE project, SIMULATED data)."""
import pandas as pd
import streamlit as st

from . import mmm as M
from .mmm_plots import adstock_chart, contribution_chart, fit_chart, response_chart, roi_chart


@st.cache_resource(show_spinner=False)
def _load():
    return M.load()


def render():
    st.subheader("Media Mix Model: where should the festive-season paid-media budget go?")
    st.warning("**Practice project, SIMULATED data.** Not real Amazon data or work done at/for Amazon.")
    st.caption("~3 years of weekly national data. Target = Prime-member customer spend (INR). Channels = search, social, "
               "display, OTT/YouTube. Controls = Diwali, Prime Day, Great Indian Festival flags, discount index, trend; "
               "Fourier yearly seasonality. PyMC-Marketing MMM with geometric adstock + logistic saturation, "
               "**calibrated with the GeoLift Prime test** via `add_lift_test_measurements`. Pre-fitted results load from "
               "`data/mmm_results.json` (refit: `python scripts/fit_mmm.py`).")
    try:
        res = _load()
    except FileNotFoundError:
        st.error("No pre-fitted results. Run `python scripts/fit_mmm.py` first."); return
    roi = res.roi_table()
    p = res.post

    c = st.columns(4)
    c[0].metric("Weeks of data", len(res.df)); c[1].metric("Holdout MAPE (last 13 wks)", f"{p['holdout_mape']:.1f}%")
    c[2].metric("In-sample R²", f"{p['r2_train']:.3f}"); c[3].metric("max r_hat / divergences", f"{p['rhat_max']:.3f} / {p['divergences']}")

    st.pyplot(fit_chart(res))
    st.pyplot(contribution_chart(res))

    st.markdown("#### ROI per channel (94% credible intervals)")
    a, b = st.columns([1, 1])
    a.pyplot(roi_chart(roi))
    show = roi.rename(columns={"spend_cr": "spend (Cr)", "roi_median": "ROI", "roi_lo": "ROI lo", "roi_hi": "ROI hi",
                               "true_roi": "true ROI", "incr_revenue_cr": "incr. revenue (Cr)", "p_roi_gt_1": "P(ROI>1)"})
    b.dataframe(show.round(2), hide_index=True)

    st.markdown("#### How the GeoLift test calibrates the MMM")
    l = res.lift.iloc[0]
    unc = pd.DataFrame(res.meta.get("uncalibrated_roi", {}))
    st.markdown(f"The GeoLift tab's Prime test found iROAS ≈ **{M.GEOLIFT_PRIME['iroas']:.2f}x** for Prime-targeted (mostly social) "
                f"ads. That enters the MMM as a lift measurement on `social`: going from INR 0 (holdout) to "
                f"INR {l.delta_x/M.CR:.2f} Cr/week (treated) adds INR {l.delta_y/M.CR:.2f} ± {l.sigma/M.CR:.2f} Cr/week. "
                "This constrains the social saturation curve, which observational data alone can't separate from the festive peak.")
    if len(unc):
        cmp_ = unc.merge(roi[["channel", "roi_median", "true_roi"]], on="channel", suffixes=("_uncal", "_cal"))
        cmp_.columns = ["channel", "ROI uncalibrated", "lo", "hi", "ROI calibrated", "true ROI"]
        st.dataframe(cmp_.round(2), hide_index=True)

    st.markdown("#### Response curves and marginal ROI")
    st.pyplot(response_chart(res.response_curves()))
    st.dataframe(res.marginal_roi_now().round(2).rename(columns={"avg_weekly_spend_cr": "avg weekly spend (Cr)",
                 "mroi_median": "marginal ROI (next INR)", "mroi_lo": "lo", "mroi_hi": "hi"}), hide_index=True)

    st.markdown("#### Adstock decay")
    st.pyplot(adstock_chart(res.adstock_curves()))

    st.markdown("#### Recovered vs true parameters")
    st.dataframe(res.params_table().round(2), hide_index=True)

    st.markdown("#### Budget optimizer: reallocate a fixed weekly budget")
    o1, o2 = st.columns(2)
    cur_total = float(sum(res.df[c].mean() for c in M.CHANNELS)) / M.CR
    total = o1.number_input("Weekly budget (INR Cr)", 0.5, 50.0, round(cur_total, 2), 0.25)
    bound = o2.slider("Max change per channel (±%)", 10, 100, 50, 10) / 100
    opt = res.optimize(total * M.CR, bound)
    st.dataframe(opt.round(2), hide_index=True)
    up = opt.attrs["uplift_weekly_cr"]
    st.metric("Expected extra Prime-member spend vs current mix", f"INR {up[1]:.2f} Cr / week",
              f"94% CI {up[0]:.2f} to {up[2]:.2f}; P(>0) {opt.attrs['p_uplift_gt_0']:.0%}")

    st.markdown("#### Growth-metric framing")
    g1, g2, g3 = st.columns(3)
    aov = g1.number_input("Avg order value (INR)", 200, 10000, 1500, 100)
    margin = g2.slider("Contribution margin", 0.05, 0.6, 0.35, 0.05)
    ltv = g3.number_input("Contribution LTV per incremental customer (INR)", 500, 50000, 4000, 500)
    ue = res.unit_economics(aov, margin, ltv)
    st.dataframe(ue.round(2), hide_index=True)
    st.caption("Cost per incremental order plays the role of incremental CAC: ad spend ÷ orders the ads actually caused. "
               "margin ROI = ROI × margin (≥1 means the channel pays back on margin). payback_orders = incremental orders' "
               "worth of margin needed to repay the ad cost.")

    best = roi.sort_values("roi_median", ascending=False).iloc[0]
    worst = roi.sort_values("roi_median").iloc[0]
    st.markdown("#### Readout")
    st.markdown(
        f"- **{best.channel.title()}** is the most incremental channel (ROI ≈ {best.roi_median:.1f}x), "
        f"**{worst.channel}** the least ({worst.roi_median:.1f}x, P(ROI>1) {worst.p_roi_gt_1:.0%}).\n"
        f"- Without the lift test the MMM credits Prime-targeted **social** with "
        f"{unc.set_index('channel').roi_median.get('social', float('nan')):.1f}x ROI, just like platform ROAS; calibrated, it's "
        f"{roi.set_index('channel').roi_median['social']:.1f}x. Experiments keep the MMM honest.\n"
        f"- Moving budget from social/display into search and OTT, with the same total, adds about **INR {up[1]:.1f} Cr/week** "
        "of Prime-member spend. Test the shift with a follow-up geo test before committing the full festive budget.")
