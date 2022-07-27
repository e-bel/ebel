"""NCBI RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey

from . import object_as_dict

Base = declarative_base()


class NcbiGeneInfo(Base):
    """Class definition for the ncbi_gene_info table."""

    __tablename__ = 'ncbi_gene_info'
    gene_id = Column(Integer, primary_key=True)

    tax_id = Column(Integer, index=True)
    symbol = Column(String(100), index=True)
    type_of_gene = Column(String(100), index=True)
    locus_tag = Column(String(100))
    chromosome = Column(String(100))
    map_location = Column(String(100))
    description_id = Column(Integer, ForeignKey('ncbi_gene_info_description.id'))
    description = relationship("NcbiGeneInfoDescription", foreign_keys=[description_id])
    xrefs = relationship("NcbiGeneInfoXref", back_populates="gene")
    mims = relationship("NcbiGeneMim", foreign_keys='NcbiGeneMim.gene_id', back_populates="gene")
    orthologs = relationship("NcbiGeneOrtholog", foreign_keys='NcbiGeneOrtholog.gene_id', back_populates="gene")
    ensembl_ids = relationship("NcbiGeneEnsembl", back_populates="genes")
    gene_ids_right = relationship("NcbiGeneOnRight", foreign_keys='NcbiGeneOnRight.gene_id', back_populates="gene")
    gene_ids_left = relationship("NcbiGeneOnLeft", foreign_keys='NcbiGeneOnLeft.gene_id', back_populates="gene")
    gene_ids_overlapping = relationship("NcbiGeneOverlapping", foreign_keys='NcbiGeneOverlapping.gene_id',
                                        back_populates="gene")

    def as_dict(self):
        """Convert object values to dictionary."""
        rdict = object_as_dict(self, ['description_id'])
        rdict.update({
            'xrefs': [{'db': x.db, 'dbid': x.dbid} for x in self.xrefs],
            'mims': [x.mim_number for x in self.mims],
            'description': self.description.description,
            'ensembls': [x.ensembl_gene_identifier for x in self.ensembl_ids],
            'orthologs': [x.other_gene_id for x in self.orthologs],
            'gene_ids_right': [x.gene_id_on_right for x in self.gene_ids_right],
            'gene_ids_left': [x.gene_id_on_left for x in self.gene_ids_left],
            'gene_ids_overlapping': [x.overlapping_gene_id for x in self.gene_ids_overlapping]
        })
        return rdict


class NcbiGeneInfoDescription(Base):
    """Class definition for the ncbi_gene_info_description table."""

    __tablename__ = 'ncbi_gene_info_description'
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text)


class NcbiGeneOnRight(Base):
    """Class definition for the ncbi_gene_on_right table."""

    __tablename__ = 'ncbi_gene_on_right'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    gene_id_on_right = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))

    gene = relationship("NcbiGeneInfo", foreign_keys=[gene_id])


class NcbiGeneOnLeft(Base):
    """Class definition for the ncbi_gene_on_left table."""

    __tablename__ = 'ncbi_gene_on_left'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    gene_id_on_left = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))

    gene = relationship("NcbiGeneInfo", foreign_keys=[gene_id])


class NcbiGeneOverlapping(Base):
    """Class definition for the ncbi_gene_overlapping table."""

    __tablename__ = 'ncbi_gene_overlapping'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gene_id = gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    overlapping_gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))

    gene = relationship("NcbiGeneInfo", foreign_keys=[gene_id])


class NcbiGeneOrtholog(Base):
    """Class definition for the ncbi_gene_ortholog table."""

    __tablename__ = 'ncbi_gene_ortholog'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tax_id = Column(Integer, index=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    other_tax_id = Column(Integer, index=True)
    other_gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))

    gene = relationship("NcbiGeneInfo", foreign_keys=[gene_id])


class NcbiGenePubmed(Base):
    """Class definition for the ncbi_gene_pubmed table."""

    __tablename__ = 'ncbi_gene_pubmed'
    id = Column(Integer, primary_key=True)

    tax_id = Column(Integer, index=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    pub_med_id = Column(Integer)


class NcbiGeneInfoXref(Base):
    """Class definition for the ncbi_gene_info_xref table."""

    __tablename__ = "ncbi_gene_info_xref"
    id = Column(Integer, primary_key=True, autoincrement=True)

    db = Column(String(100), index=True)
    dbid = Column(String(100), index=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))

    gene = relationship("NcbiGeneInfo", back_populates="xrefs")


class NcbiGeneMim(Base):
    """Class definition for the ncbi_gene_mim table."""

    __tablename__ = 'ncbi_gene_mim'
    id = Column(Integer, primary_key=True, autoincrement=True)

    mim_number = Column(Integer)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    type = Column(String(100))
    source = Column(String(100))
    med_gen_cui = Column(String(100), index=True)
    comment = Column(String(100))

    gene = relationship("NcbiGeneInfo", back_populates="mims")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "mim_number": self.mim_number,
            "gene_id": self.gene_id,
            "type": self.type,
            "source": self.source,
            "med_gen_cui": self.med_gen_cui,
            "comment": self.comment
        }


class NcbiGeneEnsembl(Base):
    """Class definition for the ncbi_gene_ensembl table."""

    __tablename__ = 'ncbi_gene_ensembl'
    id = Column(Integer, primary_key=True, autoincrement=True)

    tax_id = Column(Integer, index=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    ensembl_gene_identifier = Column(String(100))
    rna_nucleotide_accession_version = Column(String(100))
    ensembl_rna_identifier = Column(String(100))
    protein_accession_version = Column(String(100))
    ensembl_protein_identifier = Column(String(100))

    genes = relationship("NcbiGeneInfo", back_populates="ensembl_ids")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "tax_id": self.tax_id,
            "gene_id": self.gene_id,
            "ensembl_gene_identifier": self.ensembl_gene_identifier,
            "rna_nucleotide_accession_version": self.rna_nucleotide_accession_version,
            "ensembl_rna_identifier": self.ensembl_rna_identifier,
            "protein_accession_version": self.protein_accession_version,
            "ensembl_protein_identifier": self.ensembl_protein_identifier
        }


class NcbiGeneGo(Base):
    """Class definition for the ncbi_gene_go table."""

    __tablename__ = 'ncbi_gene_go'
    id = Column(Integer, primary_key=True, autoincrement=True)

    tax_id = Column(Integer, index=True)
    gene_id = Column(Integer, ForeignKey('ncbi_gene_info.gene_id'))
    go_id = Column(String(100), index=True)
    evidence = Column(String(10))
    qualifier = Column(String(100))
    go_term = Column(String(255))
    category = Column(String(10))

    pmids = relationship("NcbiGeneGoPmid", back_populates="gos")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'tax_id': self.tax_id,
            'gene_id': self.gene_id,
            'go_id': self.go_id,
            'evidence': self.evidence,
            'qualifier': self.qualifier,
            'go_term': self.go_term,
            'pmids': [x.pmid for x in self.pmids],
            'category': self.category
        }


class NcbiGeneGoPmid(Base):
    """Class definition for the ncbi_gene_go_pmid table."""

    __tablename__ = 'ncbi_gene_go_pmid'
    id = Column(Integer, primary_key=True, autoincrement=True)

    ncbi_gene_go_id = Column(Integer, ForeignKey('ncbi_gene_go.id'))
    pmid = Column(Integer)

    gos = relationship("NcbiGeneGo", back_populates="pmids")


class NcbiMedGenName(Base):
    """Class definition for the ncbi_medgen_name table."""

    __tablename__ = 'ncbi_medgen_name'
    id = Column(Integer, primary_key=True, autoincrement=True)

    cui = Column(String(100))
    name = Column(Text)
    source = Column(String(100))
    suppress = Column(String(1))
    pmids = relationship("NcbiMedGenPmid", back_populates="med_gen_name")

    def as_dict(self):
        """Convert object values to dictionary."""
        rdit = object_as_dict(self, exclude=['id'])
        rdit.update({'pmids': [x.pmid for x in self.pmids]})
        return rdit


class NcbiMedGenPmid(Base):
    """Class definition for the ncbi_medgen_pmid table."""

    __tablename__ = 'ncbi_medgen_pmid'
    id = Column(Integer, primary_key=True, autoincrement=True)

    ncbi_medgen_name_id = Column(Integer, ForeignKey('ncbi_medgen_name.id'))
    pmid = Column(Integer, index=True)

    med_gen_name = relationship("NcbiMedGenName", back_populates="pmids")

    def as_dict(self):
        """Convert object values to dictionary."""
        rdit = object_as_dict(self, exclude=['id'])
        return rdit
