# Filing state, availability dates and financial fact context

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

Use this note when interpreting amended holdings disclosures or comparing financial-report facts. A reporting date, an event date and the time the information became public describe different things. Match each requested quantity to its period, unit, entity and disclosure scope; explicit dataset definitions govern.

## Holdings disclosures and amendments

A Form 13F position describes a quarter-end holding, not a trade on the filing date. A restatement supersedes the earlier report with corrected content; an amendment reporting additional holdings supplements the report. Its summary describes that amendment, not necessarily the reconstructed total. A summary-page total is filer-reported while each holding value is rounded, so the sum of the information-table values can differ from the reported total by a few currency units: a reconciliation of the two passes within a small tolerance (the task's, if it gives one) while the rows themselves must match exactly, and the difference is taken in the direction the task defines (state the direction used when it does not). The latest accession alone is therefore not always the complete book. A notice is not a holdings inventory. Security class, share-versus-principal units and option exposure matter when defining an equity-share universe. Key a holding by its CUSIP alone, not by issuer name or title-of-class text; add the put/call flag only when the task keeps option rows as separate positions (this is the same key as aggregating by the security identifier alone in the holdings card). The same security can be spelled differently across filings or within one filing, and keying on the name or class text splits one position into two. Audit counts of raw and effective rows describe the resolved state after each restatement or amendment is applied; they are not cumulative sums over every filing in the history.

A verified sketch for one manager and one period: apply the filings in order, an original or the first filing seen sets the book, a restatement replaces it, an additional-holdings amendment appends to it. Checked on a history of an original, a same-day restatement and an additional-holdings amendment, and on a history without the original.

For each manager and period:

1. Order the filings by filing date, then amendment number (missing counts as 0), then accession number.
2. Apply them in that order: the first filing seen, or an original report, sets the book; a restatement replaces the whole book; an amendment that adds new holdings appends its rows to the book.
3. An amendment of any other type is an error to report, not a case to guess.
4. Log one row per applied filing: accession, action (base, replace or append), rows in the filing, rows in the book after it.

Output columns that repeat an input field (accession, filing date, amendment flag, amendment number and type) keep the input's own coding: SEC flat files code flags as text such as "Y" or blank, so do not turn them into booleans or numbers in the output. Name the actions with the labels the task defines (an original setting the book and a restatement replacing it may carry different labels). After resolving, aggregate duplicate positions by CUSIP (and class) before computing weights. When the history starts with an amendment, that amendment is the base; state this.

A retrospective corrected book and an as-of information set answer different questions. At decision time t, a revision published later than t was not yet available; applying it backwards to a trading signal introduces look-ahead. An economic-period key does not itself establish public availability. Currency magnitudes must follow the filing vintage and dataset units, not a universal thousands multiplier.

## Insider ownership

Form 4 distinguishes transactions from post-transaction ownership. Code S represents a market or private sale; a disposal flag alone also includes other dispositions. Direct and indirect holdings are separate, and different indirect entities can be distinct ownership interests. Footnotes may qualify prices or beneficial ownership. Shared reporting interests can refer to the same economic shares, so summing across reporting persons can double-count.

Form 4 XML layout: transaction rows are `nonDerivativeTransaction` and holding rows are `nonDerivativeHolding` (singular tag, repeated). Coding fields such as `transactionCoding/transactionCode` hold their text directly. Dates, share amounts, prices and post-transaction amounts sit in a `value` child (`transactionDate/value`, `transactionAmounts/transactionShares/value`, `postTransactionAmounts/sharesOwnedFollowingTransaction/value`). Footnote references are `footnoteId` elements with an `id` attribute. Ownership is `ownershipNature/directOrIndirectOwnership/value` (D or I). For an indirect row, the owning entity is the text of `natureOfOwnership/value`, or the holder that a referenced footnote names. Each entity keeps its own running balance. A holding row is a static position with no transaction. Check element paths on one file with `findall` before looping, and search for the singular tag names.

For one consistent ownership bucket, let $Q_{\mathrm{begin}}$ and $Q_{\mathrm{end}}$ be its initial and final share inventories, A acquisitions, D dispositions, and J other net share changes. Inventory conservation gives:

$$
Q_{\mathrm{end}} = Q_{\mathrm{begin}} + A - D + J
$$

Only for a sale-only interval with no other changes does initial inventory equal final inventory plus sales. Repeated post-trade balances are states, not additive holdings. A static holding is not an additional transaction. Reported price ranges do not necessarily identify a unique execution price unless a weighted price is separately given.

## Financial-report facts

An XBRL concept is not a complete fact identifier: entity, period, dimensions and unit establish its meaning. Instant facts describe a date; duration facts cover an interval. Consolidated and segment facts can share labels while measuring different scopes. Comparative prior-year values in a later filing can be restated; an as-reported comparison differs from a latest-restated comparison.

An inline numeric fact may carry a sign and decimal scale. Its normalized numeric value follows those attributes and the applicable transformation; XBRL decimals expresses precision, not a magnitude multiplier. An extracted instance may already contain the normalized value. Applying a visible table multiplier again would double-scale it.

For comparable numerator G and denominator R, a margin and its reciprocal-denominator variant are different ratios. A label alone does not choose the denominator. Likewise a difference between periods is not a growth rate, and weighted average prices do not equal unweighted averages of transaction prices.

## References and limits

[SEC Form 13F FAQ, questions 58b–58c](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) explains replacement versus additive amendments. [SEC Form 4 instructions](https://www.sec.gov/files/form4.pdf), sections 4 and 8, explains ownership and transaction classifications. [SEC EDGAR XBRL Guide](https://www.sec.gov/files/edgar/xbrl-guide.pdf), especially §6.6.4, distinguishes decimals from scale. Availability-time and inventory statements above are analytical implications; this note does not define proprietary pressure scores or infer unreported transaction motives.
