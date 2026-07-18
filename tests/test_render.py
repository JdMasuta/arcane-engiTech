"""Render-pipeline plumbing tests.

manim itself is not installed in CI, so these exercise render_circuit with a
fake manim module injected: they confirm the fps/quality/output arguments
are translated into the right config and the produced file is delivered to
the requested path, plus the guarded error paths.
"""
import sys
import types

import pytest

from arcane import connect, Battery, Caster, simulate
import arcane.render as render


@pytest.fixture
def simple_history():
    circuit = connect([Battery(1, name="b"), Caster(1, name="c")])
    t, Es, ET = simulate(circuit, 20)
    return circuit, Es


def test_quality_presets_match_gui_choices():
    assert set(render.QUALITY_PRESETS) == {"480p", "720p", "1080p", "1440p", "4k"}
    assert render.DEFAULT_QUALITY in render.QUALITY_PRESETS


def test_render_circuit_without_manim_raises(simple_history, monkeypatch):
    circuit, Es = simple_history
    monkeypatch.setattr(render, "MANIM_AVAILABLE", False)
    with pytest.raises(ImportError):
        render.render_circuit(circuit, Es, "out.mp4")


def test_render_circuit_rejects_unknown_quality(simple_history, monkeypatch):
    circuit, Es = simple_history
    monkeypatch.setattr(render, "MANIM_AVAILABLE", True)
    with pytest.raises(ValueError):
        render.render_circuit(circuit, Es, "out.mp4", quality="8k")


def _fake_manim_env(monkeypatch, tmp_path, captured):
    """Install a fake manim module and return the FakeScene class."""
    produced = tmp_path / "produced.mp4"
    produced.write_bytes(b"fake video")

    class FakeWriter:
        movie_file_path = str(produced)

    class FakeRenderer:
        file_writer = FakeWriter()

    class FakeScene:
        def __init__(self):
            self.renderer = FakeRenderer()

        def render(self):
            captured["rendered"] = True

    class FakeTempConfig:
        def __init__(self, overrides):
            captured["config"] = overrides

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    fake_manim = types.ModuleType("manim")
    fake_manim.tempconfig = FakeTempConfig
    monkeypatch.setitem(sys.modules, "manim", fake_manim)
    monkeypatch.setattr(render, "MANIM_AVAILABLE", True)
    return FakeScene


def test_render_circuit_translates_settings_and_writes_file(simple_history, monkeypatch, tmp_path):
    circuit, Es = simple_history
    captured = {}
    fake_scene = _fake_manim_env(monkeypatch, tmp_path, captured)
    monkeypatch.setattr(render, "make_circuit_scene",
                        lambda *a, **k: fake_scene)

    out = tmp_path / "videos" / "spell.mp4"
    result = render.render_circuit(circuit, Es, out, fps=48, quality="1080p",
                                   run_time=5.0)

    assert result == out.resolve()
    assert out.exists() and out.read_bytes() == b"fake video"
    assert captured["rendered"] is True
    cfg = captured["config"]
    assert cfg["frame_rate"] == 48
    assert cfg["quality"] == render.QUALITY_PRESETS["1080p"]
    assert cfg["output_file"] == "spell"
    # quality is applied before frame_rate so the explicit fps wins
    assert list(cfg).index("quality") < list(cfg).index("frame_rate")


def test_render_wave_uses_same_plumbing(monkeypatch, tmp_path):
    from arcane.spellwave import SpellWave
    import arcane.manim_wave as manim_wave

    wave = SpellWave(100, 0, 120)
    captured = {}
    fake_scene = _fake_manim_env(monkeypatch, tmp_path, captured)
    monkeypatch.setattr(manim_wave, "MANIM_AVAILABLE", True)
    monkeypatch.setattr(manim_wave, "make_spellwave_scene",
                        lambda *a, **k: fake_scene)

    out = tmp_path / "wave.mp4"
    result = render.render_wave(wave, out, fps=24, quality="480p")

    assert result == out.resolve()
    assert out.read_bytes() == b"fake video"
    assert captured["config"]["frame_rate"] == 24
    assert captured["config"]["quality"] == render.QUALITY_PRESETS["480p"]


def test_render_wave_without_manim_raises():
    from arcane.spellwave import SpellWave
    wave = SpellWave(100, 0, 120)
    with pytest.raises(ImportError):
        render.render_wave(wave, "wave.mp4")
