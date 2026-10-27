import pandas as pd, pytest
from geolift.data import ValidationError, load_sample, segments, validate

S, E = "2026-09-21", "2026-10-26"

def test_sample_valid():
    p = validate(load_sample(), S, E, segment="prime")
    assert p.geo.nunique() == 40 and p[p.post == 0].date.nunique() == 8

def test_missing_column():
    with pytest.raises(ValidationError, match="Missing"):
        validate(load_sample().drop(columns="y"), S, E, segment="prime")

def test_too_few_pre():
    with pytest.raises(ValidationError, match="pre-period"):
        validate(load_sample(), "2026-08-10", E, segment="prime")

def test_unbalanced():
    df = load_sample(); df = df.drop(df.index[5])
    with pytest.raises(ValidationError, match="Unbalanced"):
        validate(df, S, E, segment="prime")

def test_needs_treated_selection():
    df = load_sample().drop(columns="treated")
    with pytest.raises(ValidationError, match="treated"):
        validate(df, S, E, segment="prime")
    p = validate(df, S, E, treated_geos=["Mumbai", "Pune"], segment="prime")
    assert p[p.treated == 1].geo.nunique() == 2


def test_segments():
    df = load_sample()
    assert segments(df) == ["non_prime", "prime"]
    with pytest.raises(ValidationError, match="segments"):
        validate(df, S, E)
    with pytest.raises(ValidationError, match="not found"):
        validate(df, S, E, segment="gold")
    p, n = validate(df, S, E, segment="prime"), validate(df, S, E, segment="NON_PRIME")
    assert len(p) == len(n) == 40 * 14

def test_no_segment_column_still_works():
    df = load_sample().query("segment == 'prime'").drop(columns="segment")
    assert validate(df, S, E).geo.nunique() == 40
    with pytest.raises(ValidationError, match="no 'segment'"):
        validate(df, S, E, segment="prime")
