"""Amazon India festive-sale regional campaign geo-lift test (PRACTICE project, SIMULATED data)."""
import pandas as pd
import streamlit as st

from geolift.data import ValidationError, load_sample, segments, validate
from geolift.model import fit, simulate_power
from geolift.mmm_tab import render as render_mmm
from geolift.plots import counterfactual_chart, lift_posterior_chart

st.set_page_config(page_title="Amazon India Festive Campaign GeoLift (practice)", layout="wide")
st.title("Is paid media to Prime members incremental, or are we paying for sales we'd get anyway?")
st.warning("**Practice / portfolio project.** All data is SIMULATED. This is not real Amazon data, "
           "and not work done at or for Amazon.")
st.caption("Bayesian geo-holdout (diff-in-diff) analysis in PyMC. Treated cities ran the festive-sale paid-media "
           "campaign (search, social, display, OTT), targeted to Prime-member audiences, during the test; holdout cities did not. "
           "Outcome = weekly Prime-member customer spend (INR) per city. Toggle to non-Prime to compare.")


@st.cache_data(show_spinner=False)
def run_model(panel: pd.DataFrame, draws: int):
    r = fit(panel, draws=draws, tune=draws, chains=2)
    return r


tab_an, tab_plan, tab_mmm = st.tabs(["Analyse test", "Pre-test planner", "Media Mix Model"])

with tab_mmm:
    render_mmm()

