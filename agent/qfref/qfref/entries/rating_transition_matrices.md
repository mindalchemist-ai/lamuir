# Rating transition matrices: count matrices, cohort and pooled estimates, multi-year default probabilities, homogeneity tests and generator matrices

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Count matrices on a target rating scale

**Purpose:** Turn published transition tables with a fine rating scale into count matrices on the target scale, one per cohort.

**When to use:** The inputs are rating transition tables (counts or rates) per year or cohort, possibly on a finer scale than the one the task asks for.

**Constraints:**
- Map every source rating to exactly one target rating, as the task states (for example notches and sub-grades of the lowest grades merged into one distressed bucket, and every default-type code into Default).
- Withdrawn or not-rated outcomes are censored: they leave the sample and are not a destination, unless the task says otherwise; they enter neither the numerators nor the row totals.
- Default is absorbing: the Default row has a single count or probability in the Default column.
- A cohort contains the issuers rated (not in default) at the start of its period, as in rating-agency static-pool studies: issuers already in default are not cohort members. Cohort sizes, transition counts and any total number of transitions or issuers cover the non-default starting ratings only; the Default row comes from the absorbing convention, not from counted issuers.

**How to implement:**
1. Check the inputs and print them: each file's separator, header and first column (the beginning-of-period rating), the destination columns, whether cells are counts or percentages, and the task's mapping.
2. For each cohort, sum the source rows and columns into the target scale with the mapping; drop the censored columns.
3. When the task supplies defaults counted elsewhere (defaults not visible in the transition table, for example issuers withdrawn before defaulting), add the difference between those defaults and the visible ones to the Default column of the matching row, as the task describes. These issuers were rated at the start of the period (the transition table had moved them to a withdrawn column), so they are cohort members: after the move they are part of their row's total and of the cohort size.
4. Cohort sizes: the non-default row totals of the corrected count matrices of step 3. Build the cohort-size table once from them and print it; every reported total of transitions or issuers is the sum of that same table (`sizes[rating_columns].to_numpy().sum()`), not a second count over the raw files or over all rows.

**Limitations and cautions:** Percent tables must be converted back to counts with the row's issuer count before pooling; pooling percentages weights small cohorts as much as large ones.

**Double check:** Each count is a non-negative integer and the sum of all row totals equals the total number of transitions reported anywhere else in the outputs; if two totals differ, they count different rows (for example with or without the Default row), so state which and derive both from the same counts.

## Topic 2: Cohort and pooled transition matrices

**Purpose:** Estimate one-period transition probabilities per cohort and pooled over cohorts.

**When to use:** The task asks for annual transition matrices or an average transition matrix.

**How to implement:**
1. Cohort matrix: $P^{(t)}_{ij} = C^{(t)}_{ij} / \sum_k C^{(t)}_{ik}$ for rows with a positive total.
2. Pooled (issuer-weighted) matrix: $\bar{P}_{ij} = \sum_t C^{(t)}_{ij} / \sum_t \sum_k C^{(t)}_{ik}$, the same as summing the count matrices first; it differs from the plain mean of the cohort matrices.
3. Set the Default row to the unit vector of the Default column.

**Limitations and cautions:** A row with no issuers in a cohort has no probabilities; leave it out of that cohort rather than writing zeros that would later be averaged.

**Double check:** Every row sums to 1 within rounding and every entry lies in $[0, 1]$; if not, a censored column was kept in the totals or a row total is zero.

## Topic 3: Multi-year cumulative default probabilities

**Purpose:** Project default probabilities over several years from a one-year matrix under the Markov assumption.

**When to use:** The task asks for default probabilities accumulated over several periods.

**How to implement:**
1. Check the inputs: the one-year matrix (Topic 2) and the horizons.
2. $PD_i(h) = [\bar{P}^h]_{i,\mathrm{Default}}$, with `numpy.linalg.matrix_power(P, h)`.

**Limitations and cautions:** The projection assumes time-homogeneous Markov transitions; Topic 4 tests that assumption across cohorts.

**Double check:** $PD_i(h)$ does not decrease with $h$ for every rating and, for a monotone matrix, increases from better to worse ratings; if it decreases with $h$, the Default row is not absorbing.

