"""NSIDES RDBMS model definition."""

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Nsides(Base):
    """Class definition for the nSIDES table."""

    __tablename__ = 'nsides'
    id = Column(Integer, primary_key=True)

    drug_rxnorn_id = Column(String(20), index=True)  # This has to be a String because of mapping to drugbank ids
    drug_concept_name = Column(String(255), index=True)

    source = Column(String(10), index=True)

    condition_meddra_id = Column(Integer)
    condition_concept_name = Column(String(255), index=True)

    # OnSIDES specific
    vocabulary_id = Column(String(10))
    domain_id = Column(String(10))

    # OFFSIDES specific
    a = Column(Integer)
    b = Column(Integer)
    c = Column(Integer)
    d = Column(Integer)
    prr = Column(Float)
    prr_error = Column(Float)
    mean_reporting_frequency = Column(Float, index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
