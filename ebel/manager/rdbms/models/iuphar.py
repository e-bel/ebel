"""IUPHAR RDBMS model definition."""
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class IupharLigand(Base):
    """Class definition for the iuphar_ligand table."""

    __tablename__ = "iuphar_ligand"
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(Text)
    species: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text)
    approved: Mapped[Optional[bool]] = mapped_column()
    withdrawn: Mapped[Optional[bool]] = mapped_column()
    labelled: Mapped[Optional[bool]] = mapped_column()
    radioactive: Mapped[Optional[bool]] = mapped_column()
    pubchem_sid: Mapped[Optional[int]] = mapped_column()
    pubchem_cid: Mapped[Optional[int]] = mapped_column(
        Text
    )  # TODO: This is a integer, but for import reasons this changed to text
    uniprot_id: Mapped[Optional[str]] = mapped_column(Text)
    ensembl_id: Mapped[Optional[str]] = mapped_column(Text)
    ligand_subunit_ids: Mapped[Optional[str]] = mapped_column(Text)
    ligand_subunit_name: Mapped[Optional[str]] = mapped_column(Text)
    ligand_subunit_uni_prot_ids: Mapped[Optional[str]] = mapped_column(Text)
    ligand_subunit_ensembl_ids: Mapped[Optional[str]] = mapped_column(Text)
    iupac_name: Mapped[Optional[str]] = mapped_column(Text)
    inn: Mapped[Optional[str]] = mapped_column(Text)
    synonyms: Mapped[Optional[str]] = mapped_column(Text)
    smiles: Mapped[Optional[str]] = mapped_column(Text)
    inchi_key: Mapped[Optional[str]] = mapped_column(Text)
    inchi: Mapped[Optional[str]] = mapped_column(Text)
    gto_immu_pdb: Mapped[Optional[bool]] = mapped_column()
    gto_mpdb: Mapped[Optional[bool]] = mapped_column()
    antibacterial: Mapped[Optional[bool]] = mapped_column()

    interactions: Mapped[List["IupharInteraction"]] = relationship("IupharInteraction")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class IupharInteraction(Base):
    """Class definition for the iuphar_interaction table."""

    __tablename__ = "iuphar_interaction"
    id = mapped_column(Integer, primary_key=True)

    target: Mapped[Optional[str]] = mapped_column(String(255))
    target_id: Mapped[Optional[int]] = mapped_column()
    target_subunit_ids: Mapped[Optional[str]] = mapped_column(Text)
    target_gene_symbol: Mapped[Optional[str]] = mapped_column(String(100))
    target_uniprot: Mapped[Optional[str]] = mapped_column(String(100))
    target_ensembl_gene_id: Mapped[Optional[str]] = mapped_column(String(200))
    target_ligand: Mapped[Optional[str]] = mapped_column(String(100))
    target_ligand_id: Mapped[Optional[str]] = mapped_column()
    target_ligand_subunit_ids: Mapped[Optional[str]] = mapped_column(Text)
    target_ligand_gene_symbol: Mapped[Optional[str]] = mapped_column(String(50))
    target_ligand_uniprot_id: Mapped[Optional[str]] = mapped_column(String(200))
    target_ligand_ensembl_gene_id: Mapped[Optional[str]] = mapped_column(String(50))
    target_ligand_pubchem_sid: Mapped[Optional[str]] = mapped_column()
    target_species: Mapped[Optional[str]] = mapped_column(String(100))
    ligand: Mapped[str] = mapped_column(String(255))
    ligand_id: Mapped[int] = mapped_column(ForeignKey("iuphar_ligand.id"), index=True)
    ligand_subunit_ids: Mapped[Optional[str]] = mapped_column(Text)
    ligand_gene_symbol: Mapped[Optional[str]] = mapped_column(String(50))
    ligand_species: Mapped[Optional[str]] = mapped_column(String(50))
    ligand_pubchem_sid: Mapped[Optional[int]] = mapped_column()
    ligand_type: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column()
    type: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    action_comment: Mapped[Optional[str]] = mapped_column(String(255))
    selectivity: Mapped[Optional[str]] = mapped_column(String(50))
    endogenous: Mapped[bool] = mapped_column()
    primary_target: Mapped[bool] = mapped_column()
    concentration_range: Mapped[Optional[str]] = mapped_column(String(50))
    affinity_units: Mapped[str] = mapped_column(String(10))
    affinity_high: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    affinity_median: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    affinity_low: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    original_affinity_units: Mapped[Optional[str]] = mapped_column(String(10))
    original_affinity_low_nm: Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    original_affinity_median_nm: Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    original_affinity_high_nm: Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    original_affinity_relation: Mapped[Optional[str]] = mapped_column(String(1))
    assay_description: Mapped[Optional[str]] = mapped_column(Text)
    receptor_site: Mapped[Optional[str]] = mapped_column(String(100))
    ligand_context: Mapped[Optional[str]] = mapped_column(String(50))
    pubmed_id: Mapped[Optional[str]] = mapped_column(Text)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
