"""Reactome RDBMS model definition."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Reactome(Base):
    """Class definition for the reactome table."""

    __tablename__ = "reactome"
    id = mapped_column(Integer, primary_key=True)
    identifier = mapped_column(String(50), index=True)
    uniprot_accession = mapped_column(String(50), index=True)
    organism = mapped_column(String(255))
    name = mapped_column(String(255))
    evidence_type = mapped_column(String(255))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
