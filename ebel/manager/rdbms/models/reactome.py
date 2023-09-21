"""Reactome RDBMS model definition."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Reactome(Base):
    """Class definition for the reactome table."""

    __tablename__ = "reactome"
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(String(50), index=True)
    uniprot_accession: Mapped[str] = mapped_column(String(50), index=True)
    organism: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    evidence_type: Mapped[str] = mapped_column(String(255))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
