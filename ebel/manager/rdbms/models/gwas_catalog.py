"""GWAS Catalog RDBMS model definition."""
from typing import List, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class GwasCatalog(Base):
    """Class definition for the gwascatalog table."""

    __tablename__ = "gwascatalog"
    id: Mapped[int] = mapped_column(primary_key=True)
    date_added_to_catalog: Mapped[str] = mapped_column(String(255))
    pubmedid: Mapped[int] = mapped_column()
    first_author: Mapped[str] = mapped_column(String(255))
    date: Mapped[str] = mapped_column(String(255))
    journal: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(String(255))
    study: Mapped[str] = mapped_column(Text)
    disease_trait: Mapped[str] = mapped_column(String(255))
    initial_sample_size: Mapped[Optional[str]] = mapped_column(Text)
    replication_sample_size: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(String(50))
    chr_id: Mapped[Optional[str]] = mapped_column(Text)
    chr_pos: Mapped[Optional[str]] = mapped_column(Text)
    reported_gene_s: Mapped[Optional[str]] = mapped_column(Text)
    mapped_gene: Mapped[Optional[str]] = mapped_column(Text)
    upstream_gene_id: Mapped[Optional[str]] = mapped_column(String(50))
    downstream_gene_id: Mapped[Optional[str]] = mapped_column(String(50))
    upstream_gene_distance: Mapped[Optional[int]] = mapped_column()
    downstream_gene_distance: Mapped[Optional[int]] = mapped_column()
    strongest_snp_risk_allele: Mapped[Optional[int]] = mapped_column(Text)
    snp: Mapped[Optional[int]] = mapped_column(Text)
    merged: Mapped[Optional[int]] = mapped_column()
    snp_id_current: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text)
    intergenic: Mapped[Optional[int]] = mapped_column()
    risk_allele_frequency: Mapped[Optional[str]] = mapped_column(Text)
    p_value: Mapped[Optional[float]] = mapped_column()
    pvalue_mlog: Mapped[Optional[float]] = mapped_column()
    p_value_text: Mapped[Optional[str]] = mapped_column(Text)
    or_or_beta: Mapped[Optional[float]] = mapped_column()
    _95_ci_text: Mapped[Optional[str]] = mapped_column(Text)
    platform_snps_passing_qc: Mapped[Optional[str]] = mapped_column(Text)
    cnv: Mapped[Optional[str]] = mapped_column(Text)

    snp_genes: Mapped[List["SnpGene"]] = relationship("SnpGene", back_populates="gwascatalog")

    def as_dict(self):
        """Convert object values to dictionary."""
        gwas_catalog = object_as_dict(self)
        gwas_catalog.update({"snp_genes": [x.ensembl_identifier for x in self.snp_genes]})
        return gwas_catalog


class SnpGene(Base):
    """Class definition for the gwascatalog_snpgene table."""

    __tablename__ = "gwascatalog_snpgene"
    id: Mapped[int] = mapped_column(primary_key=True)
    ensembl_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    gwascatalog_id: Mapped[int] = mapped_column(ForeignKey("gwascatalog.id"))
    gwascatalog: Mapped[GwasCatalog] = relationship("GwasCatalog", back_populates="snp_genes")
