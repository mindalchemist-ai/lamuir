# Financial reports: fact context, scale and comparable fundamentals

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input or convention, follow the task description. A requested quantity must match concept, entity, segment, period and unit. Explicit definitions decide the comparison; an ambiguous label does not justify a convenient nearby number.

## Topic: Fact identity and period

**Purpose:** Pick the fact whose concept, entity, period, dimensions and unit match the request.

**When to use:** Reading annual reports, inline XBRL facts and statement tables.

**How to implement:** A fact = concept + entity + period + optional dimensions + unit. An instant fact is a balance at a date; a duration fact is a flow or average over an interval. Match the requested period type. Dimension members identify a security class, segment or geography. Distinguish as-reported from latest-restated comparisons when a newer filing restates a prior year.

**Limitations and cautions:**

1. Fiscal year, calendar year, filing date and cover-page disclosure date can differ.
2. Context identifiers are local labels, not globally meaningful dates.
3. Removing dimensions can turn a class-specific fact into an unrelated consolidated one.
4. Equal values under different contexts are not interchangeable.
5. Missing, nil, explicit zero and a textual dash need not mean the same thing.

**Double check:**

1. Each selected value has the requested entity, scope, period and unit.
2. Restated versus as-reported basis matches the request.

## Topic: Numeric scale, sign and units

**Purpose:** Convert displayed or tagged numbers into correct normalized values.

**When to use:** Any numeric fact or table cell.

**How to implement:** For a non-fraction inline numeric fact, let $a$ be the magnitude after the specified locale transformation, $s$ the decimal scale, $\epsilon\in\{-1,1\}$ the explicit sign:

$$
v=\epsilon a\,10^s
$$

The transformation determines the lexical number. The decimals attribute is rounding accuracy, not a multiplier. Check units separately from scale: currency, shares, currency per share, area and counts are different types.

**Limitations and cautions:**

1. Display parentheses, percent marks and comma punctuation are not universal parsing rules.
2. An extracted XBRL instance may already hold normalized $v$; applying table scale again double-scales it.
3. A percent in prose and a dimensionless ratio in a tagged fact can differ by a factor of $100$.
4. A table-level unit heading can apply only to some columns or exclude per-share figures. Never infer area scale from currency headings.
5. A sign in a calculation relationship is an aggregation weight; it does not negate the stored fact.

**Double check:**

1. Scale was applied exactly once.
2. Unit type and sign match the request.

## Topic: Statement arithmetic, margins and cashflows

**Purpose:** Compute profit measures and margins with the right denominator and sign.

**When to use:** Revenue, cost, profit, margin or cashflow quantities are requested.

**How to implement:** For compatible revenue $R$, cost of sales $C$, operating expense $E$:

$$
G=R-C,\qquad O=G-E
$$

Margins: $m_R=G/R$ and $m_C=G/C$. For nonzero denominators $m_C=m_R/(1-m_R)$. Additional operating gains or losses need their statement lines; net income also reflects non-operating items and taxes. Statement arithmetic and the requested sign convention determine the sign.

**Limitations and cautions:**

1. A phrase referring to cost must not be replaced by the revenue denominator.
2. A sales amount, a profit amount and a margin percentage are distinct, even if a field label loosely says margin.
3. Operating cashflow is not operating income.
4. Investing cashflow can include acquisitions and disposals beyond capital expenditure.
5. Signs of cash-flow lines, by where the number comes from:
   - From a tagged XBRL fact: keep the stored signed value. `NetCashProvidedByUsedInInvestingActivities` (and its operating and financing counterparts) is negative for a net outflow even where the statement's row reads "Net cash used in investing activities": that row uses a negated label, which changes the display (parentheses or a positive figure), not the fact.
   - When the task asks for the amount as displayed, or for an outflow as a positive magnitude, report the magnitude.
   - A difference between periods or filings (B minus A) is taken between the same signed values; subtracting two outflow magnitudes gives the opposite sign.

