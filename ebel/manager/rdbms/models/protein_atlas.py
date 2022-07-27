"""Protein Atlas RDBMS model definition."""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Numeric

Base = declarative_base()


class ProteinAtlasNormalTissue(Base):
    """Class definition for the protein_atlas_normal_tissue table."""

    __tablename__ = 'protein_atlas_normal_tissue'
    id = Column(Integer, primary_key=True)

    gene = Column(String(100), index=True)
    gene_name = Column(String(100))
    tissue = Column(String(100))
    cell_type = Column(String(100))
    level = Column(String(100), index=True)
    reliability = Column(String(100), index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'gene': self.gene,
                'gene_name': self.gene_name,
                'tissue': self.tissue,
                'cell_type': self.cell_type,
                'level': self.level,
                'reliability': self.reliability}


class ProteinAtlasSubcellularLocation(Base):
    """Class definition for the protein_atlas_subcellular_location table."""

    __tablename__ = 'protein_atlas_subcellular_location'
    id = Column(Integer, primary_key=True)

    gene = Column(String(100))
    gene_name = Column(String(100))
    reliability = Column(String(100))
    main_location = Column(String(100))
    additional_location = Column(String(100))
    extracellular_location = Column(String(100))
    enhanced = Column(String(100))
    supported = Column(String(100))
    approved = Column(String(100))
    uncertain = Column(String(100))
    single_cell_variation_intensity = Column(String(100))
    single_cell_variation_spatial = Column(String(100))
    cell_cycle_dependency = Column(Text)
    go_id = Column(Text)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'gene': self.gene,
                'gene_name': self.gene_name,
                'reliability': self.reliability,
                'main_location': self.main_location,
                'additional_location': self.additional_location,
                'extracellular_location': self.extracellular_location,
                'enhanced': self.enhanced,
                'supported': self.supported,
                'approved': self.approved,
                'uncertain': self.uncertain,
                'single_cell_variation_intensity': self.single_cell_variation_intensity,
                'single_cell_variation_spatial': self.single_cell_variation_spatial,
                'cell_cycle_dependency': self.cell_cycle_dependency,
                'go_id': self.go_id}


class ProteinAtlasRnaTissueConsensus(Base):
    """Class definition for the protein_atlas_rna_tissue_consensus table."""

    __tablename__ = 'protein_atlas_rna_tissue_consensus'
    id = Column(Integer, primary_key=True)

    gene = Column(String(100), index=True)
    gene_name = Column(String(100), index=True)
    tissue = Column(String(100), index=True)
    nx = Column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'gene': self.gene,
                'gene_name': self.gene_name,
                'tissue': self.tissue,
                'nx': self.nx}


class ProteinAtlasRnaBrainGtex(Base):
    """Class definition for the protein_atlas_rna_brain_gtex table."""

    __tablename__ = 'protein_atlas_rna_brain_gtex'
    id = Column(Integer, primary_key=True)

    gene = Column(String(100), index=True)
    gene_name = Column(String(100), index=True)
    brain_region = Column(String(100), index=True)
    tpm = Column(Numeric(8, 1))
    p_tpm = Column(Numeric(8, 1))
    nx = Column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'gene': self.gene,
            'gene_name': self.gene_name,
            'brain_region': self.brain_region,
            'tpm': self.tpm,
            'p_tpm': self.p_tpm,
            'nx': self.nx
        }


class ProteinAtlasRnaBrainFantom(Base):
    """Class definition for the protein_atlas_rna_brain_fantom table."""

    __tablename__ = 'protein_atlas_rna_brain_fantom'
    id = Column(Integer, primary_key=True)

    gene = Column(String(100))
    gene_name = Column(String(100))
    brain_region = Column(String(100))
    tags_per_million = Column(String(100))
    scaled_tags_per_million = Column(String(100))
    nx = Column(String(100))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'gene': self.gene,
                'gene_name': self.gene_name,
                'brain_region': self.brain_region,
                'tags_per_million': self.tags_per_million,
                'scaled_tags_per_million': self.scaled_tags_per_million,
                'nx': self.nx}


class ProteinAtlasRnaMouseBrainAllen(Base):
    """Class definition for the protein_atlas_rna_mouse_brain_allen table."""

    __tablename__ = 'protein_atlas_rna_mouse_brain_allen'
    id = Column(Integer, primary_key=True)

    gene = Column(String(100))
    gene_name = Column(String(100))
    brain_region = Column(String(100))
    expression_energy = Column(Numeric(8, 1))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'gene': self.gene,
            'gene_name': self.gene_name,
            'brain_region': self.brain_region,
            'expression_energy': self.expression_energy
        }
