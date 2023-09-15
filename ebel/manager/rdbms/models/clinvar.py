"""ClinVar RDBMS model definition."""
from typing import List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Table, Text, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column, Mapped

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()

clinvar__clinvar_phenotype = Table(
    "clinvar__phenotype",
    Base.metadata,
    Column("clinvar_id", Integer, ForeignKey("clinvar.id")),
    Column("clinvar_phenotype_id", Integer, ForeignKey("clinvar_phenotype.id")),
)


class ClinvarPhenotypeMedgen(Base):
    """Class definition for the clinvar_phenotype_medgen table."""

    __tablename__ = "clinvar_phenotype_medgen"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier: Mapped[str] = mapped_column(String(100), index=True)
    clinvar_id: Mapped[int] = mapped_column(Integer, ForeignKey("clinvar.id"))
    clinvar: Mapped["Clinvar"] = relationship("Clinvar", foreign_keys=[clinvar_id], viewonly=True)


class ClinvarOtherIdentifier(Base):
    """Class definition for the clinvar_other_identifier table."""

    __tablename__ = "clinvar_other_identifier"
    id: Mapped[int] = mapped_column(primary_key=True)

    db: Mapped[str] = mapped_column(String(100), index=True)
    identifier: Mapped[str] = mapped_column(String(100), index=True)
    clinvar_id: Mapped[int] = mapped_column(ForeignKey("clinvar.id"))
    clinvar: Mapped["Clinvar"] = relationship("Clinvar", foreign_keys=[clinvar_id], viewonly=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"db": self.db, "identifier": self.identifier}


class Clinvar(Base):
    """Class definition for the clinvar table."""

    __tablename__ = "clinvar"
    id: Mapped[int] = mapped_column(primary_key=True)

    allele_id: Mapped[int] = mapped_column()
    type: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))
    gene_id: Mapped[int] = mapped_column(index=True)
    gene_symbol: Mapped[str] = mapped_column(String(1000))
    hgnc_id: Mapped[str] = mapped_column(String(100))
    clinical_significance: Mapped[str] = mapped_column(String(100))
    clin_sig_simple: Mapped[int] = mapped_column()
    last_evaluated: Mapped[Optional[str]] = mapped_column(String(100))
    rs_db_snp: Mapped[int] = mapped_column(index=True)
    nsv_esv_db_var: Mapped[str] = mapped_column(String(100))
    rcvaccession: Mapped[str] = mapped_column(String(1000))
    origin: Mapped[str] = mapped_column(Text)
    origin_simple: Mapped[str] = mapped_column(Text)
    assembly: Mapped[str] = mapped_column(String(100), index=True)
    chromosome_accession: Mapped[str] = mapped_column(Text)
    chromosome: Mapped[str] = mapped_column(Text)
    start: Mapped[int] = mapped_column()
    stop: Mapped[int] = mapped_column()
    reference_allele: Mapped[str] = mapped_column(Text)
    alternate_allele: Mapped[str] = mapped_column(Text)
    cytogenetic: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text)
    number_submitters: Mapped[int] = mapped_column()
    guidelines: Mapped[str] = mapped_column(Text)
    tested_in_gtr: Mapped[str] = mapped_column(Text)
    submitter_categories: Mapped[int] = mapped_column()
    variation_id: Mapped[int] = mapped_column()
    position_vcf: Mapped[int] = mapped_column()
    reference_allele_vcf: Mapped[str] = mapped_column(Text(100000))
    alternate_allele_vcf: Mapped[str] = mapped_column(Text(100000))

    phenotypeMedgens: Mapped[List["ClinvarPhenotypeMedgen"]] = relationship(
        "ClinvarPhenotypeMedgen", foreign_keys=[ClinvarPhenotypeMedgen.clinvar_id]
    )
    otherIdentifiers: Mapped[List["ClinvarOtherIdentifier"]] = relationship(
        "ClinvarOtherIdentifier", foreign_keys=[ClinvarOtherIdentifier.clinvar_id]
    )

    phenotypes: Mapped[List["ClinvarPhenotype"]] = relationship(
        "ClinvarPhenotype", secondary=clinvar__clinvar_phenotype
    )

    __table_args__ = (Index("ix_clinvar__gene_symbol", gene_symbol, mysql_length=500),)

    def as_dict(self):
        """Convert object values to dictionary."""
        clinvar_entry = object_as_dict(self)
        clinvar_entry.update({"phenotypeMedgens": [x.identifier for x in self.phenotypeMedgens]})
        clinvar_entry.update({"otherIdentifiers": [x.as_dict() for x in self.otherIdentifiers]})
        return clinvar_entry


class ClinvarPhenotype(Base):
    """Class definition for the clinvar_phenotype table."""

    __tablename__ = "clinvar_phenotype"
    id = mapped_column(Integer, primary_key=True)
    phenotype = mapped_column(Text)

    clinvars = relationship("Clinvar", secondary=clinvar__clinvar_phenotype, back_populates="phenotypes")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"phenotype": self.phenotype}