**Double check:**

1. The denominator matches the wording.
2. Sign matches the requested convention.

## Topic: Aggregation, differences and averages

**Purpose:** Aggregate and compare amounts on a consistent basis.

**When to use:** Weighted prices, inclusive/exclusive totals, segment sums, per-location averages, period comparisons.

**How to implement:** With quantities $q_j$ and per-unit prices $p_j$ on a consistent basis and positive total quantity:

$$
\bar p=\frac{\sum_jq_jp_j}{\sum_jq_j}
$$

If inclusive total $A$ and exclusive amount $B$ share scope and period, the excluded component is $A-B$. Average area per location = total area / matching location count. For comparable amounts $x_A,x_B$:

$$
\Delta x=x_B-x_A,\qquad g=\frac{x_B-x_A}{x_A}
$$

For decimal ratios the percentage-point change is $100(x_B-x_A)$. Rate averages need the stated exposure or time weights.

**Limitations and cautions:**

1. Displayed average prices may be rounded, so price times displayed count need not equal reported total consideration.
2. Repurchases, equity awards, weighted-average diluted shares and period-end shares are different populations.
3. Share counts can change through splits without a cashflow.
4. Do not sum segment totals without checking overlaps and consolidation eliminations.
5. Do not take an unweighted average across differently sized groups.
6. $g$ needs $x_A\ne0$ and is awkward for a negative base.
7. Percentage-point change is not relative percentage change.
8. When an average is disclosed, use the disclosed value; when it must be computed, compute it by the stated definition. The two can differ by rounding. Use the same kind of value for every report of one field: when one report discloses an average and the other is read the same way, do not derive the other report's figure as total divided by count.
9. Read each report's own current-period column for its period values: report B's prior-year comparative is a restated view of report A's period, used only when the task asks for restated values. Print, for one field, report A's current value next to report B's comparative; if they differ, keep report A's own figure.

**Double check:**

1. Components and totals share scope, period and basis.
2. The difference type (absolute, relative, percentage-point) matches the request.

## Topic: Filing-bundle extraction workflow

**Purpose:** Extract requested fields from filing bundles into the required JSON, saved incrementally.

**When to use:** Inline-XBRL filing bundles (zip) with a required results file.

**How to implement:** Use this workflow directly; no separate written plan. Choose field groups from the request. Steps may share a cell; they do not each need a reply.

1. Locate and parse the reporting documents once. Continue only after fact contexts and numeric units resolve.
2. Build reusable fact and table indexes. Match requested quantities to period, scope and unit; use narrative/table evidence when tagged facts are absent.
3. Process a coherent group of quantities across the reports. Verify source evidence, update the results dictionary, save before the next group. Preserve earlier verified values; track unresolved requests separately and follow explicit missing-value requirements without inventing entries.
4. Compute comparisons from compatible normalized values. Check required fields, JSON types and unresolved items, then save again. After a correction, refresh dependent comparisons and outputs.

Step 1 when the first message says `read_filing` is installed (call it instead of writing a parser):

Open the filing with the provided helper `filing_io.read_filing(zip_path)`, which returns the bundle's inline-XBRL document with its facts, tables and visible text; print its `check` (fact counts, context and unit resolution, conversion statuses). Keep the results in `autosave_json(path)`, a dictionary whose file is rewritten after every assignment.

Put each value into `results` as soon as it is verified (`results["<key>"] = value`); no separate save step is needed. Each item of `doc.facts` keeps concept, context, period, members, unit and conversion status; `doc.tables` keeps rows with column positions; `doc.text` omits the header block, scripts and hidden content. Use `doc.find_facts`, `doc.find_rows`, `doc.search_text` rather than new parsing code.

Step 2 with `read_filing`: find tables for a whole group of items, both reports in one cell, and print each table compactly. Table indices differ between reports. Facts and cells are plain dicts and lists (`f["concept"]`, `t["rows"]`).