with tab_an:
    with st.sidebar:
        st.header("1. Data")
        src = st.radio("Source", ["Sample: simulated Amazon India festive-sale panel (40 cities)", "Upload CSV"])
        if src.startswith("Upload"):
            f = st.file_uploader("CSV with columns date, geo, y [, segment, spend, treated]", type="csv")
            raw = pd.read_csv(f) if f else None
        else:
            raw = load_sample()
    if raw is None:
        st.info("Upload a CSV to begin, or use the sample data.")
        st.stop()
    raw.columns = [c.strip().lower() for c in raw.columns]
    try:
        dates = sorted(pd.to_datetime(raw["date"]).dt.date.unique())
    except Exception:
        st.error("Could not read a 'date' column. Required columns: date, geo, y."); st.stop()
    with st.sidebar:
        st.header("2. Test setup")
        default_start = dates[8] if len(dates) > 8 else dates[-1]
        start = st.selectbox("Campaign start (ads ON in treated cities)", dates, index=dates.index(default_start))
        end = st.selectbox("Campaign end", dates, index=len(dates) - 1)
        segs = segments(raw)
        segment = None
        if segs:
            labels = {"prime": "Prime members", "non_prime": "Non-Prime customers"}
            default = segs.index("prime") if "prime" in segs else 0
            segment = st.radio("Customer segment", segs, index=default, format_func=lambda x: labels.get(x, x), horizontal=True)
        treated_geos = None
        if "treated" not in raw.columns:
            treated_geos = st.multiselect("Treated cities (ads ON)", sorted(raw["geo"].astype(str).unique()))
        spend_override = st.number_input("Total campaign ad spend override (INR, 0 = use 'spend' column)", 0, 10**10, 0, 100000)
        draws = st.select_slider("Posterior draws per chain", [300, 500, 1000], 500)
    try:
        panel = validate(raw, start, end, treated_geos, segment)
    except ValidationError as e:
        st.error(f"Data problem: {e}"); st.stop()

    c = st.columns(4)
    c[0].metric("Cities", panel.geo.nunique()); c[1].metric("Treated cities", panel[panel.treated == 1].geo.nunique())
    c[2].metric("Pre-period weeks", panel[panel.post == 0].date.nunique()); c[3].metric("Test weeks", panel[panel.post == 1].date.nunique())
    with st.expander("Preview data"):
        st.dataframe(panel.head(50))

    if st.button("Run Bayesian geo-lift analysis", type="primary"):
        st.session_state["go"] = True
    if not st.session_state.get("go"):
        st.stop()
    with st.spinner("Sampling posterior with PyMC (~20-60s)..."):
        r = run_model(panel, draws)
    if spend_override:
        r.spend = float(spend_override)
    s = r.summary()
    lo, med, hi = s["lift_pct"]
    m = st.columns(4)
    m[0].metric("Lift in customer spend", f"{med:.1f}%", f"94% CI {lo:.1f}% to {hi:.1f}%")
    m[1].metric("P(lift > 0)", f"{s['p_lift_gt_0']:.1%}")
    inc = s["incremental_revenue"] / 1e7
    m[2].metric("Incremental revenue", f"INR {inc[1]:.2f} Cr", f"CI {inc[0]:.2f} to {inc[2]:.2f} Cr")
    if "iroas" in s:
        m[3].metric("iROAS (incr. revenue / ad spend)", f"{s['iroas'][1]:.2f}x", f"CI {s['iroas'][0]:.2f} to {s['iroas'][2]:.2f}x")

    st.pyplot(counterfactual_chart(r.weekly)); st.pyplot(lift_posterior_chart(r.lift))

    seg_name = {"prime": "Prime-member", "non_prime": "non-Prime"}.get(segment, "customer") if segment else "customer"
    st.subheader("Readout: is paid media to " + ("Prime members" if segment == "prime" else f"{seg_name} customers")
                 + " incremental, or are we paying for sales we'd get anyway?")
    if s["p_lift_gt_0"] < 0.9:
        verdict = ("**No reliable evidence** that the festive campaign drove extra customer spend. "
                   "Re-test with more cities/weeks before scaling the regional budget.")
    elif "iroas" in s and s["iroas"][1] < 1:
        verdict = (f"The campaign **does** lift customer spend (~{med:.1f}%), but each INR of ads returns only "
                   f"{s['iroas'][1]:.2f} INR of incremental revenue (below breakeven before margin). **Cut or reallocate** spend, "
                   "and don't trust platform-reported ROAS, which credits festive purchases that would have happened anyway.")
    else:
        verdict = f"Paid media to this segment drives a credible ~{med:.1f}% lift with iROAS {s.get('iroas', [0, float('nan')])[1]:.2f}x. Compare iROAS to your margin-adjusted breakeven (e.g. 1 / contribution margin) before scaling."
    st.markdown(f"In the treated cities, {seg_name} spend was **{med:.1f}%** higher than it would have been without ads "
                f"(94% credible interval {lo:.1f}% to {hi:.1f}%; {s['p_lift_gt_0']:.0%} probability the effect is positive). "
                f"That is about **INR {s['incremental_revenue'][1]/1e7:.2f} Cr** of incremental revenue out of "
                f"INR {s['actual_revenue']/1e7:.2f} Cr actual, on INR {r.spend/1e7:.2f} Cr of ad spend. {verdict}")

    if segment == "prime":
        st.info("Prime members are high-intent and buy heavily in the festive sale anyway, so expect a small lift here; "
                "platform-reported ROAS over-credits ads most for this group. Toggle **Non-Prime customers** to compare. "
                "Next step: validate with a user-level randomised holdout (Customer Match / Amazon DSP audiences).")
    st.subheader("Convergence diagnostics")
    d = st.columns(3)
    d[0].metric("r_hat (tau)", f"{s['rhat_max']:.3f}", "OK" if s["rhat_max"] < 1.01 else "check")
    d[1].metric("ESS (tau)", f"{s['ess_min']:.0f}", "OK" if s["ess_min"] > 400 else "low")
    d[2].metric("Divergences", s["divergences"])

    rows = {"metric": [], "p3": [], "median": [], "p97": []}
    for k in ["lift_pct", "counterfactual", "incremental_revenue", "iroas"]:
        if k in s:
            rows["metric"].append(k); rows["p3"].append(s[k][0]); rows["median"].append(s[k][1]); rows["p97"].append(s[k][2])
    for k in ["p_lift_gt_0", "actual_revenue", "spend", "rhat_max", "ess_min", "divergences"]:
        rows["metric"].append(k); rows["p3"].append(None); rows["median"].append(s[k]); rows["p97"].append(None)
    st.download_button("Download results CSV", pd.DataFrame(rows).to_csv(index=False), f"geolift_results_{segment or 'all'}.csv", "text/csv")

with tab_plan:
    st.subheader("Pre-test planner: how many cities and weeks do we need?")
    st.caption("Simulates many 50/50 geo holdouts on log weekly customer spend to estimate power and minimum detectable effect.")
    p = st.columns(4)
    n_geos = p[0].slider("Cities", 6, 100, 40, 2)
    pre = p[1].slider("Pre-period weeks", 4, 26, 8)
    post = p[2].slider("Test weeks", 1, 12, 6)
    lift = p[3].slider("Expected lift (%)", 1, 30, 6) / 100
    noise = st.slider("City-week noise (log scale SD)", 0.02, 0.30, 0.05, 0.01)
    res = simulate_power(n_geos, pre, post, lift, noise)
    a, b = st.columns(2)
    a.metric("Power (one-sided, 5%)", f"{res['power']:.0%}", "OK" if res["power"] >= 0.8 else "underpowered")
    b.metric("MDE at 80% power", f"{res['mde_pct']:.1f}%")
