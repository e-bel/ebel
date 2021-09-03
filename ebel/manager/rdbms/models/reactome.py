"""Reactome RDBMS model definition."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Reactome(Base):
    """Class definition for the reactome table."""

    __tablename__ = 'reactome'
    id = Column(Integer, primary_key=True)
    identifier = Column(String(50), index=True)
    uniprot_accession = Column(String(50), index=True)
    organism = Column(String(255))
    name = Column(String(255))
    evidence_type = Column(String(255))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
