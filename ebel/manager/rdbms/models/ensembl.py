"""EnsEMBL RDBMS model definition."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Ensembl(Base):
    """Class definition for the ensembl table."""

    __tablename__ = "ensembl"
    id: Mapped[int] = mapped_column(primary_key=True)
    enst: Mapped[str] = mapped_column(String(20), index=True)
    version: Mapped[int] = mapped_column()
    chromosome: Mapped[str] = mapped_column(String(10), index=True)
    start: Mapped[int] = mapped_column(index=True)
    stop: Mapped[int] = mapped_column(index=True)
    orientation: Mapped[int] = mapped_column()
    gene_id: Mapped[str] = mapped_column(String(255))
    gene_id_short: Mapped[str] = mapped_column(String(255))
    hgnc_id: Mapped[str] = mapped_column(String(255), index=True)
    symbol: Mapped[str] = mapped_column(String(50), index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
