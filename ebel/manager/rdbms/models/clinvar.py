"""ClinVar RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, Text, ForeignKey, Index

from ebel.manager.rdbms.models import object_as_dict


Base = declarative_base()

clinvar__clinvar_phenotype = Table('clinvar__phenotype', Base.metadata,
                                   Column('clinvar_id', Integer, ForeignKey('clinvar.id')),
                                   Column('clinvar_phenotype_id', Integer, ForeignKey('clinvar_phenotype.id'))
                                   )


class ClinvarPhenotypeMedgen(Base):
    """Class definition for the clinvar_phenotype_medgen table."""

    __tablename__ = 'clinvar_phenotype_medgen'
    id = Column(Integer, primary_key=True)

    identifier = Column(String(100), index=True)
    clinvar_id = Column(Integer, ForeignKey('clinvar.id'))
    clinvar = relationship("Clinvar", foreign_keys=[clinvar_id], viewonly=True)


class ClinvarOtherIdentifier(Base):
    """Class definition for the clinvar_other_identifier table."""

    __tablename__ = 'clinvar_other_identifier'
    id = Column(Integer, primary_key=True)

    db = Column(String(100), index=True)
    identifier = Column(String(100), index=True)
    clinvar_id = Column(Integer, ForeignKey('clinvar.id'))
    clinvar = relationship("Clinvar", foreign_keys=[clinvar_id], viewonly=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'db': self.db, 'identifier': self.identifier}


class Clinvar(Base):
    """Class definition for the clinvar table."""

    __tablename__ = 'clinvar'
    id = Column(Integer, primary_key=True)

    allele_id = Column(Integer)
    type = Column(String(100))
    name = Column(String(1000))
    gene_id = Column(Integer, index=True)
    gene_symbol = Column(String(1000))
    hgnc_id = Column(String(100))
    clinical_significance = Column(String(100))
    clin_sig_simple = Column(Integer)
    last_evaluated = Column(String(100))
    rs_db_snp = Column(Integer, index=True)
    nsv_esv_db_var = Column(String(100))
    rcvaccession = Column(String(1000))
    origin = Column(Text)
    origin_simple = Column(Text)
    assembly = Column(String(100), index=True)
    chromosome_accession = Column(Text)
    chromosome = Column(Text)
    start = Column(Integer)
    stop = Column(Integer)
    reference_allele = Column(Text)
    alternate_allele = Column(Text)
    cytogenetic = Column(Text)
    review_status = Column(Text)
    number_submitters = Column(Integer)
    guidelines = Column(Text)
    tested_in_gtr = Column(Text)
    submitter_categories = Column(Integer)
    variation_id = Column(Integer)
    position_vcf = Column(Integer)
    reference_allele_vcf = Column(Text(100000))
    alternate_allele_vcf = Column(Text(100000))

    phenotypeMedgens = relationship("ClinvarPhenotypeMedgen", foreign_keys=[ClinvarPhenotypeMedgen.clinvar_id])
    otherIdentifiers = relationship("ClinvarOtherIdentifier", foreign_keys=[ClinvarOtherIdentifier.clinvar_id])

    phenotypes = relationship(
        "ClinvarPhenotype",
        secondary=clinvar__clinvar_phenotype)

    __table_args__ = (Index('ix_clinvar__gene_symbol', gene_symbol, mysql_length=500),)

    def as_dict(self):
        """Convert object values to dictionary."""
        clinvar_entry = object_as_dict(self)
        clinvar_entry.update({'phenotypeMedgens': [x.identifier for x in self.phenotypeMedgens]})
        clinvar_entry.update({'otherIdentifiers': [x.as_dict() for x in self.otherIdentifiers]})
        return clinvar_entry


class ClinvarPhenotype(Base):
    """Class definition for the clinvar_phenotype table."""

    __tablename__ = 'clinvar_phenotype'
    id = Column(Integer, primary_key=True)
    phenotype = Column(Text)

    clinvars = relationship(
        "Clinvar",
        secondary=clinvar__clinvar_phenotype,
        back_populates="phenotypes")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'phenotype': self.phenotype}
