"""NSIDES RDBMS model definition."""

from sqlalchemy import Column, Float, Index, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, Mapped

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Nsides(Base):
    """Class definition for the nSIDES table."""

    __tablename__ = "nsides"
    __table_args__ = (
        Index(
            "idx_nsides_multi",
            "condition_meddra_id",
            "condition_concept_name",
            "prr",
            "mean_reporting_frequency",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)

    drug_rxnorn_id: Mapped[str] = mapped_column(String(20), index=True)  # This has to be a String because of mapping to drugbank ids
    drug_concept_name: Mapped[str] = mapped_column(String(255), index=True)

    source: Mapped[str] = mapped_column(String(10), index=True)

    condition_meddra_id: Mapped[int] = mapped_column()
    condition_concept_name: Mapped[str] = mapped_column(String(255), index=True)

    # OFFSIDES specific
    a = mapped_column(Integer)
    b = mapped_column(Integer)
    c = mapped_column(Integer)
    d = mapped_column(Integer)
    prr = mapped_column(Float)
    prr_error = mapped_column(Float)
    mean_reporting_frequency = mapped_column(Float, index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
