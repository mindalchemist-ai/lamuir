# Debugging a provided pricing script against a convention contract

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

The task description inside <task_instructions>, and any conventions file it names, take priority over this card: where they state a different rule, follow them.

Use when a task gives a script that "runs but produces wrong outputs" together with a conventions file or a list of conventions in the task text. Audit explicit conventions alongside implementation correctness; do not assume either is already correct.

## Rule that is easy to miss

A value reported "from the perspective of" a party named in the inputs (pay or receive, long or short, buyer or seller) takes its sign from that input field. Find every place the script fixes such a sign in code, replace it with a branch on the input field, and after the final run print the input field next to the sign of each reported value.

## Algorithm: convention audit before editing

1. Contract: list every convention the task text and the conventions file state, one line each: instrument or leg, day count, payment frequency, schedule direction and roll, discount curve, projection curve, interpolation and extrapolation, compounding, sign or direction rule, build order.
2. For each function in the script, list every day-count call, frequency or step, curve used for discounting, curve used for forwards, interpolation call and sign choice, with its line number.
3. Build a table with one row per item: contract source, instrument or leg, function and line, actual behaviour, required behaviour, and status (match, mismatch, or unresolved when the contract is unclear; do not guess). Check each leg separately, even when two legs share a helper or a similar line.
4. Print the table. Every mismatch is a bug to fix, including rows in helper functions that look correct for another reason (for example a leg discounted on the right curve but accrued with the wrong day count).
5. Edit one writable working copy cumulatively; never restart from the original file after fixes were made. Scope each replacement to the intended function or leg, check that it matched the expected number of times, and print the resulting diff.
6. Compile and run the final edited file, and check the outputs of that run in the required directory. A successful edit message, or an output written by an earlier version, is not evidence of a fix.
7. Verify that every input instrument reprices to its quote. A matching reprice does not prove the conventions, because a bootstrap and a repricer that share the same wrong helper still agree.

## Checks after the fix

1. The audit table has no mismatch row left, and each fixed line is printed with its new value from the final file.
2. Instruments reprice to their quotes within the stated tolerance.
3. One hand calculation for a single cash flow per leg (accrual fraction, discount factor, forward) matches the script.
4. Build order: a curve used for discounting inside another curve's bootstrap is built first.
5. Direction: values reported "from the perspective of" a party use that party's sign.

## Common mistakes

- Checking which curve a function uses and not which day count it uses, or the reverse.
- Trusting a helper because its name matches the leg (an `annuity` helper can still accrue with the float-leg day count).
- Stopping after the repricing check passes.
