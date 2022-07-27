"""HGNC RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, Text, ForeignKey, Date

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Hgnc(Base):
    """Class definition for the hgnc table."""

    __tablename__ = 'hgnc'
    id = Column(Integer, primary_key=True)
    hgnc_id = Column(String(20))
    version = Column(BigInteger)
    bioparadigms_slc = Column(String(20))
    cd = Column(String(20))
    cosmic = Column(String(50))
    date_approved_reserved = Column(Date)
    date_modified = Column(Date)
    date_name_changed = Column(Date)
    date_symbol_changed = Column(Date)
    ensembl_gene_id = Column(String(20))
    entrez_id = Column(Integer)
    homeodb = Column(Integer)
    horde_id = Column(String(50))
    imgt = Column(String(50))
    intermediate_filament_db = Column(String(50))
    iuphar = Column(String(50))
    kznf_gene_catalog = Column(Integer)
    lncipedia = Column(String(50))
    lncrnadb = Column(String(50))
    location = Column(String(100))
    location_sortable = Column(String(100))
    locus_group = Column(String(50))
    locus_type = Column(String(50))
    mamit_trnadb = Column(Integer)
    merops = Column(String(20))
    mirbase = Column(String(20))
    name = Column(String(255))
    orphanet = Column(Integer)
    pseudogene_org = Column(String(50))
    snornabase = Column(String(20))
    status = Column(String(50))
    symbol = Column(String(100), index=True)
    ucsc_id = Column(String(50))
    uuid = Column(String(50))
    vega_id = Column(String(50))
    agr = Column(String(50))
    kznf_gene_catalog = Column(Text)

    pre_symbols = relationship("PrevSymbol", back_populates="hgnc")
    alias_names = relationship("AliasName", back_populates="hgnc")
    alias_symbols = relationship("AliasSymbol", back_populates="hgnc")
    ccdss = relationship("Ccds", back_populates="hgnc")
    enas = relationship("Ena", back_populates="hgnc")
    enzymes = relationship("Enzyme", back_populates="hgnc")
    gene_group_names = relationship("GeneGroupName", back_populates="hgnc")
    gene_group_ids = relationship("GeneGroupId", back_populates="hgnc")
    uniprots = relationship("UniProt", back_populates="hgnc")
    rna_centrals = relationship("RnaCentral", back_populates="hgnc")
    rgds = relationship("Rgd", back_populates="hgnc")
    refseqs = relationship("RefSeq", back_populates="hgnc")
    pubmeds = relationship("PubMed", back_populates="hgnc")
    prev_names = relationship("PrevName", back_populates="hgnc")
    omims = relationship("Omim", back_populates="hgnc")
    mgds = relationship("Mgd", back_populates="hgnc")
    lsdbs = relationship("Lsdb", back_populates="hgnc")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'hgnc_id': self.hgnc_id,
            'version': self.version,
            'bioparadigms_slc': self.bioparadigms_slc,
            'cd': self.cd,
            'cosmic': self.cosmic,
            'date_approved_reserved': self.date_approved_reserved,
            'date_modified': self.date_modified,
            'date_name_changed': self.date_name_changed,
            'date_symbol_changed': self.date_symbol_changed,
            'ensembl_gene_id': self.ensembl_gene_id,
            'entrez_id': self.entrez_id,
            'homeodb': self.homeodb,
            'horde_id': self.horde_id,
            'imgt': self.imgt,
            'intermediate_filament_db': self.intermediate_filament_db,
            'iuphar': self.iuphar,
            'kznf_gene_catalog': self.kznf_gene_catalog,
            'lncipedia': self.lncipedia,
            'lncrnadb': self.lncrnadb,
            'location': self.location,
            'location_sortable': self.location_sortable,
            'locus_group': self.locus_group,
            'locus_type': self.locus_type,
            'mamit_trnadb': self.mamit_trnadb,
            'merops': self.merops,
            'mirbase': self.mirbase,
            'name': self.name,
            'orphanet': self.orphanet,
            'pseudogene_org': self.pseudogene_org,
            'snornabase': self.snornabase,
            'status': self.status,
            'symbol': self.symbol,
            'ucsc_id': self.ucsc_id,
            'uuid': self.uuid,
            'vega_id': self.vega_id,
            'agr': self.agr,
            'pre_symbols': [x.prev_symbol for x in self.pre_symbols],
            'alias_names': [x.alias_name for x in self.alias_names],
            'alias_symbols': [x.alias_symbol for x in self.alias_symbols],
            'ccdss': [x.identifier for x in self.ccdss],
            'enas': [x.identifier for x in self.enas],
            'enzymes': [x.ec_number for x in self.enzymes],
            'gene_group_names': [x.name for x in self.gene_group_names],
            'gene_group_ids': [x.identifier for x in self.gene_group_ids],
            'uniprots': [x.accession for x in self.uniprots],
            'rna_centrals': [x.identifier for x in self.rna_centrals],
            'rgds': [x.identifier for x in self.rgds],
            'refseqs': [x.accession for x in self.refseqs],
            'pubmeds': [x.pmid for x in self.pubmeds],
            'prev_names': [x.prev_name for x in self.prev_names],
            'omims': [x.identifier for x in self.omims],
            'mgds': [x.identifier for x in self.mgds],
            'lsdbs': [x.identifier for x in self.lsdbs]
        }


class PrevSymbol(Base):
    """Class definition for the hgnc_prev_symbol table."""

    __tablename__ = 'hgnc_prev_symbol'
    id = Column(Integer, primary_key=True)

    prev_symbol = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="pre_symbols")

    def __str__(self):
        return self.prev_symbol


class AliasName(Base):
    """Class definition for the hgnc_alias_name table."""

    __tablename__ = 'hgnc_alias_name'
    id = Column(Integer, primary_key=True)

    alias_name = Column(String(255))

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="alias_names")

    def __str__(self):
        return self.alias_name


class AliasSymbol(Base):
    """Class definition for the hgnc_alias_symbol table."""

    __tablename__ = 'hgnc_alias_symbol'
    id = Column(Integer, primary_key=True)

    alias_symbol = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="alias_symbols")

    def __str__(self):
        return self.alias_symbol


class Ccds(Base):
    """Class definition for the hgnc_ccds table."""

    __tablename__ = 'hgnc_ccds'
    id = Column(Integer, primary_key=True)

    identifier = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="ccdss")

    def __str__(self):
        return self.identifier


class Ena(Base):
    """Class definition for the hgnc_ena table."""

    __tablename__ = 'hgnc_ena'
    id = Column(Integer, primary_key=True)

    identifier = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="enas")

    def __str__(self):
        return self.identifier


class Enzyme(Base):
    """Class definition for the hgnc_enzyme table."""

    __tablename__ = 'hgnc_enzyme'
    id = Column(Integer, primary_key=True)

    ec_number = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="enzymes")

    def __str__(self):
        return self.ec_number


class GeneGroupName(Base):
    """Class definition for the hgnc_gene_group_name table."""

    __tablename__ = 'hgnc_gene_group_name'
    id = Column(Integer, primary_key=True)

    name = Column(String(255))

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="gene_group_names")

    def __str__(self):
        return self.name

    def as_dict(self):
        """Return obj as dict."""
        return object_as_dict(self)


class GeneGroupId(Base):
    """Class definition for the hgnc_gene_group_id table."""

    __tablename__ = 'hgnc_gene_group_id'
    id = Column(Integer, primary_key=True)

    identifier = Column(Integer)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="gene_group_ids")

    def __str__(self):
        return self.identifier


class UniProt(Base):
    """Class definition for the hgnc_uniprot table."""

    __tablename__ = 'hgnc_uniprot'
    id = Column(Integer, primary_key=True)

    accession = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="uniprots")

    def __str__(self):
        return self.accession


class RnaCentral(Base):
    """Class definition for the hgnc_rna_central table."""

    __tablename__ = 'hgnc_rna_central'
    id = Column(Integer, primary_key=True)

    identifier = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="rna_centrals")

    def __str__(self):
        return self.identifier


class Rgd(Base):
    """Class definition for the hgnc_rgd table."""

    __tablename__ = 'hgnc_rgd'
    id = Column(Integer, primary_key=True)

    identifier = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="rgds")

    def __str__(self):
        return self.identifier


class RefSeq(Base):
    """Class definition for the hgnc_refseq table."""

    __tablename__ = 'hgnc_refseq'
    id = Column(Integer, primary_key=True)

    accession = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="refseqs")

    def __str__(self):
        return self.accession


class PubMed(Base):
    """Class definition for the hgnc_pubmed table."""

    __tablename__ = 'hgnc_pubmed'
    id = Column(Integer, primary_key=True)

    pmid = Column(Integer, index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="pubmeds")

    def __str__(self):
        return self.pmid


class PrevName(Base):
    """Class definition for the hgnc_prev_name table."""

    __tablename__ = 'hgnc_prev_name'
    id = Column(Integer, primary_key=True)

    prev_name = Column(String(255))

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="prev_names")

    def __str__(self):
        return self.prev_name


class Omim(Base):
    """Class definition for the hgnc_omim table."""

    __tablename__ = 'hgnc_omim'
    id = Column(Integer, primary_key=True)

    identifier = Column(Integer, index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="omims")

    def __str__(self):
        return self.identifier


class Mgd(Base):
    """Class definition for the hgnc_mgd table."""

    __tablename__ = 'hgnc_mgd'
    id = Column(Integer, primary_key=True)

    identifier = Column(String(50), index=True)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="mgds")

    def __str__(self):
        return self.identifier


class Lsdb(Base):
    """Class definition for the hgnc_lsdb table."""

    __tablename__ = 'hgnc_lsdb'
    id = Column(Integer, primary_key=True)

    identifier = Column(Text)

    hgnc_id = Column(Integer, ForeignKey('hgnc.id'))
    hgnc = relationship("Hgnc", back_populates="lsdbs")

    def __str__(self):
        return self.identifier
