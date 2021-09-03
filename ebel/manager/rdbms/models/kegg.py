"""KEGG RDBMS model definition."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Kegg(Base):
    """Class definition for the kegg table."""

    __tablename__ = 'kegg'
    id = Column(Integer, primary_key=True)

    pathway_identifier = Column(String(100))
    pathway_name = Column(String(1000))
    kegg_species_id = Column(String(100))
    kegg_gene_id_a = Column(String(100))
    gene_symbol_a = Column(String(100), index=True)
    kegg_gene_id_b = Column(String(100))
    gene_symbol_b = Column(String(100), index=True)
    kegg_int_type = Column(String(100))
    interaction_type = Column(String(50), index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
