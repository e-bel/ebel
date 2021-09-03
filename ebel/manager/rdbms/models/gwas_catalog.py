"""GWAS Catalog RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class GwasCatalog(Base):
    """Class definition for the gwascatalog table."""

    __tablename__ = 'gwascatalog'
    id = Column(Integer, primary_key=True)
    date_added_to_catalog = Column(String(255))
    pubmedid = Column(Integer)
    first_author = Column(String(255))
    date = Column(String(255))
    journal = Column(String(255))
    link = Column(String(255))
    study = Column(Text)
    disease_trait = Column(String(255))
    initial_sample_size = Column(Text)
    replication_sample_size = Column(Text)
    region = Column(String(50))
    chr_id = Column(Text)
    chr_pos = Column(Text)
    reported_gene_s = Column(Text)
    mapped_gene = Column(Text)
    upstream_gene_id = Column(String(50))
    downstream_gene_id = Column(String(50))
    upstream_gene_distance = Column(Integer)
    downstream_gene_distance = Column(Integer)
    strongest_snp_risk_allele = Column(Text)
    snp = Column(Text)
    merged = Column(Integer)
    snp_id_current = Column(Text)
    context = Column(Text)
    intergenic = Column(Integer)
    risk_allele_frequency = Column(Text)
    p_value = Column(Float)
    pvalue_mlog = Column(Float)
    p_value_text = Column(Text)
    or_or_beta = Column(Float)
    _95_ci_text = Column(Text)
    platform_snps_passing_qc = Column(Text)
    cnv = Column(Text)

    snp_genes = relationship("SnpGene", back_populates="gwascatalog")

    def as_dict(self):
        """Convert object values to dictionary."""
        gwas_catalog = object_as_dict(self)
        gwas_catalog.update({'snp_genes': [x.ensembl_identifier for x in self.snp_genes]})
        return gwas_catalog


class SnpGene(Base):
    """Class definition for the gwascatalog_snpgene table."""

    __tablename__ = 'gwascatalog_snpgene'
    id = Column(Integer, primary_key=True)
    ensembl_identifier = Column(String(100), nullable=False, index=True)
    gwascatalog_id = Column(Integer, ForeignKey('gwascatalog.id'))
    gwascatalog = relationship("GwasCatalog", back_populates="snp_genes")
