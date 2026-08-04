"""Every gate that can run in CI is wired into CI, and the ones that cannot say so.

⭐⭐ WHY THIS EXISTS. Measured at `eb89ee8`: 17 of 29 gates were wired into
`ci.yml` and TWELVE WERE NOT — including `check-no-internal-identifiers.py`,
written in the session that counted them and never added. Every lane that
reported "29/29 gates green" was reporting a number true on one laptop.

⭐ THE COUNT IS DERIVED FROM THE FILESYSTEM AND THE WORKFLOW, NEVER FROM A LIST.
A hand-maintained roster of "gates that should be in CI" is the §III.4 defect:
the roster and the workflow drift together and both look consistent. So the
gates come from `scripts/check-*.py` and the wiring from `ci.yml`'s own text.

⛔ AND A GATE THAT CANNOT REACH ITS INPUT MUST NOT EXIT NON-ZERO. That is a
failure on a condition it does not guard — the defect fixed at `94a7ce0`
(period labels) and `eb89ee8` (assumption bounds). This asserts the same shape
for `check-in-development-marking.py`, which returned 2 with no frontend
checkout.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CI = os.path.join(ROOT, ".github", "workflows", "ci.yml")
SCRIPTS = os.path.join(ROOT, "scripts")


def _gates():
    return sorted(n[:-3] for n in os.listdir(SCRIPTS)
                  if n.startswith("check-") and n.endswith(".py"))


def _ci_text():
    return open(CI, encoding="utf-8").read()


# ── 1 · every gate is wired ────────────────────────────────────────────────

def test_every_gate_script_is_invoked_by_ci():
    """⭐ THE COVERAGE FLOOR, §III.4. Both halves derived: gates from the
    directory, invocations from the workflow text."""
    text = _ci_text()
    missing = [g for g in _gates() if f"scripts/{g}.py" not in text]
    assert missing == [], (
        f"{len(missing)} gate(s) exist but CI never runs them: {missing}. "
        "A gate outside CI is enforced on one laptop.")


def test_the_gate_corpus_is_not_empty():
    """A gate list that silently became empty would make the assertion above
    vacuously true — the shape check-none-arithmetic.py exists to catch."""
    assert len(_gates()) >= 29, f"only {len(_gates())} gates found"


# ── 2 · the exit-code shape, for the gate this lane fixed ──────────────────

def _run(script, env_extra):
    """⭐ A DELIBERATELY EMPTY ENVIRONMENT — the CI shape, not this laptop's.

    ⛔ AND IT DOES NOT READ `PATH`. `sys.executable` is absolute, so no search
    path is needed — and reading one here would register this file as a consumer
    of an undocumented variable and turn `check-env-manifest.py` red. It did,
    once, while this test was being written.
    """
    env = {"HOME": "/nonexistent-home"}
    env.update(env_extra)
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script)],
                          capture_output=True, text=True, env=env, cwd=ROOT)


def test_in_development_marking_does_not_fail_when_the_frontend_is_absent():
    """⭐⭐ THE RULED SHAPE, third application. It returned 2 with no frontend
    checkout — failing on a condition it does not guard. This gate guards
    whether a marking and a capability agree, NOT whether a sibling repository
    happens to be checked out beside it."""
    r = _run("check-in-development-marking.py",
             {"AXIOM_FRONTEND": "/nonexistent-frontend-checkout"})
    assert r.returncode == 0, (
        f"exited {r.returncode} with no frontend checkout; a missing sibling "
        f"repo is not a violation of this gate\n{r.stdout}\n{r.stderr}")


def test_it_states_the_half_it_could_not_check_rather_than_passing_quietly():
    """⛔ NOT WEAKENED TO A SKIP. Exiting 0 silently would be the other defect:
    green over zero files. It must name the unchecked half in its own output."""
    r = _run("check-in-development-marking.py",
             {"AXIOM_FRONTEND": "/nonexistent-frontend-checkout"})
    out = r.stdout
    assert "NOT RUN" in out or "not verified" in out.lower(), \
        f"a reader cannot tell the marking half did not run:\n{out}"
    assert "asserts nothing" in out.lower() or "not a green" in out.lower(), \
        f"it does not disclaim the half it skipped:\n{out}"


def test_it_still_enforces_the_half_it_can_reach():
    """⭐ THE OTHER HALF IS THIS REPOSITORY'S, and it runs regardless. The
    capability's existence is checked here, so the output must report it."""
    r = _run("check-in-development-marking.py",
             {"AXIOM_FRONTEND": "/nonexistent-frontend-checkout"})
    assert "capability built" in r.stdout.lower(), \
        f"the backend half did not run:\n{r.stdout}"


def test_a_failed_control_still_fails():
    """⛔ THE FIX MUST NOT SWALLOW A REAL FAILURE. A broken control returns 2
    and must keep doing so — that is a condition the gate DOES guard."""
    src = open(os.path.join(SCRIPTS, "check-in-development-marking.py"),
               encoding="utf-8").read()
    assert "return 2" in src, "the control-failure exit was removed with the fix"
