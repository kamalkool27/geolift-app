"""Regenerate data/sample_geo_panel.csv (SIMULATED data, practice project).

40 Indian cities x 14 weeks x 2 customer segments (prime / non_prime).
20 cities (randomised within size pairs) run the festive paid-media campaign in the last 6 weeks.
The campaign has two audience ad sets in treated cities: Prime-member audiences (main budget) and
non-Prime audiences. True simulated lift: Prime 3% (high intent, would mostly buy anyway), non-Prime 8%.
"""
from pathlib import Path
import numpy as np
import pandas as pd

TRUE_LIFT = {"prime": 0.03, "non_prime": 0.08}
PRIME_SHARE = 0.6          # share of baseline customer spend from Prime members
AD_SHARE = {"prime": 0.6, "non_prime": 0.4}  # share of campaign budget per audience ad set
CITIES = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat',
          'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara', 'Ludhiana',
          'Agra', 'Nashik', 'Faridabad', 'Meerut', 'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar',
          'Ranchi', 'Coimbatore', 'Jabalpur', 'Gwalior', 'Vijayawada', 'Jodhpur', 'Madurai', 'Raipur', 'Kota', 'Chandigarh']


def make(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-07-27", periods=14, freq="7D")
    n_pre = 8
    base = np.sort(rng.lognormal(np.log(7e6), 0.5, len(CITIES)))[::-1]
    treated = np.zeros(len(CITIES), int)
    for i in range(0, len(CITIES), 2):  # pair by size, randomise within pair
        treated[i + rng.integers(2)] = 1
    season = np.exp(np.concatenate([np.linspace(0, 0.05, n_pre), np.linspace(0.12, 0.35, len(dates) - n_pre)]))
    week_spend = 4.4e6  # total campaign ad spend per week across treated cities
    tw = base * treated / (base * treated).sum()
    rows = []
    for seg, share in [("prime", PRIME_SHARE), ("non_prime", 1 - PRIME_SHARE)]:
        shock = np.exp(rng.normal(0, 0.02, len(dates)))
        for g, city in enumerate(CITIES):
            for t, d in enumerate(dates):
                post = t >= n_pre
                mu = base[g] * share * season[t] * shock[t]
                if post and treated[g]:
                    mu *= 1 + TRUE_LIFT[seg]
                y = mu * np.exp(rng.normal(0, 0.04))
                sp = round(week_spend * AD_SHARE[seg] * tw[g] * rng.uniform(0.9, 1.1), -3) if post and treated[g] else 0.0
                rows.append((d.date().isoformat(), city, seg, int(round(y)), sp, int(treated[g])))
    return pd.DataFrame(rows, columns=["date", "geo", "segment", "y", "spend", "treated"])


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "sample_geo_panel.csv"
    make().to_csv(out, index=False)
    print("wrote", out)
