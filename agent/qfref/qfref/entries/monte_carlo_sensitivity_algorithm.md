# Monte Carlo sensitivities by bump-and-revalue, and AR(1)/OU fits from dated observations

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, a bump or a convention, follow the task description.

## Algorithm 1: bump-and-revalue with common random numbers

Inputs: a pricing model with parameters $\theta$, bump sizes, a seed, and the numbers of paths and steps.

1. Create the generator from the seed and draw the standard normals $Z$ once, in the shape the base price uses.
2. Write the pricer as a function of $(\theta, Z)$ that simulates every path from $Z$ only, with no call to the generator inside.
3. Base price: $V_0 = \mathrm{PRICE}(\theta, Z)$.
4. For each sensitivity, take the absolute bump $h$ (for a relative bump of $p$ percent, $h = \theta_i p/100$), price $V_{\pm} = \mathrm{PRICE}(\theta_i \pm h, Z)$, and set the sensitivity to $(V_{+} - V_{-})/(2h)$.
5. Report the base price and every sensitivity.

The base price must equal PRICE(theta, Z) with the same Z, so that the base and the bumped prices share every random draw. A pricing function that keeps drawing from a shared generator gives every call different numbers; the difference of two prices is then dominated by noise and can have the wrong sign.

## Checks

1. Repeating PRICE(theta, Z) returns the identical number.
2. The sign of each sensitivity matches the payoff: for example a call on heating degree days, $\max(T_{\mathrm{base}} - T, 0)$ summed, loses value when temperatures rise, so its temperature delta is negative.
3. With a second seed (same number of paths) each sensitivity stays within a few standard errors.

## Algorithm 2: AR(1) / discretized OU fit on dated observations

Inputs: dated values $x(\text{date})$, an optional group (for example the year), and the step $\Delta t$.

1. Sort by group, then by date.
2. Form pairs $(x_t, x_{\mathrm{next}})$ only where the next date is exactly one step later and both rows are in the same group.
3. Regress $\Delta x = x_{\mathrm{next}} - x_t$ on $x_t$ with an intercept: $\Delta x = \alpha + \beta x_t + \varepsilon$.
4. Map to the continuous model: $\kappa = -\beta/\Delta t$ and $\sigma = \mathrm{sd}(\varepsilon)/\sqrt{\Delta t}$ with divisor $n-1$, or the mapping the task states.
5. Print the number of pairs and compare it with the count the calendar implies.

Merging or grouping can reorder rows; sort again before forming pairs. A shift by one row is a one-step lag only after sorting and only where no date is missing.
