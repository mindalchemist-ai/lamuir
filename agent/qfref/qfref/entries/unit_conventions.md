# Unit conventions

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

## Decimal ratios, percentages and basis points

A decimal ratio expresses a proportion directly. For example, 0.075, the fraction 3/40, and 7.5% represent the same proportion.

- Percent (%) means per hundred. Multiply a percentage number by 0.01 to obtain its decimal ratio: 7.5% = 7.5 × 0.01 = 0.075.
- One basis point (bp; plural bps) equals 0.0001 as a decimal ratio. Thus 75 bps = 75 × 0.0001 = 0.0075 = 0.75%.
- Leave values already expressed as decimal ratios unchanged. A decimal point alone does not identify a ratio: 2.5 dollars is an amount, not a proportion.

## Thousand, million and billion

These words indicate numerical multiplication factors, not currencies or measurement units:

| Word | Common financial abbreviation | Multiplication factor |
| --- | --- | ---: |
| Thousand | K or k | 1,000 |
| Million | M or m | 1,000,000 |
| Billion | B or b | 1,000,000,000 |

Multiply the displayed number by the indicated factor to obtain the actual amount or quantity in base units:

- USD 2.5 million, or USD 2.5 M, means 2.5 × 1,000,000 = USD 2,500,000.
- 12 thousand shares means 12 × 1,000 = 12,000 shares.
- USD 1.2 billion means 1.2 × 1,000,000,000 = USD 1,200,000,000.

The same rule applies to a column heading such as “Amounts in millions”: every displayed amount in that column carries the factor 1,000,000, even if individual cells have no suffix. Do not apply the same factor twice when the heading and cell repeat it. Interpret abbreviations using the source documentation; these meanings are not universal outside financial amount and quantity notation.

## Applying conversions

Read the documented source unit and required output unit before computing. Do not infer units from numeric dtype, magnitude or a field name alone. Preserve raw values, convert once into clearly named working columns, and reuse those columns downstream. If the output requests millions rather than base units, convert to that requested representation when saving.

Preserve signs unless absolute values are requested: converting -2 million dollars gives -2,000,000 dollars, not +2,000,000 dollars. Ratios may also be negative or exceed one. Squaring a quantity squares its conversion factor.

## Output direction: percent, decimal or basis points

The scale of each written field is set by the task's own words for that field or for its file. The output contract in the first message lists the fields whose unit the statement states (`output_contract.describe()`), and the submission check flags a field written at another scale. A field name alone does not fix the scale: names ending in `_pct` hold percent points in some tasks and decimals in others, and a name with "pct" can also be a percentile. A negated sentence ("do not report percentages as decimals") states the opposite scale.

Compute every ratio as a decimal first; multiply by the scale chosen from the table (100 for percent, 1 for decimal, 10,000 for basis points) only when writing the field. Dividing the written value by the same scale must give back the computed ratio. Exception: when the task states a conversion formula on its own input units, apply it to the inputs exactly as given. With yields stated in percent and a basis-point change defined as `(y_after - y_before) * 100`, multiply the percent-point difference by 100; do not convert the yields to decimals and then use 10,000. Check one value by hand: a move from 4.50 % to 4.60 % is 10 bps, not 1,000 or 0.1.
