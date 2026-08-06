"""§4u-c's boundary depends on one line nobody was watching.

⭐⭐ `AssignIn` sets `model_config = {"extra": "forbid"}` EXPLICITLY, and Pydantic
v2's default is `extra="ignore"`. So deleting that line does not raise, does not
warn, and does not fail any existing test — it silently converts "a client posting
comment text is REFUSED before the server sees it" into "a client posting comment
text is silently DROPPED and believes it travelled".

⛔ THE VoE SCOPE LANE FOUND THIS BY EXERCISING THE MODEL RATHER THAN READING IT.
A reader who assumed the Pydantic default would have been right about today's
behaviour and wrong about why — and would not have noticed when it changed.

⭐ Enforcement 2 (`assign()` raises) would still catch a comment that reached the
writer, so this is defence in depth, not the only line. That is exactly why it can
rot unnoticed: nothing user-visible breaks when it goes.
"""
import pytest

from services.api import voice_of_employee as V


def _assign_in_body():
    """AssignIn's FIELD DECLARATIONS only — comments stripped, class scoped.

    ⛔ §III.9, AGAIN, AND IN THIS FILE'S FIRST RUN. A fixed 900-character window
    from `class AssignIn` ran past the class into prose that says "a client that
    tries to post comment text is refused" — and the test reported a field able
    to hold words, about a comment explaining that no such field exists.
    ⭐ The body ends at the next line indented no further than the class, and
    `#` comments are removed before anything is matched.
    """
    import inspect
    import re
    src = inspect.getsource(V)
    assert "class AssignIn" in src, "the request model has been renamed or removed"
    i = src.index("class AssignIn")
    indent = len(src[:i].split("\n")[-1])
    out = []
    for line in src[i:].split("\n")[1:]:
        if line.strip() and (len(line) - len(line.lstrip())) <= indent:
            break
        out.append(re.sub(r"#.*$", "", line))
    return "\n".join(out)


def test_the_request_model_forbids_unknown_fields_explicitly():
    """⛔ NOT 'it happens to reject' — the config must be PRESENT. Pydantic v2
    defaults to `ignore`, so an absent config silently accepts and drops."""
    body = _assign_in_body()
    assert '"extra": "forbid"' in body or "'extra': 'forbid'" in body, (
        "AssignIn no longer sets extra=forbid. Pydantic v2 DEFAULTS TO `ignore`, "
        "so removing this line does not raise and does not fail any other test — "
        "it converts a refusal into a silent drop, and a client posting comment "
        "text would believe it travelled. §4u-c enforcement 3.")


def test_the_model_carries_no_field_that_could_hold_words():
    body = _assign_in_body()
    for banned in ("comment", "verbatim", "quote", "participant_ref", "text:"):
        assert banned not in body, (
            f"AssignIn declares a field able to hold words: {banned!r}")


def test_the_writer_still_raises_rather_than_stripping():
    """⭐ Enforcement 2, exercised — the pair this file is defence in depth for."""
    with pytest.raises(Exception) as ei:
        V.assign(None, 1, 1, "cat", comment="should be refused")
    msg = str(ei.value).lower()
    assert "does not travel" in msg or "refused" in msg, msg
    import inspect
    body = inspect.getsource(V.assign)
    assert ".pop(" not in body and "del " not in body, (
        "assign() appears to STRIP rather than raise — silently dropping the "
        "text lets a caller believe it travelled (§4u-c enforcement 2)")
