"""IUPHAR RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, BigInteger, Numeric

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class IupharLigand(Base):
    """Class definition for the iuphar_ligand table."""

    __tablename__ = 'iuphar_ligand'
    id = Column(Integer, primary_key=True)

    name = Column(Text)
    species = Column(Text)
    type = Column(Text)
    approved = Column(Boolean)
    withdrawn = Column(Boolean)
    labelled = Column(Boolean)
    radioactive = Column(Boolean)
    pubchem_sid = Column(BigInteger)
    pubchem_cid = Column(Text)  # TODO: This is a integer, but for import reasons this changed to text
    uniprot_id = Column(Text)
    iupac_name = Column(Text)
    inn = Column(Text)
    synonyms = Column(Text)
    smiles = Column(Text)
    inchi_key = Column(Text)
    inchi = Column(Text)
    gto_immu_pdb = Column(Boolean)
    gto_mpdb = Column(Boolean)

    interactions = relationship("IupharInteraction")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class IupharInteraction(Base):
    """Class definition for the iuphar_interaction table."""

    __tablename__ = 'iuphar_interaction'
    id = Column(Integer, primary_key=True)

    target = Column(String(255))
    target_id = Column(Integer)
    target_gene_symbol = Column(String(100))
    target_uniprot = Column(String(100))
    target_ensembl_gene_id = Column(String(200))
    target_ligand = Column(String(100))
    target_ligand_id = Column(Integer)
    target_ligand_gene_symbol = Column(String(50))
    target_ligand_ensembl_gene_id = Column(String(50))
    target_ligand_uniprot = Column(String(50))
    target_ligand_pubchem_sid = Column(Integer)
    target_species = Column(String(100))
    ligand = Column(String(255))
    ligand_id = Column(Integer, ForeignKey('iuphar_ligand.id'), index=True)
    ligand_gene_symbol = Column(String(50))
    ligand_species = Column(String(50))
    ligand_pubchem_sid = Column(Integer)
    approved_drug = Column(Text)
    type = Column(String(100))
    action = Column(String(100))
    action_comment = Column(String(255))
    selectivity = Column(String(50))
    endogenous = Column(Boolean)
    primary_target = Column(Boolean)
    concentration_range = Column(String(50))
    affinity_units = Column(String(10))
    affinity_high = Column(Numeric(6, 2))
    affinity_median = Column(Numeric(6, 2))
    affinity_low = Column(Numeric(6, 2))
    original_affinity_units = Column(String(10))
    original_affinity_low_nm = Column(Numeric(12, 3))
    original_affinity_median_nm = Column(Numeric(12, 3))
    original_affinity_high_nm = Column(Numeric(12, 3))
    original_affinity_relation = Column(String(1))
    assay_description = Column(Text)
    receptor_site = Column(String(100))
    ligand_context = Column(String(50))
    pubmed_id = Column(Text)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
