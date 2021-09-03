"""Expression Atlas RDBMS model definition."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Experiment(Base):
    """Table definition for experiment."""

    __tablename__ = 'expression_atlas_experiment'

    id = Column(Integer, primary_key=True)

    name = Column(String(100), index=True)
    title = Column(Text)

    idfs = relationship("Idf", back_populates="experiment")
    group_comparisons = relationship("GroupComparison", back_populates="experiment")
    sdrf_condenseds = relationship("SdrfCondensed", back_populates="experiment")

    def as_dict(self):
        """Convert object values to dictionary."""
        experiment = object_as_dict(self)
        experiment.update({'idfs': {idf.key_name: idf.value for idf in self.idfs}})
        gc = [{'groups': x.group_comparison, 'name': x.name, 'id': x.id} for x in self.group_comparisons]
        experiment.update({'group_comparison': gc})
        return experiment


class Idf(Base):
    """Table definition for IDF."""

    __tablename__ = 'expression_atlas_idf'

    id = Column(Integer, primary_key=True)

    key_name = Column(Text, nullable=False)
    value = Column(Text, nullable=False)

    experiment_id = Column(Integer, ForeignKey('expression_atlas_experiment.id'))
    experiment = relationship("Experiment", back_populates="idfs")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class GroupComparison(Base):
    """Table definition for group comparison."""

    __tablename__ = 'expression_atlas_group_comparison'

    id = Column(Integer, primary_key=True)

    experiment_id = Column(Integer, ForeignKey('expression_atlas_experiment.id'))
    experiment = relationship("Experiment", back_populates="group_comparisons")

    group_comparison = Column(String(100))
    name = Column(Text)

    fold_changes = relationship("FoldChange", back_populates="group_comparison")
    gseas = relationship("Gsea", back_populates="group_comparison")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class FoldChange(Base):
    """Table definition for fold changes."""

    __tablename__ = 'expression_atlas_foldchange'

    id = Column(Integer, primary_key=True)

    gene_id = Column(String(255))
    gene_name = Column(String(100, collation="utf8_bin"), index=True)
    log2foldchange = Column(Float, index=True)
    p_value = Column(Float, index=True)
    t_statistic = Column(Float)

    group_comparison_id = Column(Integer, ForeignKey('expression_atlas_group_comparison.id'))
    group_comparison = relationship("GroupComparison", back_populates="fold_changes")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class SdrfCondensed(Base):
    """Table definition for SDRF condensed."""

    __tablename__ = 'expression_atlas_sdrf_condensed'

    id = Column(Integer, primary_key=True)

    experiment_id = Column(Integer, ForeignKey('expression_atlas_experiment.id'))
    experiment = relationship("Experiment", back_populates="sdrf_condenseds")

    method = Column(String(255))
    sample = Column(String(255))
    parameter_type = Column(String(255))
    parameter = Column(String(255))
    value = Column(String(255))
    url = Column(String(255))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class Gsea(Base):
    """Table definition for Genset enrichment table."""

    __tablename__ = 'expression_atlas_gsea'

    id = Column(Integer, primary_key=True)

    group_comparison_id = Column(Integer, ForeignKey('expression_atlas_group_comparison.id'))
    group_comparison = relationship("GroupComparison", back_populates="gseas")

    term = Column(String(255), index=True)
    accession = Column(String(255))
    genes_tot = Column(Integer)
    stat_non_dir_p = Column(Float)
    p_adj_non_dir = Column(Float, index=True)
    significant_in_gene_set = Column(Integer)
    non_significant_in_gene_set = Column(Integer)
    significant_not_in_gene_set = Column(Integer)
    non_significant_not_in_gene_set = Column(Integer)
    effect_size = Column(Float)
    gsea_type = Column(String(100))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
