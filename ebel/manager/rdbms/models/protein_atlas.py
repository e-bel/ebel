"""Protein Atlas RDBMS model definition."""
from sqlalchemy import Column, Integer, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

Base = declarative_base()


class ProteinAtlasNormalTissue(Base):
    """Class definition for the protein_atlas_normal_tissue table."""

    __tablename__ = "protein_atlas_normal_tissue"
    id = mapped_column(Integer, primary_key=True)

    gene = mapped_column(String(100), index=True)
    gene_name = mapped_column(String(100))
    tissue = mapped_column(String(100))
    cell_type = mapped_column(String(100))
    level = mapped_column(String(100), index=True)
    reliability = mapped_column(String(100), index=True)

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
    id = mapped_column(Integer, primary_key=True)

    gene = mapped_column(String(100))
    gene_name = mapped_column(String(100))
    reliability = mapped_column(String(100))
    main_location = mapped_column(String(100))
    additional_location = mapped_column(String(100))
    extracellular_location = mapped_column(String(100))
    enhanced = mapped_column(String(100))
    supported = mapped_column(String(100))
    approved = mapped_column(String(100))
    uncertain = mapped_column(String(100))
    single_cell_variation_intensity = mapped_column(String(100))
    single_cell_variation_spatial = mapped_column(String(100))
    cell_cycle_dependency = mapped_column(Text)
    go_id = mapped_column(Text)

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
    id = mapped_column(Integer, primary_key=True)

    gene = mapped_column(String(100), index=True)
    gene_name = mapped_column(String(100), index=True)
    tissue = mapped_column(String(100), index=True)
    n_tpm = mapped_column(Numeric(8, 1))

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
    id = mapped_column(Integer, primary_key=True)

    gene = mapped_column(String(100), index=True)
    gene_name = mapped_column(String(100), index=True)
    brain_region = mapped_column(String(100), index=True)
    tpm = mapped_column(Numeric(8, 1))
    p_tpm = mapped_column(Numeric(8, 1))
    n_tpm = mapped_column(Numeric(8, 1))

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
    id = mapped_column(Integer, primary_key=True)

    gene = mapped_column(String(100))
    gene_name = mapped_column(String(100))
    brain_region = mapped_column(String(100))
    tags_per_million = mapped_column(String(100))
    scaled_tags_per_million = mapped_column(String(100))
    n_tpm = mapped_column(String(100))

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
    id = mapped_column(Integer, primary_key=True)

    gene = mapped_column(String(100))
    gene_name = mapped_column(String(100))
    brain_region = mapped_column(String(100))
    expression_energy = mapped_column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "gene": self.gene,
            "gene_name": self.gene_name,
            "brain_region": self.brain_region,
            "expression_energy": self.expression_energy,
        }
