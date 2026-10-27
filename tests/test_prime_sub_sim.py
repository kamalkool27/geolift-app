import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("sim", pathlib.Path(__file__).parents[1] / "scripts" / "prime_sub_sim.py")
sim = importlib.util.module_from_spec(spec); spec.loader.exec_module(sim)

def test_trial_lift_recovered():
    p = sim.panel(sim.TRUE)
    pt, ci, pr = sim.estimate(p["trials"], B=300)
    assert ci[0] < sim.TRUE["trials"] < ci[1] and pr > 0.95

def test_null_effect_not_significant():
    p = sim.panel({k: 0.0 for k in sim.TRUE})
    pt, ci, pr = sim.estimate(p["retained_d90"], B=300)
    assert ci[0] < 0 < ci[1]