Search the tables of each document for the row-label words of every requested item of a group at once with `doc.find_tables(words)`, and print each match with `doc.show_table(index)`, which shows the unit notes and then each row as "row: cell | cell".

`show_table` drops empty cells: a row reads label, then values in header order. Read the year order from the header rows above. Apply the stated unit note to every amount from that table; `t["values"]` gives the full value of a tagged cell.

**Limitations and cautions:**

1. Continue only when both fact counts are positive and both resolved shares are 1.0; otherwise fix the parse first.
2. If a structural check fails, repair that step; do not continue with guesses.
3. Reuse existing indexes and verified results.
4. Table indices differ between reports; look them up in each.
5. Keep unresolved fields out of verified `results`; never fill the template with guessed metadata to satisfy a check.

**Double check:**

1. Required fields, JSON types and unresolved items are checked before finishing.
2. After any correction, dependent comparisons were refreshed and the file saved again.

## Topic: Field selection and value normalization

**Purpose:** Verify that each chosen value matches the request, then normalize it.

**When to use:** Before assigning any value into `results`.

**How to implement:** Copy this pattern per verified field. Fill the evidence from the request, table headers and referenced footnotes before assigning. These are local helpers, not `filing_io` methods. Search routes are hints; follow cross-references and inspect the matching disclosure.

Selecting and normalizing a reported value:

1. Search routes: look for each kind of item in the sections that usually hold it: operating footprint in Business and Properties; monthly repurchases in Issuer Purchases of Equity Securities; segment profit in Segment and Management's Discussion; capital spending in Liquidity and Capital Resources and Segment; consolidated cash flow in the Consolidated Statements of Cash Flows; rate-specific debt in Market Risk, Borrowings and Debt; equity awards in Share-based or Stock-based Compensation.
2. Before taking a cell, resolve the request on every dimension (metric, scope, period, basis, row and unit) and confirm the evidence matches each one. The metric distinguishes quantity, expense, fair value, area, principal and rate; the basis distinguishes GAAP, adjusted, period-end and period-average; the row distinguishes ending nonvested, granted, vested and forfeited. Record the source (document, heading, row and column) and read every applicable header footnote.
3. For every currency or count field, print the raw cell, the unit note that applies (for example "(Amounts in millions)"), the multiplier used and the heading of the statement or note it was read from; that heading belongs to the statement the field name names. Before writing, for every required key still `None`, look for a computed value stored under a nearly identical name (`difflib.get_close_matches(key, results.keys())`): a match means it was stored under a misspelled key, so store it under the required key. Normalize only after verifying the cell's unit and scale. A tagged (already normalized) value is used as it is, with multiplier 1; do not apply its display sign or scale again. A displayed cell: remove thousands separators, read parentheses as a negative sign, then multiply by the unit multiplier from the unit note. Never infer an area scale from currency headings. Return the absolute value only when the request explicitly asks for an unsigned figure.
4. Prefer a directly disclosed component or average with the same definition. Derive a component (including minus excluding) only when both are on the same basis and differ only in that component; derive an average (total over count) only for the same population and date, with a positive count.
5. Store each value with the JSON type the schema requires.

For consolidated measures use the financial statement and supporting notes before a summary; a requested segment or adjusted measure uses its matching disclosure. Disclosure bases: Form 10-K Items 1, 2, 5, 7, 7A and 8; Regulation S-K Items 102, 303 and 305; ASC 230-10-45-10 and 45-24; ASC 280-10-50-22, 50-25, 50-29 and 50-30; ASC 718-10-50-2. The selection checks and helpers are extraction strategies, not prescribed accounting procedures.

**Limitations and cautions:**

1. An award category alone identifies neither a quantity nor an ending balance; resolve the requested measure and activity row first.
2. Pair rate-specific debt principal with the rate for the same category, date and column. Distinguish maturity totals, fair values and period-average balances; read the rate assumptions.
3. Do not average displayed rates without weights.
4. Prefer a directly disclosed value with the same definition; derive only when permitted and compatible.
5. Never take the first keyword hit without matching metric, scope, period, basis, row and unit.

