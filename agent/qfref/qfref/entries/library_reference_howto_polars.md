Polars 1.44.1 is installed. Use only APIs that exist in this version: not older removed forms, and not newer or unverified ones.

When the task text specifies how to build something or forbids a function, follow the task text.

# LibraryReference: Evaluate expressions and lazy grouped transformations

Polars pl.col returns Expr evaluated in select/with_columns/group_by, without a pandas row index. Use group_by, not groupby; rolling_mean uses min_samples. Sort before shift().over(...). collect executes a LazyFrame. Validate join cardinality and output order. null differs from NaN: fill_null does not fill NaN.

```python
import polars as pl
f=pl.DataFrame({'key':['a','a','b'],'v':[2,3,7]})
r=f.lazy().group_by('key').agg(pl.col('v').sum()).sort('key').collect()
assert r['v'].to_list()==[5,7]
```

## Version check: forms that fail in this version

Deprecated in Polars 1.x (still run, but emit a DeprecationWarning; a task that forbids warnings fails on them): `pl.count()` -> `pl.len()`; `join(..., how='outer')` -> `how='full'`, and `how='outer_coalesce'` -> `how='full', coalesce=True`; `with_row_count` -> `with_row_index`; `melt(id_vars=..., value_vars=...)` -> `unpivot(index=..., on=...)` (the keywords change too); `pivot(columns=...)` -> `pivot(on=...)`; `replace(mapping, default=...)` -> `replace_strict(mapping, default=...)`; `rolling_*(min_periods=...)` -> `min_samples=...`.

Removed in Polars 1.x (AttributeError or TypeError): `groupby` -> `group_by`; `cumsum`, `cumprod`, `cummax`, `cummin`, `cumcount` -> `cum_sum`, `cum_prod`, `cum_max`, `cum_min`, `cum_count`; `str.lengths` -> `str.len_bytes`, `str.n_chars` -> `str.len_chars`; `take` -> `gather`; `frame_equal` -> `equals`; `groupby_dynamic` -> `group_by_dynamic`, `groupby_rolling` -> `rolling`; `Expr.map` -> `map_batches`; `Expr.apply` -> `map_elements(..., return_dtype=...)`; `sort(reverse=...)` -> `sort(descending=...)`.

To find every remaining deprecated call, run the migrated script once with `python -W error::DeprecationWarning script.py` (warnings become errors that name the line), fix each, and repeat until it runs clean; then run it normally for the outputs. `map_elements` can emit `MapWithoutReturnDtypeWarning` (no `return_dtype`) or `PolarsInefficientMapWarning` (a native expression exists; the warning names it): replace it with the native expression.

Unavailable/wrong-object: none verified.
