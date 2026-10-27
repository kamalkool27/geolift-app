import pandas as pd, pytest
from geolift.data import ValidationError, load_sample, validate

S, E = "2026-09-21", "2026-10-26"

def test_sample_valid():
    p = validate(load_sample(), S, E)
    assert p.geo.nunique() == 40 and p[p.post == 0].date.nunique() == 8

def test_missing_column():
    with pytest.raises(ValidationError, match="Missing"):
        validate(load_sample().drop(columns="y"), S, E)

def test_too_few_pre():
    with pytest.raises(ValidationError, match="pre-period"):
        validate(load_sample(), "2026-08-10", E)

def test_unbalanced():
    df = load_sample(); df = df.drop(df.index[5])
    with pytest.raises(ValidationError, match="Unbalanced"):
        validate(df, S, E)

def test_needs_treated_selection():
    df = load_sample().drop(columns="treated")
    with pytest.raises(ValidationError, match="treated"):
        validate(df, S, E)
    p = validate(df, S, E, treated_geos=["Mumbai", "Pune"])
    assert p[p.treated == 1].geo.nunique() == 2
