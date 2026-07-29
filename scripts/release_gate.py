"""Refuse to run a verification against a build you cannot name.

⭐ THIS EXISTS BECAUSE A CRAWL BLAMED A COMMIT THAT NO LONGER EXISTED. On
2026-07-29 a three-mode crawl recorded `plan-vs-methods` 500s on two datasets and
they were written up as a live defect. The endpoint had already been fixed; the
crawl started before Railway finished publishing the fix, and 20/20 calls were
clean minutes later. The finding was real, reproducible, and about the wrong
build.

**Pushed is not published.** A verification tool that cannot name the artifact it
tested produces findings nobody can attribute, and the cost is not one wasted
report — it is that the next genuine red gets waved away as "probably the deploy
again". A red we read past is a decaying instrument.

Sentry already tags this same SHA as `release`, so an event and a crawl now name
one build.

⭐ THIS REFUSES ON ABSENCE, NOT ONLY ON MISMATCH. If /health omits `release` or
reports null, the deployed build has no identity and the assertion is
unfalsifiable — so it exits rather than passing. "I could not check" and "I
checked and it matched" must never print the same tick, which is the same
green-over-nothing failure this codebase keeps paying for.

NOTE: optimization-anchor/scripts/release_gate.py is a sibling copy for shoot.py,
which lives in the frontend repo. Two files, deliberately — they are separate
deployables and neither can import the other. If you change the protocol here,
change it there.
"""
import json
import os
import subprocess
import sys
import urllib.request


def deployed_release(api_base, timeout=20):
    """The SHA the deployed API reports, or None if it has no identity."""
    with urllib.request.urlopen(api_base.rstrip("/") + "/health", timeout=timeout) as r:
        return (json.load(r) or {}).get("release")


def local_head(repo_dir=None):
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def refuse(lines):
    print("\n" + "=" * 66)
    print("  REFUSING TO RUN — release assertion failed")
    print("=" * 66)
    for l in lines:
        print("  " + l)
    print("=" * 66 + "\n")
    sys.exit(2)


def assert_release(api_base, expect=None, label="verification"):
    """Refuse unless the deployed API names a build, and it is the expected one.

    `expect` None means "no expectation to compare against" — the release is
    still REQUIRED and reported, because an unattributable run is the failure
    mode this guards. Set AXIOM_EXPECT_RELEASE to pin it.
    """
    expect = expect or os.environ.get("AXIOM_EXPECT_RELEASE") or None
    try:
        got = deployed_release(api_base)
    except Exception as e:
        refuse([f"{api_base}/health did not answer: {str(e)[:90]}",
                "The backend must be reachable and must name its build."])

    if not got:
        refuse([f"{api_base}/health returned no `release`.",
                "The deployed build has no identity, so 'does it match?' cannot",
                "be answered. This is not a pass — it is an unfalsifiable check.",
                "",
                "Fix: set RAILWAY_GIT_COMMIT_SHA in the API service environment."])

    if expect and got[:7] != expect[:7]:
        refuse([f"deployed release : {got[:12]}",
                f"commit under test: {expect[:12]}",
                "",
                "PUSHED IS NOT PUBLISHED. Every red from this run would belong to",
                "a build you are not testing. Wait for the deploy to land, or set",
                "AXIOM_EXPECT_RELEASE to the SHA you actually mean to test."])

    if expect:
        print(f"  ✓ release gate: deployed {got[:12]} == under test {expect[:12]}")
    else:
        print(f"  · release gate: deployed {got[:12]} (no expectation pinned; "
              f"set AXIOM_EXPECT_RELEASE to assert)")
    return got
