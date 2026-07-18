import numpy as np
import pytest

from arcane import connect, Battery, Caster, simulate
from arcane.spellwave import SpellWave, SpellWave2D, waves_from_cast_log

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


def test_waves_from_cast_log_per_caster_overrides():
    log = [{"step": 30, "caster": "sniper", "energy": 100},
           {"step": 40, "caster": "grenade", "energy": 100}]
    overrides = {"sniper": {"max_range": 90, "speed": 2.0}}
    waves = waves_from_cast_log(log, n_steps=200, max_range=20, speed=0.5,
                                width=2.0, overrides_by_caster=overrides)
    sniper_wave, grenade_wave = waves
    assert sniper_wave.max_range == 90
    assert sniper_wave.speed == 2.0
    assert sniper_wave.width == 2.0            # untouched key falls back to the global default
    assert grenade_wave.max_range == 20        # caster absent from overrides: pure defaults
    assert grenade_wave.speed == 0.5


@pytest.fixture(scope="module")
def wave2d():
    return SpellWave2D(energy=100, start_step=20, n_steps=140, max_range=20,
                       speed=0.5, width=1.5, grid_points=80)


def test_2d_renormalized_density_integrates_to_one(wave2d):
    alive = np.where(wave2d.alive)[0]
    assert alive.size > 5
    for i in alive:
        integral = trapezoid(trapezoid(wave2d.P[i], wave2d.x, axis=1), wave2d.y)
        assert integral == pytest.approx(1.0, abs=1e-6)


def test_2d_renormalization_constant_does_real_work(wave2d):
    assert wave2d.A[0] == pytest.approx(1.0, abs=0.05)
    assert np.nanmax(wave2d.A) > 1.5


def test_2d_classical_model_hits_the_ultra_magic_catastrophe(wave2d):
    alive = np.where(wave2d.alive)[0]
    assert wave2d.classical[alive[-1]] > 1e5 * wave2d.energy
    _, _, renorm_total = wave2d.timeline()
    assert renorm_total.max() == pytest.approx(wave2d.energy)


def test_2d_wave_fizzles_when_norm_collapses(wave2d):
    assert wave2d.fizzle_step is not None
    assert not wave2d.is_alive(wave2d.fizzle_step)
    assert float(wave2d.density_at(wave2d.fizzle_step).max()) == 0.0
    assert float(wave2d.density_at(wave2d.start_step - 5).max()) == 0.0


def test_2d_wave_field_is_two_dimensional(wave2d):
    assert wave2d.P.ndim == 3  # (time, y, x)
    assert wave2d.density_at(50).shape == (wave2d.y.size, wave2d.x.size)
    xmin, xmax, ymin, ymax = wave2d.extent()
    assert xmax > xmin and ymax > ymin
    assert ymin < 0 < ymax  # y is centred on the caster's line of travel


def test_2d_wave_rejects_bad_parameters():
    with pytest.raises(ValueError):
        SpellWave2D(100, 0, 100, max_range=0)
    with pytest.raises(ValueError):
        SpellWave2D(100, 0, 100, width=-1)


def test_waves_from_cast_log_can_build_2d_waves():
    log = [{"step": 10, "caster": "c", "energy": 100}]
    waves = waves_from_cast_log(log, n_steps=80, wave_cls=SpellWave2D,
                                max_range=15, speed=1.0)
    assert isinstance(waves[0], SpellWave2D)
    assert waves[0].max_range == 15


def test_caster_wave_params_default_to_none():
    c = Caster(1, name="c")
    assert c.wave_range is None
    assert c.wave_speed is None
    assert c.wave_width is None
    overridden = Caster(1, name="c2", wave_range=75, wave_speed=1.5, wave_width=4)
    assert (overridden.wave_range, overridden.wave_speed, overridden.wave_width) == (75, 1.5, 4)
