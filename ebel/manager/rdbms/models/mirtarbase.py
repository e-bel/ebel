"""KEGG RDBMS model definition."""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Mirtarbase(Base):
    """Class definition for the mirtarbase table."""

    __tablename__ = 'mirtarbase'
    id = Column(Integer, primary_key=True)

    mi_rtar_base_id = Column(String(20))
    mi_rna = Column(String(50))
    species_mi_rna = Column(String(50), index=True)
    target_gene = Column(String(50), index=True)
    target_gene_entrez_id = Column(Integer)
    species_target_gene = Column(String(50), index=True)
    experiments = Column(Text)
    support_type = Column(String(50), index=True)
    references_pmid = Column(Integer)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
