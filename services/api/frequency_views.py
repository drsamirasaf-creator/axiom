"""Frequency views — the same statements read at a coarser or finer grain.

⭐⭐ THREE VIEWS, NOT FOUR (ruling 2, 6 Aug). Semi-annual is DROPPED: it exists in
neither `PERIODS_PER_YEAR` nor `periods.py`, so it is a real build — derivation,
encoder, label formatter and divisor map — for a frequency almost nobody reports
on. Monthly, quarterly and annual all exist already.

⭐ A VIEW FINER THAN THE DATA IS DISABLED AND SAYS WHY. Quarterly data enables
quarterly and annual; annual enables annual alone. ⛔ The disabled view is
RENDERED as disabled with its reason, never hidden — a missing option reads as a
product that cannot do it, and this one can, for a dataset that supplied the
grain.

## ⭐⭐ AGGREGATION OBEYS THE DECLARED CLASSIFICATION, NEVER A NAME

Every registry token declares `aggregation` (ruling 3). ⛔ **Nothing here infers
it.** A prefix rule gets `mk.dps` wrong, gets `sa.arr` wrong, and cannot classify
`po.days_in_period` at all. Flows SUM; stocks take the CLOSING sub-period; derived
lines are RECOMPUTED from aggregated inputs and never aggregated themselves.

⛔ **The failure this prevents is quiet and large: summing four quarterly balance
sheets triples assets** and the result still balances, because assets and
liabilities are both tripled. A reconciliation check would not catch it.

## ⭐⭐ INTERPOLATION SHIPS, AND §8a IS RECONCILED RATHER THAN OVERRIDDEN

§8a forbids `imputed` — *filling a MISSING observation within the supplied grain*.
That remains forbidden and `FORBIDDEN["imputed_status"]` still stands.

⭐ **Interpolation is a different act.** It re-grains a COMPLETE series to a finer
view, at the CXO's explicit request, with the method named. Nothing is missing:
ingest rejects gaps, so a supplied series has no holes to fill. The distinction is
**self-selection** — a CXO who chooses a method and reads "estimated by linear
interpolation" is not being handed a fabricated number unasked.

⛔ **AND THAT IS WHY THE STATUS TRAVELS WITH THE FIGURE RATHER THAN THE SESSION.**
The CXO chose it; a pack recipient did not. A session flag would be lost the moment
the number left the screen.
"""
from .modules.financials import ratio_registry as RR
from .modules.financials import periods as PR

# ⭐ Ruled: three. The tuple is ordered COARSEST-LAST so "finer than" is an index
# comparison rather than a lookup table that could disagree with itself.
VIEWS = ("monthly", "quarterly", "annual")
_PER_YEAR = {"monthly": 12, "quarterly": 4, "annual": 1}
_RANK = {v: i for i, v in enumerate(VIEWS)}

# ⭐ The status vocabulary this module emits. `interpolated` is NOT `imputed`; see
# the module docstring and CORE §8a's reconciliation.
INTERPOLATED = "interpolated"
LINEAR = "linear"

METHOD_LABEL = {
    LINEAR: "estimated by linear interpolation between reported quarters, "
            "not reported data",
}


def _vocab():
    v, _g, _r = RR._index()
    return v


def aggregation_of(token):
    """The declared rule for one token, or None if the token is unknown.

    ⛔ RETURNS None RATHER THAN A DEFAULT. A default here is the whole defect:
    an unclassified token would silently take `sum`, and a stock summed is the
    tripling this module exists to prevent.
    """
    return (_vocab().get(token) or {}).get("aggregation")


def enabled_views(frequency):
    """Which views a dataset at `frequency` enables, each with its reason."""
    base = frequency if frequency in _RANK else "annual"
    out = []
    for v in VIEWS:
        finer = _RANK[v] < _RANK[base]
        out.append({
            "view": v,
            "enabled": not finer,
            # ⭐ THE REASON IS ALWAYS PRESENT, enabled or not. A disabled control
            # with no explanation is indistinguishable from a broken one.
            "reason": (f"This dataset is {base}. A {v} view would need "
                       f"{v} data, or interpolation."
                       if finer else
                       ("the grain the data was supplied at" if v == base
                        else f"aggregated from {base}")),
            "is_base": v == base,
            "requires_interpolation": finer,
        })
    return out


