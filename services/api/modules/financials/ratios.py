"""The ratio library — sole owner of the arithmetic AND the definition.

⭐ NET DEBT WAS COMPUTED IN FOUR PLACES AND THEY AGREED ON EVERY STORED DATASET.
That agreement is why it survived: `short_term_debt + long_term_debt − cash`,
written out by hand at financials:328, intelligence:1569, valuation:135 and
valuation:542, producing identical numbers across all 14 datasets. A definitional
split needs only one of the four to be edited once.

⭐ AND THEY WERE NOT ACTUALLY EQUIVALENT. Measured before consolidating, with
long_term_debt absent in the last historical period:

    financials:328     -> None          (absence-propagating, via _n)
    valuation:135      -> TypeError
    valuation:542      -> TypeError
    intelligence:1569  -> TypeError

Three of four raised where the fourth returned absence. No stored dataset has a
missing balance-sheet line, so nothing exercised the one path on which they
differed, and the "they all agree" reading was true only of populated data.

⭐⭐ THE LIBRARY OWNS THE ARITHMETIC AND THE DEFINITION — NOT THE OPERAND SOURCE.
`net_debt(debt, cash)` takes debt as an ARGUMENT and must never recompute it from
the balance sheet. Four callers inject `_debt_book` and they do not all supply the
same thing:

    valuation:126             short_term_debt + long_term_debt
    financials:609            _n(short_term_debt, long_term_debt)
    intelligence:599          debt0, the same book debt
    prescience_decision:241   (short_term_debt + long_term_debt)
                                  * wacc_mods["debt_scale"]      <- SHOCKED

Prescience deliberately scales debt to evaluate scenarios. A library that fetched
`bs["short_term_debt"][ys] + bs["long_term_debt"][ys]` itself would silently
un-shock every Prescience scenario — still rendering, still typechecking, wrong
only where nobody looks. "Where does the debt come from" is the caller's question;
"what is net debt, and what happens when an operand is missing" is this module's.
"""
from typing import Optional

Number = Optional[float]


def net_debt(debt: Number, cash: Number) -> Number:
    """Total debt less cash. Absence propagates.

    `debt` is supplied by the caller — see the module docstring. Passing a
    balance sheet here instead of a number would be the defect this signature
    exists to prevent.
    """
    # Imported inside the function: engines imports this module, so a
    # module-level import would close the cycle. One absence primitive, not two —
    # duplicating `_n` here to avoid the cycle would put the absence contract in
    # two places, which is the shape this whole library exists to remove.
    from .engines import _n
    return _n(lambda d, c: d - c, debt, cash)
