"""Pre-fit the MMM and save posterior summaries to data/mmm_results.json (so the app loads instantly).
Usage: python scripts/fit_mmm.py [draws] [tune] [chains]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from geolift.mmm import run_and_save  # noqa: E402

if __name__ == "__main__":
    a = [int(v) for v in sys.argv[1:]]
    r = run_and_save(*a)
    print(r.roi_table().round(2).to_string())
    print(r.params_table().round(2).to_string())
    print("holdout MAPE %.2f%%  R2 %.3f  rhat %.3f  div %d" % (r.post["holdout_mape"], r.post["r2_train"], r.post["rhat_max"], r.post["divergences"]))
    print("uncalibrated", r.meta["uncalibrated_roi"], r.meta["uncalibrated_mape"])
    o = r.optimize(); print(o.round(2).to_string(), o.attrs)
    print(r.unit_economics(margin=0.35).round(2).to_string())