# ═══════════════════════════════════════════════════════════════════════════
# BUCKETING — which sub-periods make one coarser period, and is it complete
# ═══════════════════════════════════════════════════════════════════════════

def _bucket_key(period, from_freq, to_freq):
    """The coarser period a sub-period belongs to, ENCODED AT THE TARGET GRAIN.

    ⛔⭐⭐ THE ENCODING IS THE WHOLE POINT AND A FIRST VERSION GOT IT WRONG. It
    built a monthly→quarterly key as `year*100 + quarter`, producing `202401` for
    2024 Q1 — six digits, which IS the monthly encoding. `derive_frequency` reads
    frequency from DIGIT COUNT, so the aggregated series would have declared
    itself monthly, every label would have read "Jan 2024" for a quarter, and the
    divisor `periods_per_year` would have returned 12 for annual data.
    ⭐ Quarterly is YYYYQ (5 digits); monthly is YYYYMM (6). A key must be valid
    in the frequency it claims — asserted by `bucket`.
    """
    year, sub = PR.decode_period(period, from_freq)
    if to_freq == "annual":
        return year
    if to_freq == "quarterly":
        if from_freq == "monthly":
            return year * 10 + ((sub - 1) // 3 + 1)
        return period
    return period


def bucket(periods, from_freq, to_freq):
    """Group sub-periods into target periods, marking each complete or partial.

    ⭐⭐ PARTIAL IS A PROPERTY OF THE BUCKET, COMPUTED FROM THE EXPECTED COUNT.
    Eight months of data leaves the third quarter holding two of three months.
    ⛔ It is rendered AS PARTIAL WITH ITS CAVEAT, never silently: a bucket
    labelled "Q3" built from two months WILL be compared against a real Q3, in
    this product and in the client's own reporting.
    """
    if _RANK[to_freq] < _RANK[from_freq]:
        raise ValueError("a coarser view cannot be built from finer data "
                         "by aggregation")
    expect = _PER_YEAR[from_freq] // _PER_YEAR[to_freq]
    order, members = [], {}
    for p in sorted(periods):
        k = _bucket_key(p, from_freq, to_freq)
        if k not in members:
            members[k] = []
            order.append(k)
        members[k].append(p)
    out = [{"period": k, "members": members[k],
            "expected": expect, "have": len(members[k]),
            "complete": len(members[k]) == expect,
            "partial": len(members[k]) != expect}
           for k in order]
    # ⭐⭐ EVERY PRODUCED KEY MUST BE VALID AT THE TARGET GRAIN, and this caught a
    # real defect (see `_bucket_key`). A key in the wrong encoding is not a
    # cosmetic problem: frequency is DERIVED FROM DIGIT COUNT, so the aggregated
    # series would misreport its own frequency to every consumer downstream.
    bad = [b["period"] for b in out
           if not PR.period_is_valid(b["period"], to_freq)]
    if bad:
        raise ValueError(f"bucket produced {bad[:3]} which are not valid "
                         f"{to_freq} periods — the target encoding is wrong")
    if PR.derive_frequency([b["period"] for b in out]) not in (to_freq, None):
        raise ValueError(f"the aggregated periods read as "
                         f"{PR.derive_frequency([b['period'] for b in out])!r}, "
                         f"not {to_freq!r}")
    return out


# ═══════════════════════════════════════════════════════════════════════════
# AGGREGATION
# ═══════════════════════════════════════════════════════════════════════════

def aggregate_series(series, buckets, rule):
    """One token's series, re-grained. `series` maps str(period) -> value.

    ⭐ ABSENCE PROPAGATES. If any member of a bucket is missing, the aggregate is
    None — the same discipline `_n` already applies everywhere else. A sum that
    skipped a missing month would report a smaller year as a real one.
    """
    out = {}
    for b in buckets:
        vals = [series.get(str(p)) for p in b["members"]]
        if any(v is None for v in vals) or not vals:
            out[str(b["period"])] = None
            continue
        if rule == "sum":
            out[str(b["period"])] = sum(vals)
        elif rule == "closing":
            # ⭐⭐ THE LAST MEMBER, AND `members` IS SORTED. A stock's coarser
            # value is its closing position — not a sum, not a mean. On a partial
            # bucket this is the latest position the client actually reported,
            # which is a true statement about a date even when the bucket is
            # incomplete.
            out[str(b["period"])] = vals[-1]
        elif rule == "constant":
            # ⛔ A RATE DOES NOT AGGREGATE. Carried through unchanged, and only
            # when every member agrees — a policy that changed mid-year is a
            # finding, not something to average away.
            out[str(b["period"])] = vals[0] if len(set(vals)) == 1 else None
        elif rule == "period_defined":
            out[str(b["period"])] = sum(vals)
        else:
            # `derived` never reaches here — the caller recomputes it.
            raise ValueError(f"aggregate_series called with rule {rule!r}")
    return out


# ⭐ The statement blocks and the token prefix each is keyed by, so a block's
# lines can be looked up in the registry without a second naming convention.
_BLOCK_PREFIX = {"income_statement": "is.", "balance_sheet": "bs.",
                 "cash_flow": "cf."}


def aggregate_statements(data, to_freq, *, field_map=None):
    """Re-grain the stored statements. Returns blocks, buckets and coverage.

    ⭐ `field_map` maps a stored field name to its registry token. Built from the
    registry's own `field` entries, so a line the registry does not classify is
    REPORTED rather than aggregated by a guess.
    """
    from_freq = PR.frequency_of(data)
    per = (data.get("periods") or {})
    hist = list(per.get("historical") or [])
    fcst = list(per.get("forecast") or [])
    allp = hist + fcst
    if not allp:
        return {"error": "no periods"}
    if _RANK[to_freq] < _RANK[from_freq]:
        raise ValueError("finer than the data")

    fmap = field_map or _field_map()
    bk = bucket(allp, from_freq, to_freq)
    n_hist = len(bucket(hist, from_freq, to_freq)) if hist else 0

    blocks, unclassified = {}, []
    for block, prefix in _BLOCK_PREFIX.items():
        src = data.get(block) or {}
        outb = {}
        for field, series in src.items():
            tok = fmap.get(prefix + field) or fmap.get(field)
            rule = aggregation_of(tok) if tok else None
            if rule is None:
                # ⛔ REPORTED, NOT DEFAULTED. See `aggregation_of`.
                unclassified.append(f"{block}.{field}")
                continue
            if rule == "derived":
                # ⭐ Recomputed by the caller from aggregated inputs; a derived
                # line aggregated directly is a second definition of it.
                continue
            outb[field] = aggregate_series(series, bk, rule)
        blocks[block] = outb
    return {"from": from_freq, "to": to_freq, "buckets": bk,
            "n_historical_buckets": n_hist,
            "blocks": blocks, "unclassified": sorted(unclassified),
            "partial": [b["period"] for b in bk if b["partial"]]}


def _field_map():
    """stored field name -> registry token, from the registry's own `field`."""
    out = {}
    for tok, meta in _vocab().items():
        f = (meta or {}).get("field")
        if f:
            out[tok.split(".", 1)[0] + "." + f.split(".")[-1]] = tok
            out[f.split(".")[-1]] = tok
    # ⭐ Derived tokens carry no `field`, and several stored lines are named for
    # the token rather than the field. Both directions are registered so a lookup
    # cannot depend on which one a block happens to use.
    for tok in _vocab():
        out.setdefault(tok, tok)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ INTERPOLATION — OFF BY DEFAULT, SELF-SELECTED, MARKED EVERYWHERE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ LINEAR IS THREE RULES, NOT ONE (CORE §8n), and it needs ruling 3's
# classification exactly as aggregation does:
#
#   flow    divide the parent period evenly across its children
#   stock   HOLD THE LEVEL — a closing balance is a position at a date, and
#           smearing it across three months invents three positions
#   ratio   NEVER interpolate the ratio; recompute it from interpolated
#           components, or the result is a ratio of nothing
#
# ⛔ NON-LINEAR IS REFUSED, and the refusal ships as a value with its reason.

REFUSED_METHODS = {
    "seasonal": {
        "refused": True, "ruling": "R2 / CORE §8n",
        "reason": (
            "A non-linear shape asserts WHEN within the period activity "
            "occurred. Fitting one needs at least two years of sub-annual "
            "history, and AXIOM has no seasonality model. A shape chosen "
            "without that evidence is a response function nobody supplied — "
            "the same refusal R2 applies to price optimisation. A client who "
            "DECLARES a seasonal profile is supplying an input rather than "
            "having one invented; that is a different feature."),
    },
}


def interpolate_series(series, from_periods, to_freq, from_freq, rule,
                       method=LINEAR):
    """One token's series, re-grained FINER. Every produced value is estimated.

    ⭐ Returns `{period: {"value": v, "status": "interpolated"|None,
    "method": ...}}` — the status travels WITH THE FIGURE, not beside the series
    and not in the session. A reported period keeps `status=None`; only the
    values AXIOM produced carry the mark.
    """
    if method != LINEAR:
        raise ValueError(f"method {method!r} is refused — see REFUSED_METHODS")
    if _RANK[to_freq] >= _RANK[from_freq]:
        raise ValueError("interpolation makes a series FINER")
    n = _PER_YEAR[to_freq] // _PER_YEAR[from_freq]
    out = {}
    for p in sorted(from_periods):
        v = series.get(str(p))
        children = _children(p, from_freq, to_freq, n)
        for i, c in enumerate(children):
            if v is None:
                out[str(c)] = {"value": None, "status": None, "method": None}
            elif rule == "sum":
                # ⭐ A flow divides evenly — a declared uniform-activity
                # assumption, stated rather than assumed.
                out[str(c)] = {"value": v / n, "status": INTERPOLATED,
                               "method": method}
            elif rule == "closing":
                # ⭐⭐ A STOCK HOLDS ITS LEVEL. The closing position is true at
                # the LAST child; the earlier children carry it forward because
                # AXIOM has no basis for a path between two balance dates.
                # ⛔ Dividing it would be the tripling defect in reverse.
                out[str(c)] = {"value": v, "status": INTERPOLATED,
                               "method": method}
            elif rule == "constant":
                # ⭐ A rate is unchanged at any grain and is NOT estimated — it
                # is the same declared policy. No status.
                out[str(c)] = {"value": v, "status": None, "method": None}
            else:
                raise ValueError(f"interpolate_series called with rule {rule!r}")
            # ⭐ The LAST child of a stock is the reported closing position
            # itself, so it is not an estimate and must not be marked as one.
            if rule == "closing" and i == n - 1 and v is not None:
                out[str(c)] = {"value": v, "status": None, "method": None}
    return out


def interpolate_statements(data, to_freq, method=LINEAR):
    """Re-grain the stored statements FINER. Every produced figure is marked.

    ⭐ Same classification as aggregation, applied in the opposite direction —
    which is why ruling 3 was a prerequisite for both. A derived line is not
    interpolated; it is recomputed from interpolated components by the consumer,
    exactly as it is recomputed from aggregated ones.
    """
    from_freq = PR.frequency_of(data)
    per = (data.get("periods") or {})
    allp = list(per.get("historical") or []) + list(per.get("forecast") or [])
    if _RANK[to_freq] >= _RANK[from_freq]:
        raise ValueError("interpolation makes a series FINER")
    fmap = _field_map()
    blocks, unclassified = {}, []
    for block, prefix in _BLOCK_PREFIX.items():
        src = data.get(block) or {}
        outb = {}
        for field, series in src.items():
            tok = fmap.get(prefix + field) or fmap.get(field)
            rule = aggregation_of(tok) if tok else None
            if rule is None:
                unclassified.append(f"{block}.{field}")
                continue
            if rule in ("derived", "period_defined"):
                continue
            outb[field] = interpolate_series(series, allp, to_freq, from_freq,
                                             rule, method)
        blocks[block] = outb
    n_marked = sum(1 for b in blocks.values() for s in b.values()
                   for v in s.values() if v["status"] == INTERPOLATED)
    return {"from": from_freq, "to": to_freq, "blocks": blocks,
            "unclassified": sorted(unclassified),
            "method": method, "method_label": METHOD_LABEL[method],
            # ⭐ THE COUNT IS PART OF THE ANSWER. "Some figures are estimated" is
            # not a disclosure; "412 of 480 figures on this view are estimated"
            # is. §III.4's denominator rule, applied to a marking.
            "n_interpolated": n_marked,
            "status": INTERPOLATED}


def _children(period, from_freq, to_freq, n):
    year, sub = PR.decode_period(period, from_freq)
    if from_freq == "annual" and to_freq == "quarterly":
        return [year * 100 + q for q in range(1, 5)]
    if from_freq == "annual" and to_freq == "monthly":
        return [year * 100 + m for m in range(1, 13)]
    if from_freq == "quarterly" and to_freq == "monthly":
        return [year * 100 + (sub - 1) * 3 + m for m in range(1, 4)]
    raise ValueError(f"no child mapping for {from_freq} -> {to_freq}")
