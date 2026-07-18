"""Renormalized wave-function model of a travelling spell.

Formalizes the "Theory of Magic" spell-propagation math
(https://www.youtube.com/watch?v=AaCQf18zbE0):

- A *classical* spell is a shrinking bump: its spatial variance goes to
  zero as it arrives at max range, so its energy density blows up toward
  infinity — the **ultra-magic catastrophe**.
- Modelling the spell as a quantum wave packet fixes the shape problem,
  but magic is not unitary: the packet's amplitude dies as it approaches
  max range, so the real-world rule P = |Psi|^2 stops summing to one.
- The Golden Rule of Magic Theory (you are not bound by real physics)
  permits a **renormalized wave function**:

      P(x, t) = A(t) * |Psi(x, t)|^2,   A(t) = 1 / integral(|Psi|^2 dx)

  which keeps P a valid probability density for as long as the spell
  lives, without infinite-energy paradoxes.

Concretely, in magic units (hbar = m = 1, one circuit step = one time
unit): Psi is an exact spreading Gaussian packet multiplied by a
stationary max-range absorber D(x) = exp(-(x/R)^6 / 2). While the packet
travels, the overlap with the absorber grows, the raw norm N(t) drifts
below one, and A(t) = 1/N(t) visibly does the video's renormalization
work. When N(t) falls below `fizzle_norm` the spell is spent.
"""
import numpy as np

_trapezoid = getattr(np, "trapezoid", getattr(np, "trapz", None))

DEFAULT_MAX_RANGE = 30.0
DEFAULT_SPEED = 0.5
DEFAULT_WIDTH = 2.0
DEFAULT_DISPERSION_TIME = 120.0
GRID_POINTS = 600
FIZZLE_NORM = 5e-3


class SpellWave:
    """One cast spell propagating as a renormalized wave packet.

    Precomputes, for every circuit step from `start_step` to `n_steps`,
    the renormalized density P(x), the renormalization constant A(t),
    the raw norm N(t), and the classical-model energy for comparison.
    """

    def __init__(self, energy, start_step, n_steps, caster="caster",
                 max_range=DEFAULT_MAX_RANGE, speed=DEFAULT_SPEED,
                 width=DEFAULT_WIDTH, dispersion_time=DEFAULT_DISPERSION_TIME,
                 fizzle_norm=FIZZLE_NORM, grid_points=GRID_POINTS):
        if max_range <= 0 or speed <= 0 or width <= 0:
            raise ValueError("max_range, speed, and width must all be > 0")
        self.energy = float(energy)
        self.start_step = int(start_step)
        self.n_steps = int(n_steps)
        self.caster = caster
        self.max_range = float(max_range)
        self.speed = float(speed)
        self.width = float(width)
        # dispersion_time = 2*m*sigma0^2 in magic units: picking it directly
        # is picking the spell's "mass", i.e. how long the packet stays
        # coherent before quantum spreading smears it out
        self.dispersion_time = float(dispersion_time)
        self.fizzle_norm = float(fizzle_norm)
        # the packet is born 3 sigma inside the grid so its full norm starts
        # on-grid (A(0) ~ 1) instead of half-clipped at x = 0
        self.launch_x = 3.0 * self.width
        self.x = np.linspace(0.0, 1.15 * self.max_range, grid_points)
        self._absorber_sq = np.exp(-((self.x / self.max_range) ** 6))
        self._compute_history()

    # -- physics -------------------------------------------------------------
    def _free_density(self, t):
        """|Psi_free|^2 of the exact spreading Gaussian packet at time t."""
        sigma_sq = self.width ** 2 * (1.0 + (t / self.dispersion_time) ** 2)
        center = self.launch_x + self.speed * t
        return (np.exp(-((self.x - center) ** 2) / (2.0 * sigma_sq))
                / np.sqrt(2.0 * np.pi * sigma_sq))

    def flight_time(self):
        """Steps for the packet centre to reach max range."""
        return (self.max_range - self.launch_x) / self.speed

    def _classical_energy(self, t):
        """The ultra-magic catastrophe: E ~ 1/sigma^2 with sigma -> 0."""
        shrink = max(1.0 - t / self.flight_time(), 1e-3)
        return self.energy / shrink ** 2

    def _compute_history(self):
        duration = max(self.n_steps - self.start_step, 0)
        self.P = np.zeros((duration, self.x.size))
        self.A = np.full(duration, np.nan)
        self.N = np.zeros(duration)
        self.classical = np.zeros(duration)
        self.alive = np.zeros(duration, dtype=bool)
        fizzled = False
        self.fizzle_step = None
        for i in range(duration):
            t = float(i)
            density = self._free_density(t) * self._absorber_sq
            norm = float(_trapezoid(density, self.x))
            self.N[i] = norm
            self.classical[i] = self._classical_energy(t)
            if fizzled or norm < self.fizzle_norm:
                if not fizzled:
                    fizzled = True
                    self.fizzle_step = self.start_step + i
                continue
            self.alive[i] = True
            self.A[i] = 1.0 / norm
            self.P[i] = self.A[i] * density

    # -- step-indexed views (circuit timeline) --------------------------------
    def _local(self, step):
        return int(step) - self.start_step

    def is_alive(self, step):
        i = self._local(step)
        return 0 <= i < self.alive.size and bool(self.alive[i])

    def density_at(self, step):
        """Renormalized P(x) at a circuit step (zeros before birth/after
        fizzle)."""
        i = self._local(step)
        if 0 <= i < self.P.shape[0]:
            return self.P[i]
        return np.zeros_like(self.x)

    def energy_density_at(self, step):
        return self.energy * self.density_at(step)

    def A_at(self, step):
        i = self._local(step)
        if 0 <= i < self.A.size:
            return float(self.A[i])
        return float("nan")

    def norm_at(self, step):
        i = self._local(step)
        if 0 <= i < self.N.size:
            return float(self.N[i])
        return 0.0

    def classical_energy_at(self, step):
        i = self._local(step)
        if 0 <= i < self.classical.size:
            return float(self.classical[i])
        return 0.0

    def timeline(self):
        """(steps, classical_series, renormalized_total_series) for plots.

        The renormalized total is E_cast while alive and 0 after the
        fizzle — finite by construction, unlike the classical series.
        """
        steps = np.arange(self.start_step, self.n_steps)
        renorm_total = np.where(self.alive, self.energy, 0.0)
        return steps, self.classical.copy(), renorm_total


def waves_from_cast_log(cast_log, n_steps, max_range=DEFAULT_MAX_RANGE,
                        speed=DEFAULT_SPEED, width=DEFAULT_WIDTH,
                        dispersion_time=DEFAULT_DISPERSION_TIME):
    """Build one SpellWave per recorded cast event.

    cast_log entries are the dicts simulation.simulate() appends:
    {"step": int, "caster": name, "energy": consumed}.
    """
    return [SpellWave(entry["energy"], entry["step"], n_steps,
                      caster=entry["caster"], max_range=max_range,
                      speed=speed, width=width,
                      dispersion_time=dispersion_time)
            for entry in cast_log]
