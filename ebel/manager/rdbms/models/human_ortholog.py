"""HGNC Human Ortholog RDBMS model definition."""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class HumanOrtholog(Base):
    """Class definition for the human_ortholog table."""

    __tablename__ = 'human_ortholog'

    id = Column(Integer, primary_key=True)

    hgnc_id = Column(String(20), index=True)
    human_entrez_gene = Column(Integer)
    human_ensembl_gene = Column(String(20))
    human_symbol = Column(String(50), index=True)
    ortholog_species = Column(Integer, index=True)
    ortholog_species_entrez_gene = Column(Integer)
    ortholog_species_ensembl_gene = Column(String(50))
    ortholog_species_db_id = Column(String(50))
    ortholog_species_symbol = Column(String(50), index=True)
    support = Column(Text)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
