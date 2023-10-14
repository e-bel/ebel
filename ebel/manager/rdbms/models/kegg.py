"""KEGG RDBMS model definition."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Kegg(Base):
    """Class definition for the kegg table."""

    __tablename__ = "kegg"
    id: Mapped[int] = mapped_column(primary_key=True)

    pathway_identifier: Mapped[str] = mapped_column(String(100))
    pathway_name: Mapped[str] = mapped_column(String(1000))
    kegg_species_id: Mapped[str] = mapped_column(String(100))
    kegg_gene_id_a: Mapped[str] = mapped_column(String(100))
    gene_symbol_a: Mapped[str] = mapped_column(String(100), index=True)
    kegg_gene_id_b: Mapped[str] = mapped_column(String(100))
    gene_symbol_b: Mapped[str] = mapped_column(String(100), index=True)
    kegg_int_type: Mapped[str] = mapped_column(String(100))
    interaction_type: Mapped[str] = mapped_column(String(50), index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
