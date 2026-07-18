# The math: renormalized spell waves

An informal formalization of the "Theory of Magic" spell-propagation model,
after GorillaOfDestiny's video ([youtube.com/watch?v=AaCQf18zbE0](https://www.youtube.com/watch?v=AaCQf18zbE0)),
and how `arcane.spellwave` implements it.

## The problem: the ultra-magic catastrophe

Model a spell classically as a travelling bump of energy that must vanish at
its maximum range. The natural way to make it vanish is to shrink its spatial
variance to zero as it arrives — but the energy *density* of a bump scales
like 1/σ². As σ → 0 the expression for the spell's total potential energy
blows up toward infinity: the **ultra-magic catastrophe**.

A purely classical fix exists (cancel the divergence by construction), but it
pins the spell into a simple, stationary bump — no wave mechanics, no
interference, no probability distributions. Quantum mechanics is the far more
attractive framework, because wave packets natively give all three.

## The problem with going quantum

Real quantum mechanics derives probability density directly from the wave
function:

    P(x, t) = |Ψ(x, t)|²

and unitarity guarantees ∫P dx = 1 forever. Magic is *not* unitary: a spell's
amplitude dies as it approaches max range, so its normalization changes as it
travels and total probability fails to balance to one. Enforcing the
real-world rule breaks the model.

## The solution: a renormalized wave function

Apply the Golden Rule of Magic Theory — you are not strictly bound by the
laws of real-world physics — and promote the normalization to a dynamic
scaling factor:

    P(x, t) = A(t) · |Ψ(x, t)|²,       A(t) = 1 / ∫ |Ψ(x, t)|² dx

`A(t)` is a changing constant chosen at every instant so that the probability
density stays valid and balanced across space. The result is a functioning,
wave-like spell model with no infinite-energy paradox.

## What the code computes

`arcane/spellwave.py` realizes this in magic units (ħ = m = 1; one circuit
step = one time unit) on a 1D grid x ∈ [0, 1.15·R]:

| Video concept | Implementation |
|---|---|
| The travelling spell | Exact spreading Gaussian packet: centre x_c(t) = x₀ + v·t, width σ(t)² = σ₀²·(1 + (t/τ_d)²). `dispersion_time` τ_d is the magic-units "mass" choice — how long the packet stays coherent. |
| Amplitude death at max range | A stationary absorber D(x) = exp(−(x/R)⁶/2): the wave is Ψ = D·Ψ_free, so the raw norm N(t) = ∫|Ψ|²dx decays as the packet overlaps it. This is the non-unitary "magic" step. |
| The renormalization constant | `A(t) = 1/N(t)`, recomputed each step; the stored density is P = A·|Ψ|², which integrates to 1 (machine precision) at every alive step. |
| The spell ending | **Fizzle**: when N(t) < `fizzle_norm` the spell is spent; P is zero afterwards. |
| The ultra-magic catastrophe | The classical comparison series σ_cl(t) = σ₀·(1 − t/t_flight) with E_cl ∝ E/σ_cl², which blows up ~10⁸× at arrival while the renormalized total stays exactly E_cast. |

In the studio, every `Caster` firing spawns one of these waves on the shared
timeline (`simulate(..., cast_log=...)` records the casts). The **Spell
propagation** tab scrubs P(x, t) alongside the circuit, displays A(t) and
∫|Ψ|²dx live so you can watch the renormalization work, and plots the
classical blow-up against the finite renormalized total on a log axis.
`arcane.render.render_wave()` exports the same animation through manim.

The model deliberately keeps the Golden Rule's spirit: it is not a claim
about real physics, just a self-consistent piece of magic mathematics.
