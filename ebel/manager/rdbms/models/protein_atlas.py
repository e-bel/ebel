"""Protein Atlas RDBMS model definition."""
from typing import Optional

from sqlalchemy import Column, Integer, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, Mapped

Base = declarative_base()


class ProteinAtlasNormalTissue(Base):
    """Class definition for the protein_atlas_normal_tissue table."""

    __tablename__ = "protein_atlas_normal_tissue"
    id: Mapped[int] = mapped_column(primary_key=True)

    gene: Mapped[str] = mapped_column(String(100), index=True)
    gene_name: Mapped[str] = mapped_column(String(100))
    tissue: Mapped[Optional[str]] = mapped_column(String(100))
    cell_type: Mapped[Optional[str]] = mapped_column(String(100))
    level: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    reliability: Mapped[str] = mapped_column(String(100), index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "tissue": self.tissue,
            "cell_type": self.cell_type,
            "level": self.level,
            "reliability": self.reliability,
        }


class ProteinAtlasSubcellularLocation(Base):
    """Class definition for the protein_atlas_subcellular_location table."""

    __tablename__ = "protein_atlas_subcellular_location"
    id: Mapped[int] = mapped_column(primary_key=True)

    gene: Mapped[str] = mapped_column(String(100))
    gene_name: Mapped[str] = mapped_column(String(100))
    reliability: Mapped[str] = mapped_column(String(100))
    main_location: Mapped[Optional[str]] = mapped_column(String(100))
    additional_location: Mapped[Optional[str]] = mapped_column(String(100))
    extracellular_location: Mapped[Optional[str]] = mapped_column(String(100))
    enhanced: Mapped[Optional[str]] = mapped_column(String(100))
    supported: Mapped[Optional[str]] = mapped_column(String(100))
    approved: Mapped[Optional[str]] = mapped_column(String(100))
    uncertain: Mapped[Optional[str]] = mapped_column(String(100))
    single_cell_variation_intensity: Mapped[Optional[str]] = mapped_column(String(100))
    single_cell_variation_spatial: Mapped[Optional[str]] = mapped_column(String(100))
    cell_cycle_dependency: Mapped[Optional[str]] = mapped_column(Text)
    go_id: Mapped[str] = mapped_column(Text)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "reliability": self.reliability,
            "main_location": self.main_location,
            "additional_location": self.additional_location,
            "extracellular_location": self.extracellular_location,
            "enhanced": self.enhanced,
            "supported": self.supported,
            "approved": self.approved,
            "uncertain": self.uncertain,
            "single_cell_variation_intensity": self.single_cell_variation_intensity,
            "single_cell_variation_spatial": self.single_cell_variation_spatial,
            "cell_cycle_dependency": self.cell_cycle_dependency,
            "go_id": self.go_id,
        }


class ProteinAtlasRnaTissueConsensus(Base):
    """Class definition for the protein_atlas_rna_tissue_consensus table."""

    __tablename__ = "protein_atlas_rna_tissue_consensus"
    id: Mapped[int] = mapped_column(primary_key=True)

    gene: Mapped[str] = mapped_column(String(100), index=True)
    gene_name: Mapped[str] = mapped_column(String(100), index=True)
    tissue: Mapped[str] = mapped_column(String(100), index=True)
    n_tpm: Mapped[float] = mapped_column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "tissue": self.tissue,
            "n_tpm": self.nx,
        }


class ProteinAtlasRnaBrainGtex(Base):
    """Class definition for the protein_atlas_rna_brain_gtex table."""

    __tablename__ = "protein_atlas_rna_brain_gtex"
    id: Mapped[int] = mapped_column(primary_key=True)

    gene: Mapped[str] = mapped_column(String(100), index=True)
    gene_name: Mapped[str] = mapped_column(String(100), index=True)
    brain_region: Mapped[str] = mapped_column(String(100), index=True)
    tpm: Mapped[float] = mapped_column(Numeric(8, 1))
    p_tpm: Mapped[float] = mapped_column(Numeric(8, 1))
    n_tpm: Mapped[float] = mapped_column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "brain_region": self.brain_region,
            "tpm": self.tpm,
            "p_tpm": self.p_tpm,
            "n_tpm": self.nx,
        }


class ProteinAtlasRnaBrainFantom(Base):
    """Class definition for the protein_atlas_rna_brain_fantom table."""

    __tablename__ = "protein_atlas_rna_brain_fantom"
    id: Mapped[int] = mapped_column(primary_key=True)

    gene: Mapped[str] = mapped_column(String(100))
    gene_name: Mapped[str] = mapped_column(String(100))
    brain_region: Mapped[str] = mapped_column(String(100))
    tags_per_million: Mapped[str] = mapped_column(String(100))
    scaled_tags_per_million: Mapped[str] = mapped_column(String(100))
    n_tpm: Mapped[str] = mapped_column(String(100))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "brain_region": self.brain_region,
            "tags_per_million": self.tags_per_million,
            "scaled_tags_per_million": self.scaled_tags_per_million,
            "n_tpm": self.nx,
        }


class ProteinAtlasRnaMouseBrainAllen(Base):
    """Class definition for the protein_atlas_rna_mouse_brain_allen table."""

    __tablename__ = "protein_atlas_rna_mouse_brain_allen"
    id: Mapped[int] = mapped_column(primary_key=True)

    gene: Mapped[str] = mapped_column(String(100))
    gene_name: Mapped[str] = mapped_column(String(100))
    brain_region: Mapped[str] = mapped_column(String(100))
    expression_energy: Mapped[float] = mapped_column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "brain_region": self.brain_region,
            "expression_energy": self.expression_energy,
        }
