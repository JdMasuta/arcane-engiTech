"""Dark-themed matplotlib canvas base for the Qt views."""
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from arcane import theme


class ThemedCanvas(FigureCanvasQTAgg):
    """A FigureCanvas pre-styled to the arcane palette with one axes."""

    def __init__(self, parent=None, facecolor=None):
        self.figure = Figure(figsize=(5, 3), constrained_layout=True)
        super().__init__(self.figure)
        if parent is not None:
            self.setParent(parent)
        bg = "#" + (facecolor or theme.SURFACE)
        self.figure.set_facecolor(bg)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(bg)
        self._style_axes()

    def _style_axes(self, ax=None):
        ax = ax if ax is not None else self.ax
        muted = "#" + theme.TEXT_MUTED
        ax.set_facecolor(self.figure.get_facecolor())
        for spine in ax.spines.values():
            spine.set_color("#" + theme.BORDER)
        ax.tick_params(colors=muted, labelsize=8)
        ax.xaxis.label.set_color(muted)
        ax.yaxis.label.set_color(muted)
        ax.title.set_color("#" + theme.TEXT)
