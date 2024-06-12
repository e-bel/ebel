"""KEGG RDBMS model definition."""
from typing import Optional

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Mirtarbase(Base):
    """Class definition for the mirtarbase table."""

    __tablename__ = "mirtarbase"
    id: Mapped[int] = mapped_column(primary_key=True)

    mi_rtar_base_id: Mapped[str] = mapped_column(String(20))
    mi_rna: Mapped[str] = mapped_column(String(50))
    species_mi_rna: Mapped[str] = mapped_column(String(50), index=True)
    target_gene: Mapped[str] = mapped_column(String(50), index=True)
    target_gene_entrez_id: Mapped[int] = mapped_column()
    species_target_gene: Mapped[str] = mapped_column(String(50), index=True)
    experiments: Mapped[str] = mapped_column(Text)
    support_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    references_pmid: Mapped[int] = mapped_column()

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
