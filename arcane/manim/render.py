"""Render circuit and spell-wave animations to video via manim's Python API.

This is the export path the GUI drives: scenes are wrapped in a manim
tempconfig so callers pick the frame rate, resolution preset, and output
file directly, without shelling out to the manim CLI.
"""
import shutil
from pathlib import Path

from arcane.manim.circuit import MANIM_AVAILABLE, make_circuit_scene, make_combined_scene

# Resolution presets, mirrored from manim's own quality flags so the GUI can
# offer them by name. Frame rate is chosen separately.
QUALITY_PRESETS = {
    "480p": "low_quality",
    "720p": "medium_quality",
    "1080p": "high_quality",
    "1440p": "production_quality",
    "4k": "fourk_quality",
}
DEFAULT_QUALITY = "720p"


def _check_render_inputs(quality):
    if not MANIM_AVAILABLE:
        raise ImportError("manim is not installed; pip install manim to render videos")
    if quality not in QUALITY_PRESETS:
        raise ValueError(f"Unknown quality {quality!r}; choose from {sorted(QUALITY_PRESETS)}")


def _render_scene(scene_cls, output_path, fps, quality, progress):
    """Render a Scene subclass to output_path under a tempconfig."""
    from manim import tempconfig

    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config_overrides = {
        "quality": QUALITY_PRESETS[quality],
        "frame_rate": fps,
        "output_file": output_path.stem,
        "media_dir": str(output_path.parent / ".arcane_media"),
        "disable_caching": True,
        "progress_bar": "display" if progress else "none",
        "verbosity": "WARNING",
    }
    with tempconfig(config_overrides):
        scene = scene_cls()
        scene.render()
        produced = Path(scene.renderer.file_writer.movie_file_path)

    if produced.resolve() != output_path:
        shutil.copy2(produced, output_path)
    return output_path


def render_circuit(comp_list, Es, output_path, fps=30, quality=DEFAULT_QUALITY,
                   run_time=10.0, progress=False):
    """Render the circuit's energy animation to output_path (an .mp4).

    fps sets the frame rate; quality is a key of QUALITY_PRESETS. Returns the
    Path the video was written to. Raises ImportError if manim is missing or
    ValueError for an unknown quality.
    """
    _check_render_inputs(quality)
    name = Path(output_path).stem or "ArcaneCircuitScene"
    scene_cls = make_circuit_scene(comp_list, Es, run_time=run_time, name=name)
    return _render_scene(scene_cls, output_path, fps, quality, progress)


def render_wave(wave, output_path, fps=30, quality=DEFAULT_QUALITY,
                run_time=8.0, progress=False):
    """Render one spell wave's renormalized propagation to output_path.

    wave is a SpellWave or SpellWave2D; same fps/quality semantics as
    render_circuit.
    """
    from arcane.manim.wave import make_spellwave_scene

    _check_render_inputs(quality)
    name = Path(output_path).stem or "SpellWaveScene"
    scene_cls = make_spellwave_scene(wave, run_time=run_time, name=name)
    return _render_scene(scene_cls, output_path, fps, quality, progress)


def render_combined(comp_list, Es, wave, output_path, fps=30,
                    quality=DEFAULT_QUALITY, run_time=10.0, progress=False):
    """Render the circuit schematic and the spell wave it cast together,
    one above the other, sharing a single timeline.

    wave must come from the same run that produced Es (see
    simulation.simulate(cast_log=...) and spellwave.waves_from_cast_log()).
    Same fps/quality semantics as render_circuit.
    """
    _check_render_inputs(quality)
    name = Path(output_path).stem or "ArcaneCombinedScene"
    scene_cls = make_combined_scene(comp_list, Es, wave, run_time=run_time, name=name)
    return _render_scene(scene_cls, output_path, fps, quality, progress)