## Topic 4: Chi-square homogeneity test of transitions across cohorts

**Purpose:** Test whether the transition distribution out of one rating is the same in every cohort (time homogeneity of the Markov chain).

**When to use:** The task asks to test the Markov property, stationarity or homogeneity of transitions across years.

**Constraints:**
- One contingency table per starting rating, with one row per cohort and one column per destination rating, filled with counts (not probabilities).
- Apply the column and row filters the task states before testing (for example dropping destination columns whose total count is below a minimum), and always drop rows (cohorts) and columns whose total is zero: an all-zero row or column has zero expected counts, which the test cannot use.
- When fewer than two rows or two columns remain, the test has no information: report statistic 0, degrees of freedom 0 and p-value 1 (and no rejection), unless the task defines another value. Never write a negative or placeholder number for a statistic, degrees of freedom or p-value.

**How to implement:**
1. Check the inputs and print, per starting rating, the table's shape before and after the filters.
2. `scipy.stats.chi2_contingency(table)` returns the statistic, the p-value, the degrees of freedom $(r - 1)(c - 1)$ and the expected counts; it applies Yates' continuity correction only when the degrees of freedom equal 1 (`correction=False` turns it off), so use the setting the task names.
3. Reject at the task's significance level when the p-value is below it.

**Limitations and cautions:** Sparse cells make the chi-square approximation unreliable, which is why minimum-count filters exist; with the filters the test covers only the remaining destinations.

**Double check:** For every rating the statistic is non-negative, the degrees of freedom equal $(r - 1)(c - 1)$ of the filtered table and the p-value lies in $[0, 1]$; if not, a placeholder or an unfiltered zero row slipped in, so rebuild the table.

## Topic 5: Generator matrix by matrix logarithm

**Purpose:** Estimate a continuous-time generator $Q$ with $\bar{P} \approx e^{Q}$.

**When to use:** The task asks for a continuous-time generator or transition intensities.

**Constraints:** A valid generator has non-negative off-diagonal entries, non-positive diagonal entries and rows summing to zero; the Default row is zero.

**How to implement:**
1. $Q = \log \bar{P}$ with `scipy.linalg.logm`, keeping the real part (discard an imaginary part of rounding size; a large one means the logarithm does not exist as a real generator).
2. Regularize as the task states; the common fix sets negative off-diagonal entries to 0 and then sets each diagonal entry to minus the sum of the row's off-diagonal entries.
3. Set the Default row to zero.

**Limitations and cautions:** The regularized $Q$ no longer reproduces $\bar{P}$ exactly; $e^{Q}$ (`scipy.linalg.expm`) differs from $\bar{P}$ by the size of the removed entries.

**Double check:** Row sums of $Q$ are 0 within rounding, off-diagonals are $\ge 0$ and $\|e^{Q} - \bar{P}\|$ is small; if not, the regularization step was skipped or applied before taking the real part.

## Topic 6: Comparing with a reference transition matrix

**Purpose:** Compare an estimated matrix with a published long-run matrix on the same scale.

**When to use:** The task gives a reference matrix (often in percent and with a not-rated column) and asks for deviations.

**How to implement:**
1. Drop the not-rated column, convert percentages to probabilities and renormalize each row to sum to 1, the same withdrawal treatment as the estimate.
2. Align rows and columns by rating label, not by position.
3. Signed deviation $\Delta_{ij} = \bar{P}_{ij} - P^{\mathrm{ref}}_{ij}$.

**Limitations and cautions:** A reference built over a different period or region differs for economic reasons, not only estimation error; large deviations in the default column of speculative grades are expected in stress years.

**Double check:** Both matrices are row-stochastic on the same labels before the subtraction; the deviations of each row sum to 0.

References: Jafry and Schuermann (2004), Measurement, estimation and comparison of credit migration matrices, Journal of Banking and Finance 28(11); Israel, Rosenthal and Wei (2001), Finding generators for Markov chains via empirical transition matrices, Mathematical Finance 11(2); Lando and Skodeberg (2002), Analyzing rating transitions and rating drift with continuous observations, Journal of Banking and Finance 26.
