"""§4v — the departmental strategy map: a constrained hierarchy, auto-laid-out.

⭐⭐ POSITION IS NOT DATA, SO THIS MODULE PUBLISHES NO POSITION. On a free canvas
where a CXO drags nodes, position acquires meaning the model does not carry — two
nodes side by side read as related whether or not anyone said so. What the map
asserts spatially is exactly one thing: WHICH LAYER a node is in, and its ORDER
within that layer. The renderer turns a layer and an index into coordinates.

⭐⭐ THE LAYOUT ALGORITHM IS A LAYERED (SUGIYAMA-STYLE) ASSIGNMENT WITHOUT THE
CROSSING-MINIMISATION PASS, and the omission is deliberate. Barycentre ordering
reduces edge crossings by REORDERING NODES — which means declaring one new edge
can move a node the reader was looking at, on a map they return to weekly. Order
here is a pure function of STABLE KEYS (obj_key, kr_key, initiative id), so:
  · adding, revoking or re-declaring an edge NEVER moves a node;
  · a re-upload keeps every node where it was, because the keys survive it;
  · two readers of the same department see the same picture.
The cost is paid in crossings, and crossings are the right thing to pay with.

⭐⭐ UNCONNECTED NODES ARE THE FINDING, NOT AN OMISSION. 8 of 49 KPIs measure no
objective and 41 of 82 key results have nobody resourcing them. A map that drew
only the connected part would report a tidier company than exists — the reader
would see a complete strategy and never learn that half of it is unfunded.

⛔ EDGES ARE DECLARED, NEVER INFERRED. `KeyResult.kpi_key` was designed to match
KRs to KPIs by text and is NULL on all 82 rows — inference-by-name has produced
nothing here, and had it produced something it would have been a guess wearing a
declaration's clothes. Every edge carries an actor and a date, and removal is a
REVOKE (§4v.1 ruling 1), so a revoked edge stops connecting while the fact that
someone considered and rejected it survives.

⛔ NO NEW COMPUTATION. Nothing here derives a figure; it arranges rows the
product already publishes and reports which of them nobody connected.
"""

# ⭐ THE HIERARCHY IS CONSTRAINED, AND THIS TUPLE IS THE CONSTRAINT. Objective →
# key result → KPI → initiative: intent, then how intent is measured as a target,
# then the standing measure, then the work. An edge that skips a layer is still
# drawable — a KPI may serve an objective directly — but no node may sit outside
# these four.
LAYERS = ("objective", "key_result", "kpi", "initiative")

# ⭐ §4v — the destinations shipped at cc49b2a. No node is a dead end: every one
# opens the page that owns it, keyed the way that page addresses it.
_DEST = {
    "objective": lambda k: f"/objective/{k}",
    "key_result": lambda k: f"/key-result/{k}",
    "kpi": lambda k: f"/kpi/{k}",
    "initiative": lambda k: f"/initiative/{k}",
}


def _node(layer, key, label, *, sort_key, meta=None):
    """⛔ NO `x`, NO `y`. See the module docstring: a coordinate published here
    would be an assertion about the world, and the world did not make it."""
    return {
        "id": f"{_PREFIX[layer]}:{key}",
        "layer": layer,
        "layer_index": LAYERS.index(layer),
        "key": str(key),
        "label": label or "",
        "to": _DEST[layer](key),
        "sort_key": sort_key,
        "connected": False,
        **(meta or {}),
    }


_PREFIX = {"objective": "obj", "key_result": "kr", "kpi": "kpi",
           "initiative": "ini"}


def _order(nodes):
    """⭐⭐ ORDERING IS A PURE FUNCTION OF STABLE KEYS — never of input order, and
    never of the edge set. Sorting on the payload's arrival order would make the
    map reflow whenever an unrelated query plan changed; sorting on the edges
    would make it reflow on every declaration, which is the one moment the reader
    is looking at it."""
    return sorted(nodes, key=lambda n: (n["layer_index"], n["sort_key"], n["id"]))