**Double check:**

1. `verify_selection` passes with evidence recorded (document, heading, row, column, footnotes).
2. The value uses the JSON type the schema requires; an integral-valued float stays a float when required.

## Topic: Tagged facts, prose and fallback parsing

**Purpose:** Build reliable fact and table indexes, and read untagged items from text.

**When to use:** Building indexes when `read_filing` is unavailable, a concept search finds nothing, or an item lives in prose or narrative tables.

**How to implement:** Step 1 in code, only when `read_filing` is not available:

Reading inline XBRL without the helper:

1. Read the zip members directly (no shell unzip); the main document is the HTML member containing `ix:header` (exhibits have none).
2. Parse it in XML mode (`BeautifulSoup(raw, "xml")`) so that names stay as written: `nonFraction`, `contextRef`, `unitRef`.
3. Index the contexts by id and collect the unit ids.
4. Collect every `nonFraction` and `nonNumeric` fact as a list (repeated facts are all kept) with its concept name, context, unit, scale, format, sign and text.
5. Check: the counts of numeric and non-numeric facts, the share of facts whose context resolves, and the share of numeric facts whose unit resolves.

Print `check`; continue only when both fact counts are positive and both resolved shares are 1.0. A context's members are `contexts[id].find_all("explicitMember")`; its period is in `startDate`/`endDate` or `instant`. Key each fact by concept name plus `contextRef`; use members to separate facts sharing a concept (per security class, per period). Apply each fact's `format` transform and `scale` before using the number. Keep concept, context, unit, raw text, transformation, scale, sign and nil status; keep repeated observations and resolve duplicates by meaning and consistency. Connect related disclosures through compatible contexts and dimensions. Use tagged facts and narrative/table evidence as complementary sources. The table index keeps table identity, row labels, headers, cell positions, spans and surrounding unit notes. Keep provenance for verified observations.

**Limitations and cautions:**

1. An HTML parser lowercases names (`nonfraction`, `contextref`), so a query in original case silently finds nothing.
2. Do not key facts by concept name alone; it drops contexts and repeated facts.
3. Facts can nest (`ix:nonNumeric` may contain other facts); use a parser, not a regular expression.
4. Many items are not tagged (officer names and ages, square footage, narrative-table figures). If a concept search finds nothing, do not try more concept names; read the HTML text or table rows around the item's heading, using the table's stated unit.
5. Job titles, officer ages, security descriptions and policy statements can come from prose. Interpret text at its stated date and scope; a named officer's age is not automatically the age of the role's current holder at another date.
6. Inline continuation chains can join text separated in the HTML; excluded text is not part of the tagged fact.
7. Presentation position or taxonomy label alone does not show the company reported a value; taxonomy definitions do not replace the issuer's facts.
8. Never substitute a year embedded in a label for an instrument's identity.
9. Do not use plain `get_text` as a visibility filter: for prose search, build a separate narrative view without scripts, styles and hidden content, but keep hidden inline facts in the fact index.
10. Preserve percent marks and negative parentheses until interpretation; dropping blank cells or currency symbols must not break column alignment.
11. Layouts change between filings; match by meaning, not by column number.

**Double check:**

1. Sample a few instant/duration periods and dimensional members; a large fact count with missing contexts is an extraction failure.
2. Prose-derived values were read from the right section, date and scope.

## References

[XBRL International: iXBRL Tagging Features](https://www.xbrl.org/guidance/ixbrl-tagging-features/), transformed values and scale versus accuracy. [Inline XBRL 1.1 specification index](https://specifications.xbrl.org/work-product-index-inline-xbrl-inline-xbrl-1.1.html), typed facts and continuation semantics. [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), fact contexts, units and submissions. [SEC Guide to Financial Statements](https://www.sec.gov/about/reports-publications/beginners-guide-financial-statements), statement distinctions.
