"""T1 — the dimensional model's ORM tables.

⭐⭐ THIS MODULE MUST BE IMPORTED BEFORE `include_accounts` RUNS `create_all`.
A model imported afterwards is a table that is never made, and the failure
surfaces far away as a missing relation at query time — the §4u-c defect, twice
repeated since. See the import block in `main.py`.

⭐ MIGRATION 0027 CREATES THE SAME THREE TABLES for environments that run
Alembic. Both mechanisms exist in this repo and both are needed: the Procfile
starts gunicorn directly with no migration step, so `create_all` is the live
path, while 0027 keeps a managed database in step. `ax_initiative_impact_
declarations` carries the same pair.

The vocabulary, the composition rules and the reconciler live in
`modules/financials/dimensions.py`; this file is only the storage.
"""
from datetime import datetime

from sqlalchemy.sql import false as sa_false

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, String,
                        UniqueConstraint, func)

from .accounts import Base


class DimensionMember(Base):
    """One segment, product, customer, channel or geography line.

    ⭐ SHAPED ON `ax_departments`, which is already AXIOM's dimension-member
    table: a stable key that survives a rename, a mutable display name, a
    self-referencing parent, and a flag for the rows the system owns.
    """
    __tablename__ = "ax_dimension_member"
    __table_args__ = (UniqueConstraint("company_id", "dimension_type", "code",
                                       name="uq_dimension_member"),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    # ⭐ A COLUMN, NOT A TABLE PER TYPE. Segment and product rows are never
    # adjacent in a way that invites a sum.
    dimension_type = Column(String(24), index=True, nullable=False)
    # ⭐⭐ THE ax_departments LESSON: an opaque token minted at creation,
    # deliberately NOT derived from the display name. A hash of the name made a
    # rename look like a new member, which is how a re-upload once duplicated an
    # entire org tree.
    member_key = Column(String(64), index=True, nullable=False)
    code = Column(String(64), nullable=False)
    name = Column(String(200), nullable=False)
    # ⭐ Nests WITHIN one dimension_type only. Never across types: segment x
    # product is a MATRIX, and a self-referencing parent is exactly the
    # structure that would invite someone to walk it as a tree.
    parent_id = Column(Integer, index=True, nullable=True)
    active_from = Column(Integer, nullable=True)
    active_to = Column(Integer, nullable=True)
    # ⭐⭐ THE RESIDUAL IS A MEMBER, NOT A COMPUTED GAP. One system-owned row per
    # (company, dimension_type) carries the unreconciled remainder, so every
    # chart that sums the dimension sums to the company total BY CONSTRUCTION.
    is_unallocated = Column(Boolean, nullable=False, default=False,
                            server_default=sa_false())
    source = Column(String(40), nullable=False, default="upload")
    # ⭐ server_default AS WELL AS the Python default. Migration 0027
    # declares one and the ORM did not, so a raw-SQL writer against a
    # create_all-made table hit a NOT NULL violation that the same INSERT
    # would have survived against a migration-made one. Two mechanisms for
    # one table must not disagree about its defaults.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        server_default=func.now())


class DimensionMap(Base):
    """A member's membership of another dimension type.

    ⭐⭐ THIS TABLE'S EXISTENCE IS THE LICENCE TO COMBINE TWO DIMENSIONS. Absent
    for a pair, segment and product are PARALLEL decompositions of the same
    revenue and `dimensions.reconcile_across` REFUSES. That makes the source
    document's anti-double-counting rule STRUCTURAL rather than a validation
    someone forgets to run — `Company = Segments + Products` is the single most
    consequential arithmetic error available in this module, and the licence to
    avoid it is a table row rather than a reviewer's memory.
    """
    __tablename__ = "ax_dimension_map"
    __table_args__ = (UniqueConstraint("company_id", "member_id",
                                       "parent_member_id", name="uq_dimension_map"),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    member_id = Column(Integer, index=True, nullable=False)
    parent_member_id = Column(Integer, index=True, nullable=False)
    valid_from = Column(Integer, nullable=True)
    valid_to = Column(Integer, nullable=True)
    # ⭐ Populated ONLY where the client explicitly supplies fractional mapping.
    # Weights above 1.0 are a resolution workflow, never a silent normalise.
    weight = Column(Float, nullable=True)
    source = Column(String(40), nullable=False, default="upload")
    # ⭐ server_default AS WELL AS the Python default. Migration 0027
    # declares one and the ORM did not, so a raw-SQL writer against a
    # create_all-made table hit a NOT NULL violation that the same INSERT
    # would have survived against a migration-made one. Two mechanisms for
    # one table must not disagree about its defaults.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        server_default=func.now())


class DimensionObservation(Base):
    """One measured value, for one member, in one period, on one dataset version.

    ⭐⭐ ONE FACT TABLE WITH A `measure` COLUMN, where the source document
    proposes four (RevenueObservation, CostObservation, ProductVolumeObservation,
    PricingObservation). Every measure reconciles the same way, carries the same
    data_status and versions the same way; four tables of one shape would need
    four reconcilers and would drift apart on the first change.

    ⭐ NOTHING IS EVER WRITTEN FOR A MEMBER THE CLIENT DID NOT SUPPLY. There is
    no zero-filling and no dense grid — absence is absence, and the existing
    `financials.engines._n` propagation carries it forward untouched.
    """
    __tablename__ = "ax_dimension_observation"
    __table_args__ = (UniqueConstraint("dataset_id", "member_id", "period",
                                       "measure", "basis",
                                       name="uq_dimension_observation"),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    # ⭐ Ties every observation to a dataset VERSION, so a re-upload creates a
    # new version and nothing is mutated. The non-destructive guarantee is
    # INHERITED here rather than restated.
    dataset_id = Column(Integer, index=True, nullable=False)
    member_id = Column(Integer, index=True, nullable=False)
    # ⭐⭐ THE SAME PERIOD INTEGER + FREQUENCY THE STATEMENTS USE, parsed through
    # `modules.financials.periods` via `dimensions.period_of` and never through
    # its own date handling. A second period representation is how a quarterly
    # client's dimension rows stop lining up with their own statements.
    period = Column(Integer, index=True, nullable=False)
    frequency = Column(String(16), nullable=False)
    measure = Column(String(32), index=True, nullable=False)
    value = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True)
    unit_of_measure = Column(String(24), nullable=True)
    # ⭐ THE DATA-STATUS TAXONOMY. `imputed` is DELIBERATELY NOT a permitted
    # value — see `dimensions.DATA_STATUSES` and CORE §8a.
    data_status = Column(String(24), nullable=False, default="observed")
    basis = Column(String(20), nullable=False, default="actual")
    source_sheet = Column(String(64), nullable=True)
    source_row = Column(Integer, nullable=True)
    # ⭐ Without it, a recomputation that differs cannot be distinguished from a
    # data change — the difference between "the model improved" and "the
    # client's numbers moved".
    calculation_version = Column(String(32), nullable=True)
    # ⭐ server_default AS WELL AS the Python default. Migration 0027
    # declares one and the ORM did not, so a raw-SQL writer against a
    # create_all-made table hit a NOT NULL violation that the same INSERT
    # would have survived against a migration-made one. Two mechanisms for
    # one table must not disagree about its defaults.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                        server_default=func.now())
