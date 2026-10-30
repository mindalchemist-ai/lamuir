# Security events, earnings comparisons and contingent claims: splits and dividends, earnings surprise, complementary event claims, offering sizes and information dates

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Read the topics relevant to the task; a task usually needs several of them.

## Topic 1: Splits, dividends and share units

**Purpose:** Express prices, share counts, volumes and dividends on one consistent share basis across splits.

**When to use:** The data contains splits or cash dividends and the task asks for adjusted prices, adjusted volumes, holding-period returns or dividends per original share.

**Constraints:**
- A split with ratio $R > 0$ new shares per old share leaves ownership unchanged: $n_{\mathrm{new}} = R\,n_{\mathrm{old}}$ and $P_{\mathrm{new}} = P_{\mathrm{old}} / R$; volume in new-share units is multiplied by $R$.
- A dividend applies to the shares outstanding on its ex-date; the ex-date, record date and payment date are different dates.
- When the task defines a dividend total itself (for example as the sum of the dividend amounts as given, before adjustment), report exactly that definition: the plain sum of the amounts, with no split conversion, even when the field is named per original share.
- Only when the task asks for an economic total per original share without defining it are later dividends converted with the splits before them (step 2); that total is computed in its own loop, separate from any price-adjustment loop.

**How to implement:**
1. Check the inputs and print them: each action's type, ex-date and ratio or amount, sorted by ex-date, and which share basis the task asks for.
2. Dividend total: first read how the task defines it. If it is the sum of the amounts as given (pre-adjustment), `total = sum(amount for each dividend)` and this step ends. Otherwise, for an economic total per original share, as a line-by-line algorithm in its own loop:
   - `splits = sorted((ex_date, ratio) for each split)` and `total = 0.0`
   - `for ex_date, amount in sorted(dividends):`
   - `    factor = prod(ratio for d, ratio in splits if d <= ex_date)` (1 when no split is on or before the dividend)
   - `    total += amount * factor`
   A dividend before any split is already per original share (factor 1).
3. Back-adjusting prices (processing actions backward in time) keeps its own running split and dividend factors for the prices; it does not touch `total`.
4. Holding-period return of one share with no split, initial price $P_0$, final price $P_1$ and cash dividend $D$: $R = (P_1 + D - P_0)/P_0$. With splits, first express the final holding and every dividend in original-share units (steps 2 and 3).

**Limitations and cautions:** A backward-adjusted price is a constructed series, not a traded price; vendors use different reference prices and reinvestment assumptions.

**Double check:** Print the task's sentence that defines the dividend total next to the reported number; a total defined as the sum of the amounts equals that sum exactly. For an economic per-original-share total, print each dividend's date, split product and result; a dividend dated before a split has split product 1.

## Topic 2: Earnings surprise

**Purpose:** Measure how far reported earnings differ from a comparable expectation.

**When to use:** The task compares reported EPS with a consensus estimate or classifies beats and misses.

**Constraints:**
- Reported EPS $A$ and estimate $E$ must agree on EPS definition, share basis, currency, fiscal period and information date.
- Unscaled surprise: $U = A - E$.

**How to implement:**
1. Check the inputs and print them: the EPS and estimate columns, the period keys used to match them, and the scaling the task names.
2. Match each report to its estimate for the same period; compute $U$.
3. Standardize only with the denominator the task names: analyst-estimate dispersion and the historical variability of seasonal earnings changes give different standardized surprises.
4. Apply the task's rule for a zero or near-zero denominator and its classification thresholds.

**Limitations and cautions:** A dispersion denominator is not the standard error of the consensus mean; a percentage surprise against a near-zero benchmark is unstable even with a deterministic rule.

**Double check:** The sign of $U$ agrees with each beat or miss label; a zero denominator never produces an infinite or `nan` score unless the task asks for one.

## Topic 3: Complementary event claims

**Purpose:** Value a YES claim and its NO complement on the same event and judge whether their prices are consistent.

**When to use:** The task compares prices of binary event contracts, possibly on different venues.

**Constraints:**
- With event indicator $I$, a unit YES claim pays $I$ and its complementary NO claim pays $1 - I$ at the same settlement date, so together they pay 1.
- With discount factor $D(t, T)$, matched settlement and no costs, their combined value is $D(t, T)$.

**How to implement:**
1. Check the inputs: the event definitions, cancellation terms, settlement currency and settlement dates of both claims; they are complements only when all agree.
2. Combined price $=$ YES price $+$ NO price; compare it with $D(t, T)$ (with 1 when the task ignores discounting).
3. Subtract the fees and costs the task states before calling a gap a profit.

**Limitations and cautions:** A quote dislocation is not automatically executable arbitrage: liquidity, funding, outcome disputes and venue credit risk matter. Trading close, event resolution and cash settlement are different times; a settled receivable is not necessarily reusable cash at once.

**Double check:** Each pair compared refers to the same event; a combined price far from 1 for many pairs suggests mismatched events or quote units (cents versus dollars).

## Topic 4: Debt and equity offering sizes

**Purpose:** Separate an offering's base size from the amount sold under the underwriters' option.

**When to use:** A filing reports an offering with an over-allotment (greenshoe) or initial purchasers' option and the task asks for an offering size.

**How to implement:**
1. Find the sentence giving the total and the amount sold under full or partial exercise of the option.
2. When the total "includes" the option amount, base size $=$ total $-$ exercised amount.
3. Report the size the task asks for (base, before over-allotment, or total, including it) and quote the sentence that splits them.

**Limitations and cautions:** A later filing can report a further exercise of the option; use the filing the task names.

**Double check:** The reported size is either the stated total or the total minus the option amount, never a number not in the filing's arithmetic.

## Topic 5: Availability dates and measurement periods

**Purpose:** Place filings and facts on the date they became known, separate from the period they measure.

**When to use:** The task builds signals or event windows from filings, amendments or reported facts.

**Constraints:**
- A filing's fiscal period says what it measures; its publication time says when it can first enter the information set.
- An amendment changes available knowledge from its own availability date, unless the task uses a revised-history dataset.

**How to implement:**
1. Check the inputs and print them: for each fact, its period end, filing or acceptance date, and form type (original or amendment).
2. Use the availability date for signal timing; use the period for matching like with like.
3. Compare facts only when units, consolidation scope and duration agree, not merely their label.
4. Align signal dates, active positions and return periods on the same timeline.

**Limitations and cautions:** Same-period facts with different units, consolidation scope or duration do not become comparable merely by sharing a label; a revised-history dataset already contains later knowledge.

**Double check:** No signal uses a filing dated after the signal date; print the count of facts dropped by this rule.

References: [Investor.gov, Stock Split](https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split); [SEC, EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). The holding-return and complementary-payoff identities are direct cashflow accounting.
