"""Expression Atlas RDBMS model definition."""
from typing import List

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Experiment(Base):
    """Table definition for experiment."""

    __tablename__ = "expression_atlas_experiment"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(Text)

    idfs: Mapped[List["Idf"]] = relationship("Idf", back_populates="experiment")
    group_comparisons: Mapped[List["GroupComparison"]] = relationship("GroupComparison", back_populates="experiment")
    sdrf_condenseds: Mapped[List["SdrfCondensed"]] = relationship("SdrfCondensed", back_populates="experiment")

    def as_dict(self):
        """Convert object values to dictionary."""
        experiment = object_as_dict(self)
        experiment.update({"idfs": {idf.key_name: idf.value for idf in self.idfs}})
        gc = [{"groups": x.group_comparison, "name": x.name, "id": x.id} for x in self.group_comparisons]
        experiment.update({"group_comparison": gc})
        return experiment


class Idf(Base):
    """Table definition for IDF."""

    __tablename__ = "expression_atlas_idf"

    id: Mapped[int] = mapped_column(primary_key=True)

    key_name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    experiment_id: Mapped[int] = mapped_column(ForeignKey("expression_atlas_experiment.id"))
    experiment: Mapped[Experiment] = relationship("Experiment", back_populates="idfs")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class GroupComparison(Base):
    """Table definition for group comparison."""

    __tablename__ = "expression_atlas_group_comparison"

    id: Mapped[int] = mapped_column(primary_key=True)

    experiment_id: Mapped[int] = mapped_column(ForeignKey("expression_atlas_experiment.id"))
    experiment: Mapped[Experiment] = relationship("Experiment", back_populates="group_comparisons")

    group_comparison: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(Text)

    fold_changes: Mapped[List["FoldChange"]] = relationship("FoldChange", back_populates="group_comparison")
    gseas: Mapped[List["Gsea"]] = relationship("Gsea", back_populates="group_comparison")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class FoldChange(Base):
    """Table definition for fold changes."""

    __tablename__ = "expression_atlas_foldchange"

    id: Mapped[int] = mapped_column(primary_key=True)

    gene_id: Mapped[str] = mapped_column(String(255))
    gene_name: Mapped[str] = mapped_column(String(100), index=True)
    log2foldchange: Mapped[float] = mapped_column(index=True)
    p_value: Mapped[float] = mapped_column(index=True)
    t_statistic: Mapped[float] = mapped_column()

    group_comparison_id: Mapped[int] = mapped_column(ForeignKey("expression_atlas_group_comparison.id"))
    group_comparison: Mapped[GroupComparison] = relationship("GroupComparison", back_populates="fold_changes")

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class SdrfCondensed(Base):
    """Table definition for SDRF condensed."""

    __tablename__ = "expression_atlas_sdrf_condensed"

    id: Mapped[int] = mapped_column(primary_key=True)

    experiment_id: Mapped[int] = mapped_column(ForeignKey("expression_atlas_experiment.id"))
    experiment: Mapped[Experiment] = relationship("Experiment", back_populates="sdrf_condenseds")

    method: Mapped[str] = mapped_column(String(255))
    sample: Mapped[str] = mapped_column(String(255))
    parameter_type: Mapped[str] = mapped_column(String(255))
    parameter: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)


class Gsea(Base):
    """Table definition for Genset enrichment table."""

    __tablename__ = "expression_atlas_gsea"

    id: Mapped[int] = mapped_column(primary_key=True)

    group_comparison_id: Mapped[int] = mapped_column(ForeignKey("expression_atlas_group_comparison.id"))
    group_comparison: Mapped[GroupComparison] = relationship("GroupComparison", back_populates="gseas")

    term: Mapped[str] = mapped_column(String(255), index=True)
    accession: Mapped[str] = mapped_column(String(255))
    genes_tot: Mapped[int] = mapped_column()
    stat_non_dir_p: Mapped[float] = mapped_column()
    p_adj_non_dir: Mapped[float] = mapped_column(index=True)
    significant_in_gene_set: Mapped[int] = mapped_column()
    non_significant_in_gene_set: Mapped[int] = mapped_column()
    significant_not_in_gene_set: Mapped[int] = mapped_column()
    non_significant_not_in_gene_set: Mapped[int] = mapped_column()
    effect_size: Mapped[float] = mapped_column()
    gsea_type: Mapped[str] = mapped_column(String(100))

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