def build_map(*, objectives, kpis, initiatives, edges):
    """-> {layers, nodes, edges, unconnected, dropped_edges, counts}.

    `objectives` is the okr-map's objective list, each carrying its `key_results`.
    `edges` are DECLARED links, each `{kind, src, dst, declared_by, declared_at,
    revoked_at}` with `src`/`dst` in the `obj:`/`kr:`/`kpi:`/`ini:` id space.
    """
    nodes = []
    for oi, o in enumerate(objectives or []):
        okey = o.get("obj_key") or o.get("key") or o.get("objective_id")
        if okey is None:
            continue
        nodes.append(_node("objective", okey,
                           o.get("objective") or o.get("title"),
                           sort_key=str(okey),
                           meta={"status": o.get("status"),
                                 "owner": o.get("owner")}))
        for kr in (o.get("key_results") or []):
            kkey = kr.get("kr_key") or kr.get("key")
            if kkey is None:
                continue
            # ⭐ A KEY RESULT SORTS UNDER ITS OBJECTIVE, by the PARENT'S stable
            # key rather than the parent's position — so children stay beneath
            # their parent without inheriting the parent's mutability.
            nodes.append(_node("key_result", kkey,
                               kr.get("name") or kr.get("text") or kr.get("kr"),
                               sort_key=f"{okey}\x00{kkey}",
                               meta={"objective_key": str(okey),
                                     "progress": kr.get("progress")}))
    for k in (kpis or []):
        kid = k.get("id") or k.get("kpi_id")
        if kid is None:
            continue
        nodes.append(_node("kpi", kid, k.get("name") or k.get("kpi"),
                           sort_key=f"{int(kid):012d}" if str(kid).isdigit()
                                    else str(kid),
                           meta={"unit": k.get("unit")}))
    for i in (initiatives or []):
        iid = i.get("id")
        if iid is None:
            continue
        nodes.append(_node("initiative", iid, i.get("title"),
                           sort_key=str(i.get("ref_code") or "")
                                    + f"\x00{int(iid):012d}",
                           meta={"ref_code": i.get("ref_code"),
                                 "status": i.get("status")}))

    nodes = _order(nodes)
    by_id = {n["id"]: n for n in nodes}

    drawn, dropped = [], 0
    for e in (edges or []):
        # ⭐ §4v.1 RULING 1 — a revoked link is still a row, and must stop being
        # a line. The column is inert unless every reader filters on it.
        if e.get("revoked_at"):
            continue
        # ⛔ AN EDGE WITH NO ACTOR AND NO DATE IS AN INFERENCE. It is refused
        # and COUNTED, because silently drawing it would put an unattributed
        # claim on a map whose whole premise is attribution.
        if e.get("declared_by") is None or not e.get("declared_at"):
            dropped += 1
            continue
        src, dst = e.get("src"), e.get("dst")
        if src not in by_id or dst not in by_id:
            # ⭐ A LINE TO NOWHERE IS DROPPED AND REPORTED — a link whose other
            # end is in another department, or whose row a re-upload retired.
            dropped += 1
            continue
        by_id[src]["connected"] = True
        by_id[dst]["connected"] = True
        drawn.append({"kind": e.get("kind"), "src": src, "dst": dst,
                      "src_layer": by_id[src]["layer"],
                      "dst_layer": by_id[dst]["layer"],
                      "declared_by": e.get("declared_by"),
                      "declared_by_label": e.get("declared_by_label"),
                      "declared_at": e.get("declared_at"),
                      "source": e.get("source")})

    # ⭐⭐ THE FINDING IS COUNTABLE, PER LAYER. "How much of this is unresourced"
    # must be answerable without counting dots on a picture — and per layer,
    # because an unmeasured objective and an unresourced key result are
    # different problems with different owners.
    unconnected = {ly: 0 for ly in LAYERS}
    counts = {ly: 0 for ly in LAYERS}
    for n in nodes:
        counts[n["layer"]] += 1
        if not n["connected"]:
            unconnected[n["layer"]] += 1

    for n in nodes:
        n.pop("sort_key", None)

    return {"layers": list(LAYERS), "nodes": nodes, "edges": drawn,
            "unconnected": unconnected, "counts": counts,
            "node_count": len(nodes), "edge_count": len(drawn),
            "dropped_edges": dropped}


def map_permission(*, has_authority, is_platform_staff):
    """Who may draw and revoke an edge — §4v.1 ruling 3's separate link permission.

    ⭐⭐ THE REASON IS PART OF THE ANSWER. Five of Meridian's seven departments
    have no authority holder, so for most readers this map is read-only — and a
    disabled control with no explanation reads as a broken feature, which is the
    one conclusion that would be wrong. The refusal names who could edit it and
    says nothing is wrong with the map.
    """
    if is_platform_staff:
        # ⛔ PLATFORM STAFF REFUSED, however the operator bypass reads elsewhere.
        # Drawing an edge asserts that one part of a customer's business serves
        # another; that is never ours to say.
        return {"may_edit": False,
                "why": "Platform staff may read this map but never draw on it — "
                       "an edge is a claim about how this company's own work "
                       "connects, and only the company may make it."}
    if not has_authority:
        return {"may_edit": False,
                "why": "This map is read-only because nobody holds authority for "
                       "this department yet. An administrator can grant it; the "
                       "holder then draws and revokes the connections."}
    return {"may_edit": True,
            "why": "You hold authority for this department, so you may draw a "
                   "connection or revoke one. Both are recorded with your name "
                   "and the date."}
