"""Manim scene builders and the video render pipeline.

Everything here degrades gracefully when the third-party manim package is
absent: MANIM_AVAILABLE is False and the builders/renderers raise
ImportError only when actually called. Note that `from manim import ...`
inside these modules is an absolute import and always resolves to the
third-party package, never to this sub-package.
"""
from arcane.manim.circuit import (MANIM_AVAILABLE, make_circuit_scene,
                                  make_combined_scene)
from arcane.manim.wave import build_wave_mobjects, make_spellwave_scene
from arcane.manim.render import (QUALITY_PRESETS, DEFAULT_QUALITY,
                                 render_circuit, render_wave,
                                 render_combined)

__all__ = [
    "MANIM_AVAILABLE", "make_circuit_scene", "make_combined_scene",
    "make_spellwave_scene", "build_wave_mobjects", "QUALITY_PRESETS",
    "DEFAULT_QUALITY", "render_circuit", "render_wave", "render_combined",
]
