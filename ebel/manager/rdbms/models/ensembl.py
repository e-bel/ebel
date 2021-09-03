"""EnsEMBL RDBMS model definition."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Ensembl(Base):
    """Class definition for the ensembl table."""

    __tablename__ = 'ensembl'
    id = Column(Integer, primary_key=True)
    enst = Column(String(20), index=True)
    version = Column(Integer)
    chromosome = Column(String(10), index=True)
    start = Column(Integer, index=True)
    stop = Column(Integer, index=True)
    orientation = Column(Integer)
    gene_id = Column(String(255))
    gene_id_short = Column(String(255))
    hgnc_id = Column(String(255), index=True)
    symbol = Column(String(50), index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
