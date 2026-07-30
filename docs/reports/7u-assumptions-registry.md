# §7u scope (a) — the assumptions registry

Dispatch 1 (ledger) `96ee35c` · Dispatch 2 (build) `c24c05e`

## The three artefacts

| artefact | version | entries | who may change it |
|---|---|---|---|
| `platform_defaults` | `7u-pd.1` | 10 | product, with a version bump |
| `methodological` | `7u-mc.1` | 8 | methodology owner only; each entry states why it is not client-settable |
| `seeds` | `7u-sd.1` | 7 | changed only to break a reproduction deliberately |

Plus **13 divergent identifiers** resolving the six overloaded names to distinct
keys, `tol` to one key with its caveat, and the two kd-kink constants.

**Three versions, not one** — they have different lifetimes and different rules
about who may change them, so §7s.1 pins all three. `versions()` returns them.

**Company assumptions are excluded, and a test enforces it.** They are data, not
config; they belong in the pack's input snapshot as *values*. A version string
pointing at per-company mutable data would repeat the `FinancialDataset` defect —
a pointer to a row whose contents can change underneath it.

**Seeds are included and this was not optional.** They change no methodology and
they determine a rendered number. A pack pinning every assumption and not the
seed does not reproduce.

**KFLOOR is methodological.** The reasoning lives in the artefact, not only the
ledger: a client-settable k-anonymity floor is a client-settable disclosure risk,
and the instrument's candour rests on respondents trusting a floor they do not
control.

**Keys carry meaning.** Every entry states what it governs and who consumes it;
a test fails any entry that does not. A registry of bare numbers is how six
identifiers became ambiguous in the first place.

## The empty-diff proof

Asserted two ways.

1. **No compute-path file was modified.** The lane adds a registry, a guard and
   tests. `git diff --name-only` against the compute modules returns nothing, so
   every rendered figure is identical by construction rather than by comparison.
2. **Parity at the source.** 18 parametrised tests assert each registered value
   equals the constant the code actually uses. If adopting the registry would
   move a number, these fail — which is the assertion made *before* a pack ever
   reads the registry, not downstream of one.

Corpus digest recorded for future values-change lanes: `auto_forecast` over the
stored corpus, **16 evaluated, 20 skipped-and-named**, digest
`35fa9262e7af3b0c608748a2c66fedfb`.

## The coverage guard and its control

`scripts/check-assumption-registry.py`. Per III.4 it does **not** compare the
registry against a list — whatever enumerates the list is itself hand-synced, and
"40 registered, 40 confirmed" prints the same tick either way. It **scans the
code** for module-level numeric constants across eight compute modules and fails
on any without a registry entry.

**Matched by value, not by name**, deliberately: a name-keyed check would call
`sigma` covered because *some* `sigma` is registered, which is precisely the
collision the registry exists to end.

**Known-positive control on every invocation** — an unregistered constant is
planted in a throwaway module and the guard must go red. A coverage guard that
has never rejected anything is indistinguishable from one that cannot.

**It fired on its first run**, finding `LEV_KD_KINK` and `LEV_KD_COEF`
unregistered. CORE routes the kd kink's *duplication* to sole ownership, not to
config versioning — but a pack must still *pin* those values, because they
determine a rendered number. Pinning a value is not resolving a duplication.
Both are now registered with the routing note; both rulings stand.

## Verification

- `tests/unit/test_assumptions_registry.py` — **28 tests**
- backend suite — **932 passed, 3 xfailed**
- **ten gates green**, registry guard wired into `.github/workflows/ci.yml`

One self-caught instrument error: the first parity test indexed `gbm_valuation`'s
return as a dict when it returns a tuple. The shape is now asserted in the test
rather than assumed — fifth self-caught instrument error this era.

## Not in scope

§7u scope (b) remains deferred. `revenue_growth`'s `0.03` site still needs its
own review **before §7p ships** — §7p's greenfield path produces exactly the
shape that makes the fallback reachable.
