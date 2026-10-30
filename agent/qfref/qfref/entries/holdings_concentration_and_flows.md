# Holdings analytics: aggregation by identifier, concentration, pairwise overlap, turnover, crowding, entity naming and proportional fund flows

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Aggregating holdings by security identifier

**Purpose:** Turn raw holding rows into one row per security identifier per book and period, with one representative label.

**When to use:** Any holdings task (13F books, fund holdings) before weights, overlap, turnover or crowding are computed.

**Constraints:**
- Aggregate by the security identifier alone (`CUSIP` or the task's equivalent key); issuer names and class labels are display attributes. Grouping by identifier plus a label splits one security into several rows and breaks every count, weight and rank built on it.
- "Latest period" is the latest of the task's stated target periods, selected by its key in the cleaned table, not the latest date found in the raw filings.

**How to implement:**
1. Check the inputs and print them: the identifier column, the value and share columns, the book key (manager or fund) and its order key, the period key and the list of target periods.
2. Sum the value columns per book, period and identifier.
3. Attach one representative label per identifier, merged back by identifier.
4. For latest-period outputs, filter the cleaned table to the latest period key first, and take every column of those outputs (dates, labels) from that filtered frame; set the period end date from the period list.
5. Write every date column in ISO 8601 form, `YYYY-MM-DD`, unless the task's own example shows another format: filing dates such as `30-SEP-2025` are converted (`pd.to_datetime(...).dt.strftime('%Y-%m-%d')`), never copied as they appear in the raw filings, because other outputs and any comparison on dates use the ISO form.
6. Take the label shown for an identifier in any summary or ranking from this cleaned table, so that one identifier has the same label in every output file.

**Limitations and cautions:** A value read with `.iloc[0]` from a frame that still holds several periods belongs to whichever period comes first.

**Double check:** Each identifier appears once per book and period, all latest-period rows share one period end date, and every date matches `YYYY-MM-DD`; if not, a label was part of the grouping key, the frame was not filtered, or a raw date was copied, so fix that step.

## Topic 2: Portfolio weights and Herfindahl concentration

**Purpose:** Compute normalized portfolio weights and the Herfindahl concentration with its effective number of positions.

**When to use:** The task asks for weights, concentration, HHI or the effective number of names of a long-only book.

**Constraints:** Weights refer to the whole book or to a selected subset as the task defines; the two give different concentrations.

**How to implement:**
1. Check the inputs: nonnegative holding values $v_i$ of one book and period (Topic 1), and whether the task restricts to a subset.
2. Weights: $w_i = v_i / V$ with $V = \sum_i v_i > 0$.
3. Herfindahl index: $\mathrm{HHI} = \sum_i w_i^2$.
4. Effective number of positions: $N_{\mathrm{eff}} = 1 / \mathrm{HHI}$.
5. Subset with weights summing to $c < 1$: raw concentration $\sum_i w_i^2$, conditional concentration $\sum_i (w_i / c)^2$; report the one the task names.

**Limitations and cautions:**
- When a task defines a fund's exposures on a selected subset, a name outside that subset has zero shares and zero dollars for that fund, even if it appears in the fund's complete list.
- When a metric's inputs are in the data, compute it rather than writing a placeholder such as zero.

**Double check:** Each book's weights sum to 1 and $1/n \le \mathrm{HHI} \le 1$ for $n$ positive positions; if not, the weights were not normalized per book and period.

## Topic 3: Pairwise weighted overlap between books

**Purpose:** Measure, for each pair of books, how much of their weight they hold in common, and count their common names.

**When to use:** The task asks for portfolio overlap, holdings overlap or common names between managers or funds.

**Constraints:**
- "One row per unordered pair" means each pair once, with the entity of the lower order key first ($i < j$), so $n$ entities give $n(n-1)/2$ rows. The order key is the task's order or identifier column of the entities, not the position of a column in a pivot table.
- Both books are normalized over the same period and aligned on the union of securities, with missing weights set to 0.

**How to implement:**
1. Check the inputs and print them: the latest-period weights of every book (Topic 1, Topic 2) and the entities' order key.
2. Sort the entities by their order key and loop over pairs in that sorted list: for positions $a < b$ in it, entity $i$ is the one at $a$ and $j$ the one at $b$. A pivot table orders its columns by label, which is not the order key, so do not take the pair order from the pivot columns.
3. Weighted overlap on the union of securities: $O_{ij} = \sum_k \min(w_{ik}, w_{jk})$.
4. Common names: the number of securities with positive weight in both books.

**Limitations and cautions:**
- Common-name counts ignore position sizes.
- Snapshot weight distance is sometimes called turnover but includes price movement (Topic 4).

**Double check:**
- Every row has $i < j$ in the order key and there are $n(n-1)/2$ rows; if not, rebuild the loop from the sorted list of step 2.
- $O_{ij} = 1 - \frac{1}{2}\sum_k |w_{ik} - w_{jk}|$ for books with unit totals; if not, the weights were not normalized or not aligned on the union.

## Topic 4: Turnover between two weight vectors

**Purpose:** Measure how much a book changed between two periods.

**When to use:** The task asks for turnover between consecutive periods of a book, or between two weight vectors.

**Constraints:** Use the formula or bound the task gives; when it only says "turnover", the common portfolio convention is the one-sided measure, and the choice is stated in a code comment.

**How to implement:**
1. Check the inputs: the two weight vectors and the period order from the task's period list.
2. Align both on the union of names, with missing weights set to 0.
3. One-sided turnover: $\frac{1}{2} \sum_i |w^{\mathrm{curr}}_i - w^{\mathrm{prev}}_i|$, in $[0, 1]$ for fully invested long-only books (a full replacement is 1).
4. Two-sided turnover, when the task defines it: $\sum_i |w^{\mathrm{curr}}_i - w^{\mathrm{prev}}_i|$, in $[0, 2]$.
5. New, exited and common names: names with positive weight only in the current period, only in the previous one, and in both.

**Limitations and cautions:** Snapshot turnover includes price drift; trading turnover is measured against drifted pre-trade weights.

**Double check:** Every turnover value lies in its range; if not, the vectors were not aligned on the union or not normalized.

## Topic 5: Security crowding ranking

**Purpose:** Rank the securities of one period by how widely and how heavily the books hold them.

**When to use:** The task asks for crowded securities, the most widely held names, or a ranked list of securities by holders.

**Constraints:**
- The primary key is the number of holders. When the task names no tie rule, ties are broken by the size measure the same table reports for those rows (the total value held), larger first, and only then by the identifier ascending: holder counts tie often, so ordering equal counts by identifier or by input row would give positions with no economic meaning.
- Positions $1, \dots, n$ follow the written row order.

**How to implement:**
1. Check the inputs and print them: the latest-period holdings by book and identifier (Topic 1), and any ranking rule or tie rule the task states.
2. Per identifier: holder count, total value, average and maximum holder weight, and the list of holders (Topic 6).
3. Sort with a stable sort by holder count descending, then total value descending, then identifier ascending, unless the task names other keys (then exactly those keys, in its order).
4. Reset the row index and number the rows $1, 2, \dots, n$ as the rank; write the table in that order.

**Limitations and cautions:**
- `rank(method="min")` repeats tied ranks and skips positions, so it never gives a complete list; `method="first"` on the primary key alone orders ties by the current row order.
- Do not invent a tie rule from an observed output, and do not round amounts to display precision to force an order. Values equal up to floating-point noise (a ratio that is the same economic fraction for every name) are ties: merge the noise before sorting, as the ordinal-ranking entry describes, then break the ties with the next key.

**Double check:** Within each group of equal holder counts, total value is non-increasing down the table, and the ranks are exactly $1, \dots, n$; if not, re-sort with all keys of step 3 and renumber.

## Topic 6: Naming entities in output fields

**Purpose:** Write fields that list or name entities (holders, members, pairs) so that they match the other outputs.

**When to use:** Any output field that names one or more funds, managers, securities or pairs, in a CSV cell or a JSON value.

**Constraints:** A field that names entities holds the identifier that names them in the other outputs (a ticker or a label), never an internal order or sequence number.

**How to implement:**
1. Check the inputs: the identifier the task uses for the entities in its tables.
2. JSON: a list of entities is a flat array of identifiers; a pair is a two-element array `[id_i, id_j]` in the order of Topic 3; a field holding one quantity per entity is an object keyed by identifier, `{id: value}`, unless the task says it is a single number.
3. CSV cell: join the identifiers with a separator that occurs in none of them.

**Limitations and cautions:** Do not write records with extra attributes (names, weights) in place of the identifier, and do not join labels with `_`, `-` or spaces, which labels themselves can contain.

**Double check:** Every identifier written in a list or pair field appears in the identifier column of another output; if not, an order number or a display name was written instead.

## Topic 7: Proportional fund flows

**Purpose:** Allocate an assumed proportional outflow of each fund to the securities it holds, in dollars.

**When to use:** The task models ETF or fund redemptions as proportional sales of holdings (sale pressure, outflow exposure).

**Constraints:** Under a pro-rata redemption the basket sold is valued at NAV, so ratios of subset dollars to a fund's redemption use redeemed NAV dollars as the base unless the task names another.

**How to implement:**
1. Check the inputs and print them: fund net assets $A_f$, full-fund weights $w_{fi}$, shares held $q_{fi}$, and outflow fractions $\rho_f$.
2. Holding dollars: $V_{fi} = A_f\, w_{fi}$.
3. Implied constituent price, for positive shares: $P_{fi} = V_{fi} / q_{fi}$; across funds, the aggregate implied price is total dollars over total shares, not the mean of the prices.
4. Dollar outflow allocated to security $i$: $\mathrm{flow}_i = \sum_f \rho_f\, V_{fi}$.
5. Parts reported side by side over one base partition it: a part specific to one fund next to the overlap part is the fund's covered amount minus the overlap amount, so the parts add back to the covered total.

**Limitations and cautions:**
- Summing only a selected universe captures only that universe's share; renormalizing the selected holdings to one reallocates the omitted exposure and changes the scenario.
- Actual ETF redemptions can transfer securities in kind; a modeled sale-pressure amount is an assumed exposure, not executed selling or price impact.
- Liquidity ratios compare compatible quantities (shares with share volume, dollars with dollar volume); there is no universal blend.
- Each rank column orders the rows by its own named metric; the position of a row in a table sorted by another key is not that rank.

**Double check:** Under a pro-rata sale, a subset's sell dollars divided by the fund's redeemed NAV dollars equals the subset's weight in the fund (within about $10^{-3}$); if not, the base or the weights are wrong.

## Topic 8: ETF premium or discount and NAV-based transfer

**Purpose:** Measure the price-to-NAV premium of an ETF and the relative transfer of a redemption.

**When to use:** The task reports an ETF premium or discount, or the transfer between market dollars and NAV dollars of redeemed shares.

**Constraints:**
- Compute derived numbers (the premium or discount transfer) from unrounded prices: a premium column in a product file is a rounded display (whole basis points, or a percent with few decimals) and can carry another sign convention.
- A field the task asks to report from the product data (a snapshot of the product file's own metrics) keeps the product file's value as given, converted only to the task's unit. A derived number, such as the premium or discount transfer of a redemption, is computed from the market price and NAV per share columns where it is written, never from a variable that holds a parsed premium or discount column.

**How to implement:**
1. Check the inputs: market price $P$, NAV per share $N > 0$, redeemed shares, and the cash-flow base the task states.
2. Relative premium: $P / N - 1$.
3. Transfer in basis points, with market dollars = redeemed shares times $P$ and NAV dollars = redeemed shares times $N$: $(\text{market} - \text{NAV}) / \text{NAV} \times 10^4$, which equals $(P / N - 1) \times 10^4$ and takes no extra redemption-fraction multiplier. Compute this derived transfer from the market price and NAV per share columns for every row; do not take the transfer from a premium or discount column of an input file, because that column is rounded for display (whole basis points, or a percent with few decimals) and can carry another sign convention. This step covers the derived transfer only: a field the task asks to report from the product data keeps the product file's value (Constraints). The value is negative when the fund trades at a discount ($P < N$); keep the sign. Print, for each fund, $P$, $N$ and the computed basis points next to the input file's premium column: the computed number has decimals and the same sign.
4. Cash buffer in basis points: net cash divided by net assets times $10^4$.

**Limitations and cautions:** Multiplying a rounded premium column by $10^4$ is not this quantity; a zero redeemed quantity leaves the cash-flow ratio undefined; NAV dollars and secondary-market traded dollars are different quantities.

**Double check:** The transfer in basis points equals $(P / N - 1) \times 10^4$ recomputed from the price and NAV columns, has decimals, and is negative for every fund whose price is below its NAV; a whole number or a positive value for such a fund means a parsed premium column was used, so recompute it from $P$ and $N$. A field reported from the product data is compared with the product file instead.

References: SEC Investor Bulletin on ETFs (https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24) for primary-market mechanics. Concentration and overlap identities follow from normalized weights and $\min(a, b) = (a + b - |a - b|)/2$; flow identities are accounting under the stated proportional scenario, not a liquidation model.
