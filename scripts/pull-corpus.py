#!/usr/bin/env python3
"""Pull the dataset corpus into a durable local cache. READ-ONLY.

⭐ NEVER COMMITTED. The corpus is customer financial data. It lives OUTSIDE the
working tree — default `~/.axiom-cache/ds.json`, overridable with DS_CACHE — so
it cannot be added by an absent-minded `git add -A`. The repo also gitignores
`ds.json` as a second fence, because the convergence_study.py convention defaults
it to the repo root.

Extends the DS_CACHE convention already used by scripts/convergence_study.py
rather than inventing a second one.

Prints counts only. No company names, no figures — those belong in neither
stdout nor any committed report.

    railway run --service Postgres python3 scripts/pull-corpus.py
"""
import json
import os
import sys

DEFAULT = os.path.join(os.path.expanduser("~"), ".axiom-cache", "ds.json")


def cache_path() -> str:
    return os.environ.get("DS_CACHE") or DEFAULT


def load_corpus():
    """The corpus, or None when it is absent.

    ⭐ RETURNS None RATHER THAN {} SO A CALLER CANNOT SWEEP ZERO DATASETS AND
    REPORT AGREEMENT. An empty corpus and a missing corpus are both "nothing was
    compared", and a harness that prints '0 disagreements' over either is the
    silent-empty pattern applied to itself.
    """
    p = cache_path()
    if not os.path.exists(p):
        return None
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return None
    return d or None


def main():
    import psycopg
    url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("✗ no DATABASE_PUBLIC_URL / DATABASE_URL — run under `railway run`")
        return 2
    cn = psycopg.connect(url.replace("postgresql+psycopg://", "postgresql://"))
    cur = cn.cursor()
    cur.execute("select id, data from financial_datasets order by id")
    rows = cur.fetchall()
    out = {}
    for did, data in rows:
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                continue
        if isinstance(data, dict) and "income_statement" in data:
            out[str(did)] = data
    p = cache_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w", encoding="utf-8"))
    os.chmod(p, 0o600)
    print(f"  rows read              {len(rows)}")
    print(f"  datasets with a payload {len(out)}")
    print(f"  written to             {p}  (mode 600, outside the working tree)")
    cn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
