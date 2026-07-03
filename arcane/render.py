"""Render a circuit animation to a video file via manim's Python API.

This is the export path the GUI drives: it wraps make_circuit_scene() in a
manim tempconfig so callers pick the frame rate, resolution preset, and
output file directly, without shelling out to the manim CLI.
"""
import shutil
from pathlib import Path

from arcane.manim_scene import MANIM_AVAILABLE, make_circuit_scene

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


def render_circuit(comp_list, Es, output_path, fps=30, quality=DEFAULT_QUALITY,
                   run_time=10.0, progress=False):
    """Render the circuit's energy animation to output_path (an .mp4).

    fps sets the frame rate; quality is a key of QUALITY_PRESETS. Returns the
    Path the video was written to. Raises ImportError if manim is missing or
    ValueError for an unknown quality.
    """
    if not MANIM_AVAILABLE:
        raise ImportError("manim is not installed; pip install manim to render videos")
    if quality not in QUALITY_PRESETS:
        raise ValueError(f"Unknown quality {quality!r}; choose from {sorted(QUALITY_PRESETS)}")

    from manim import tempconfig

    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scene_cls = make_circuit_scene(comp_list, Es, run_time=run_time,
                                   name=output_path.stem or "ArcaneCircuitScene")

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
