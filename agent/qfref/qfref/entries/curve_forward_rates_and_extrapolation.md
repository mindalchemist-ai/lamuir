# Forward Rates from a Discount Curve: Derivatives at the Ends and Extrapolation

A discount curve is known only on its node maturities and on whatever interpolation the task prescribes between them. Forward rates are derivatives of that curve, so they are the first quantity to go wrong at the edges of the curve. This entry covers how to differentiate the curve, what to do at the first and last node, and how to extend the curve beyond its last node.

## Contents

1. [Shared Foundations](#1-shared-foundations)
2. [Forward Rates from Discount Factors](#2-forward-rates-from-discount-factors)
3. [Derivatives at the Ends of the Curve](#3-derivatives-at-the-ends-of-the-curve)
4. [Extrapolation Beyond the Last Node](#4-extrapolation-beyond-the-last-node)
5. [Checks and Scope](#5-checks-and-scope)
6. [References](#6-references)

## 1. Shared Foundations

| Symbol | Definition |
|---|---|
| $P(T)$ | Discount factor for maturity $T$ years, $0 < P(T) \le 1$ for nonnegative rates |
| $T_{1} < \dots < T_{n}$ | Node maturities of the curve |
| $z(T)$ | Continuously compounded zero rate, $P(T) = e^{-z(T) T}$ |
| $f(T)$ | Instantaneous forward rate at $T$ |
| $F(T_{a}, T_{b})$ | Simple or continuously compounded forward rate between $T_{a}$ and $T_{b}$ |
| $h$ | Step of a finite-difference derivative |

Follow the task's compounding and interpolation conventions where it states them; the relations below are the continuous-compounding forms.

## 2. Forward Rates from Discount Factors

The instantaneous forward rate is the slope of minus the log discount factor:

$$
f(T) = -\frac{\mathrm{d}}{\mathrm{d}T} \ln P(T) = z(T) + T \cdot z'(T)
$$

The continuously compounded forward rate between two maturities is the average of $f$ over the interval:

$$
F(T_{a}, T_{b}) = \frac{\ln P(T_{a}) - \ln P(T_{b})}{T_{b} - T_{a}} = \frac{1}{T_{b} - T_{a}} \int_{T_{a}}^{T_{b}} f(u) \, \mathrm{d}u
$$

When $\ln P$ is interpolated linearly between nodes, $f$ is constant on each interval and equals $F(T_{i}, T_{i+1})$ there; at a node the left and right values differ, so state which one is reported.

## 3. Derivatives at the Ends of the Curve

A central difference uses points on both sides of $T$:

$$
f(T) \approx -\frac{\ln P(T + h) - \ln P(T - h)}{2h}
$$

At the last node $T_{n}$ the point $T_{n} + h$ lies outside the curve, and at the first node $T_{1} - h$ may lie before the first quote. Whatever value the interpolator returns there is not market information, so the central difference at an end node is not a forward rate. At the ends use a one-sided difference inside the curve:

$$
f(T_{n}) \approx -\frac{\ln P(T_{n}) - \ln P(T_{n} - h)}{h}
$$

or a library derivative that handles the boundary itself, such as `numpy.gradient` with `edge_order=2` on the node values. Many interpolators clamp outside their range and return $P(T_{n})$ for every $T > T_{n}$; a central difference at $T_{n}$ then mixes a zero slope with the true slope and returns about half the forward rate, or exactly zero when both sides are clamped.

## 4. Extrapolation Beyond the Last Node

Extending the discount factor flat, $P(T) = P(T_{n})$ for $T > T_{n}$, means no further discounting, so the forward rate beyond the curve is zero. The standard extension holds the forward rate constant instead (flat-forward extrapolation):

$$
P(T) = P(T_{n}) \cdot e^{-f_{n} (T - T_{n})}, \qquad T > T_{n}
$$

where $f_{n}$ is the forward rate on the last interval, or the zero rate held flat when the task says so:

$$
P(T) = e^{-z(T_{n}) T}, \qquad T > T_{n}
$$

Either extension keeps forward rates positive when the curve's rates are positive; a flat discount factor does not.

## 5. Checks and Scope

- Each forward rate should be of the same order as the neighbouring forward and zero rates; a zero, a sign change or a jump at the first or last node points to a boundary error, not to the market.
- Recompute the end-node forward rates with a one-sided difference and compare.
- Integrating the reported forward rates over $[0, T_{i}]$ should give back $-\ln P(T_{i})$ at every node.
- A model calibrated to the forward curve, such as a Hull–White drift $\theta(t)$, inherits any boundary error in $f$, so check the forward curve before using it.

## 6. References

- Hull, J. C., *Options, Futures, and Other Derivatives*, chapter on interest rates (zero rates, forward rates, the instantaneous forward rate).
- Hagan, P. S. and West, G. (2006), "Interpolation methods for curve construction", *Applied Mathematical Finance* 13(2), 89–129 (forward rates implied by interpolation schemes; flat-forward and constant-zero extrapolation).
