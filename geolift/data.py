"""Loading and validating the geo panel (long format: date, geo, y, [segment], [spend], [treated])."""
from pathlib import Path
import pandas as pd

REQUIRED = ["date", "geo", "y"]
SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_geo_panel.csv"
MIN_PRE_PERIODS = 4
MIN_GEOS = 4


class ValidationError(ValueError):
    pass


def load_sample() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_PATH)


def segments(df: pd.DataFrame) -> list:
    """Customer segments present in the optional 'segment' column (e.g. prime / non_prime)."""
    cols = {c.strip().lower(): c for c in df.columns}
    if "segment" not in cols:
        return []
    return sorted(df[cols["segment"]].dropna().astype(str).str.strip().str.lower().unique())


def validate(df: pd.DataFrame, test_start, test_end, treated_geos=None, segment=None) -> pd.DataFrame:
    """Return a clean panel with columns date, geo, y, spend, treated, post. Raises ValidationError.

    If the data has a 'segment' column (e.g. prime / non_prime), pass segment= to analyse one segment.
    """
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    if "segment" in df.columns:
        df["segment"] = df["segment"].astype(str).str.strip().str.lower()
        if segment is None:
            if df["segment"].nunique() > 1:
                raise ValidationError(f"Data has several segments ({', '.join(sorted(df['segment'].unique()))}); choose one to analyse.")
        else:
            if str(segment).lower() not in set(df["segment"]):
                raise ValidationError(f"Segment '{segment}' not found in the 'segment' column.")
            df = df[df["segment"] == str(segment).lower()]
    elif segment is not None:
        raise ValidationError("A segment was selected but the data has no 'segment' column.")
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValidationError(f"Missing required column(s): {', '.join(missing)}. Expected: date, geo, y (+ optional spend, treated).")
    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception as e:
        raise ValidationError(f"Could not parse 'date' column: {e}")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    if df["y"].isna().any():
        raise ValidationError("Column 'y' (customer spend, INR) has missing or non-numeric values.")
    if (df["y"] <= 0).any():
        raise ValidationError("Column 'y' must be > 0 for every geo-period (the model works on log revenue).")
    df["geo"] = df["geo"].astype(str)
    if df.duplicated(["date", "geo"]).any():
        raise ValidationError("Duplicate (date, geo) rows found - one row per geo per period (per segment) expected.")
    n_dates = df["date"].nunique()
    counts = df.groupby("geo")["date"].nunique()
    if (counts != n_dates).any():
        bad = ", ".join(counts[counts != n_dates].index[:5])
        raise ValidationError(f"Unbalanced panel: every geo needs a row for each of the {n_dates} dates (check: {bad}).")
    if df["geo"].nunique() < MIN_GEOS:
        raise ValidationError(f"Need at least {MIN_GEOS} geos (got {df['geo'].nunique()}).")

    test_start, test_end = pd.Timestamp(test_start), pd.Timestamp(test_end)
    if test_end < test_start:
        raise ValidationError("Test end date is before test start date.")
    df = df[df["date"] <= test_end]
    df["post"] = (df["date"] >= test_start).astype(int)
    n_pre = df.loc[df.post == 0, "date"].nunique()
    n_post = df.loc[df.post == 1, "date"].nunique()
    if n_pre < MIN_PRE_PERIODS:
        raise ValidationError(f"Only {n_pre} pre-period dates before the test start; need at least {MIN_PRE_PERIODS} (8-12 weeks recommended).")
    if n_post < 1:
        raise ValidationError("No data inside the test window.")

    if treated_geos:
        df["treated"] = df["geo"].isin([str(g) for g in treated_geos]).astype(int)
    elif "treated" in df.columns:
        df["treated"] = pd.to_numeric(df["treated"], errors="coerce").fillna(0).astype(int)
        if df.groupby("geo")["treated"].nunique().max() > 1:
            raise ValidationError("'treated' must be constant within each geo (1 = ads on, 0 = holdout).")
    else:
        raise ValidationError("No 'treated' column - select the treated geos (ads ON) in the sidebar.")
    n_t = df.loc[df.treated == 1, "geo"].nunique()
    n_c = df.loc[df.treated == 0, "geo"].nunique()
    if n_t < 1 or n_c < 1:
        raise ValidationError(f"Need at least one treated and one holdout geo (got {n_t} treated, {n_c} holdout).")
    if "spend" not in df.columns:
        df["spend"] = 0.0
    df["spend"] = pd.to_numeric(df["spend"], errors="coerce").fillna(0.0)
    return df.sort_values(["geo", "date"]).reset_index(drop=True)[["date", "geo", "y", "spend", "treated", "post"]]
