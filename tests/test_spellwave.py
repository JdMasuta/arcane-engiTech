import numpy as np
import pytest

from arcane import connect, Battery, Caster, simulate
from arcane.spellwave import SpellWave, waves_from_cast_log

trapezoid = getattr(np, "trapezoid", getattr(np, "trapz", None))


@pytest.fixture(scope="module")
def wave():
    return SpellWave(energy=100, start_step=20, n_steps=220)


def test_renormalized_density_integrates_to_one(wave):
    alive = np.where(wave.alive)[0]
    assert alive.size > 10
    for i in alive:
        assert trapezoid(wave.P[i], wave.x) == pytest.approx(1.0, abs=1e-6)


def test_renormalization_constant_does_real_work(wave):
    # A ~ 1 at launch, then grows well past 1.5 as the absorber eats the norm
    assert wave.A[0] == pytest.approx(1.0, abs=0.01)
    assert np.nanmax(wave.A) > 1.5


def test_classical_model_hits_the_ultra_magic_catastrophe(wave):
    alive = np.where(wave.alive)[0]
    last_alive = alive[-1]
    assert wave.classical[last_alive] > 1e5 * wave.energy
    _, _, renorm_total = wave.timeline()
    assert renorm_total.max() == pytest.approx(wave.energy)


def test_wave_fizzles_when_norm_collapses(wave):
    assert wave.fizzle_step is not None
    assert wave.fizzle_step > wave.start_step + wave.flight_time()
    assert not wave.is_alive(wave.fizzle_step)
    assert float(wave.density_at(wave.fizzle_step).max()) == 0.0
    assert float(wave.density_at(wave.start_step - 5).max()) == 0.0


def test_wave_rejects_bad_parameters():
    with pytest.raises(ValueError):
        SpellWave(100, 0, 100, max_range=0)
    with pytest.raises(ValueError):
        SpellWave(100, 0, 100, speed=-1)


def test_simulate_cast_log_records_and_restores():
    battery = Battery(1, name="b")
    battery.energy = 250
    caster = Caster(1, name="c")
    circuit = connect([battery, caster])
    log = []
    simulate(circuit, 250, cast_log=log)
    assert [entry["caster"] for entry in log] == ["c", "c"]
    for entry in log:
        assert entry["energy"] >= caster.cast_threshold
    # the wrapper is removed afterwards: cast resolves to the class method
    assert "cast" not in caster.__dict__


def test_waves_from_cast_log_alignment():
    log = [{"step": 30, "caster": "c1", "energy": 100},
           {"step": 90, "caster": "c2", "energy": 100}]
    waves = waves_from_cast_log(log, n_steps=200, max_range=20, speed=1.0)
    assert [w.start_step for w in waves] == [30, 90]
    assert all(w.max_range == 20 for w in waves)
    assert waves[0].is_alive(31) and not waves[0].is_alive(29)
