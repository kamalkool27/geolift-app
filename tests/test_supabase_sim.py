import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("sim", pathlib.Path(__file__).parents[1] / "scripts" / "supabase_sim.py")
sim = importlib.util.module_from_spec(spec); spec.loader.exec_module(sim)

def test_signup_lift_recovered():
    s, u = sim.panel(sim.TRUE_SIGNUP_LIFT, sim.TRUE_UPGRADE_LIFT)
    pt, ci, p = sim.estimate(s, B=300)
    assert ci[0] < sim.TRUE_SIGNUP_LIFT < ci[1] and p > 0.95

def test_null_effect_not_significant():
    s, u = sim.panel(0.0, 0.0)
    pt, ci, p = sim.estimate(u, B=300)
    assert ci[0] < 0 < ci[1]
