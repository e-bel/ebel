"""HGNC RDBMS model definition."""
import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Hgnc(Base):
    """Class definition for the hgnc table."""

    __tablename__ = "hgnc"

    id: Mapped[int] = mapped_column(primary_key=True)
    hgnc_id: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(BigInteger)
    bioparadigms_slc: Mapped[Optional[str]] = mapped_column(String(20))
    cd: Mapped[Optional[str]] = mapped_column(String(20))
    cosmic: Mapped[Optional[str]] = mapped_column(String(50))
    date_approved_reserved: Mapped[datetime.date] = mapped_column(Date)
    date_modified: Mapped[Optional[datetime.date]] = mapped_column(Date)
    date_name_changed: Mapped[Optional[datetime.date]] = mapped_column(Date)
    date_symbol_changed: Mapped[Optional[datetime.date]] = mapped_column(Date)
    ensembl_gene_id: Mapped[Optional[str]] = mapped_column(String(20))
    entrez_id: Mapped[Optional[int]] = mapped_column()
    homeodb: Mapped[Optional[int]] = mapped_column()
    horde_id: Mapped[Optional[str]] = mapped_column(String(50))
    imgt: Mapped[Optional[str]] = mapped_column(String(50))
    iuphar: Mapped[Optional[str]] = mapped_column(String(50))
    kznf_gene_catalog: Mapped[int] = mapped_column()
    lncipedia: Mapped[Optional[str]] = mapped_column(String(50))
    lncrnadb: Mapped[Optional[str]] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(100))
    location_sortable: Mapped[Optional[str]] = mapped_column(String(100))
    locus_group: Mapped[str] = mapped_column(String(50))
    locus_type: Mapped[str] = mapped_column(String(50))
    merops: Mapped[Optional[str]] = mapped_column(String(20))
    mirbase: Mapped[Optional[str]] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255))
    orphanet: Mapped[Optional[int]] = mapped_column()
    snornabase: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(50))
    symbol: Mapped[str] = mapped_column(String(100), index=True)
    ucsc_id: Mapped[Optional[str]] = mapped_column(String(50))
    uuid: Mapped[str] = mapped_column(String(50))
    vega_id: Mapped[Optional[str]] = mapped_column(String(50))
    agr: Mapped[Optional[str]] = mapped_column(String(50))
    kznf_gene_catalog: Mapped[Optional[str]] = mapped_column(Text)

    pre_symbols: Mapped[List["PrevSymbol"]] = relationship("PrevSymbol", back_populates="hgnc")
    alias_names: Mapped[List["AliasName"]] = relationship("AliasName", back_populates="hgnc")
    alias_symbols: Mapped[List["AliasSymbol"]] = relationship("AliasSymbol", back_populates="hgnc")
    ccdss: Mapped[List["Ccds"]] = relationship("Ccds", back_populates="hgnc")
    enas: Mapped[List["Ena"]] = relationship("Ena", back_populates="hgnc")
    enzymes: Mapped[List["Enzyme"]] = relationship("Enzyme", back_populates="hgnc")
    gene_group_names: Mapped[List["GeneGroupName"]] = relationship("GeneGroupName", back_populates="hgnc")
    gene_group_ids: Mapped[List["GeneGroupId"]] = relationship("GeneGroupId", back_populates="hgnc")
    uniprots: Mapped[List["UniProt"]] = relationship("UniProt", back_populates="hgnc")
    rna_centrals: Mapped[List["RnaCentral"]] = relationship("RnaCentral", back_populates="hgnc")
    rgds: Mapped[List["Rgd"]] = relationship("Rgd", back_populates="hgnc")
    refseqs: Mapped[List["RefSeq"]] = relationship("RefSeq", back_populates="hgnc")
    pubmeds: Mapped[List["PubMed"]] = relationship("PubMed", back_populates="hgnc")
    prev_names: Mapped[List["PrevName"]] = relationship("PrevName", back_populates="hgnc")
    omims: Mapped[List["Omim"]] = relationship("Omim", back_populates="hgnc")
    mgds: Mapped[List["Mgd"]] = relationship("Mgd", back_populates="hgnc")
    lsdbs: Mapped[List["Lsdb"]] = relationship("Lsdb", back_populates="hgnc")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "hgnc_id": self.hgnc_id,
            "version": self.version,
            "bioparadigms_slc": self.bioparadigms_slc,
            "cd": self.cd,
            "cosmic": self.cosmic,
            "date_approved_reserved": self.date_approved_reserved,
            "date_modified": self.date_modified,
            "date_name_changed": self.date_name_changed,
            "date_symbol_changed": self.date_symbol_changed,
            "ensembl_gene_id": self.ensembl_gene_id,
            "entrez_id": self.entrez_id,
            "homeodb": self.homeodb,
            "horde_id": self.horde_id,
            "imgt": self.imgt,
            "iuphar": self.iuphar,
            "kznf_gene_catalog": self.kznf_gene_catalog,
            "lncipedia": self.lncipedia,
            "lncrnadb": self.lncrnadb,
            "location": self.location,
            "location_sortable": self.location_sortable,
            "locus_group": self.locus_group,
            "locus_type": self.locus_type,
            "merops": self.merops,
            "mirbase": self.mirbase,
            "name": self.name,
            "orphanet": self.orphanet,
            "snornabase": self.snornabase,
            "status": self.status,
            "symbol": self.symbol,
            "ucsc_id": self.ucsc_id,
            "uuid": self.uuid,
            "vega_id": self.vega_id,
            "agr": self.agr,
            "pre_symbols": [x.prev_symbol for x in self.pre_symbols],
            "alias_names": [x.alias_name for x in self.alias_names],
            "alias_symbols": [x.alias_symbol for x in self.alias_symbols],
            "ccdss": [x.identifier for x in self.ccdss],
            "enas": [x.identifier for x in self.enas],
            "enzymes": [x.ec_number for x in self.enzymes],
            "gene_group_names": [x.name for x in self.gene_group_names],
            "gene_group_ids": [x.identifier for x in self.gene_group_ids],
            "uniprots": [x.accession for x in self.uniprots],
            "rna_centrals": [x.identifier for x in self.rna_centrals],
            "rgds": [x.identifier for x in self.rgds],
            "refseqs": [x.accession for x in self.refseqs],
            "pubmeds": [x.pmid for x in self.pubmeds],
            "prev_names": [x.prev_name for x in self.prev_names],
            "omims": [x.identifier for x in self.omims],
            "mgds": [x.identifier for x in self.mgds],
            "lsdbs": [x.identifier for x in self.lsdbs],
        }


class PrevSymbol(Base):
    """Class definition for the hgnc_prev_symbol table."""

    __tablename__ = "hgnc_prev_symbol"
    id: Mapped[int] = mapped_column(primary_key=True)

    prev_symbol: Mapped[str] = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc: Mapped[Hgnc] = relationship("Hgnc", back_populates="pre_symbols")

    def __str__(self):
        return self.prev_symbol


class AliasName(Base):
    """Class definition for the hgnc_alias_name table."""

    __tablename__ = "hgnc_alias_name"
    id: Mapped[int] = mapped_column(primary_key=True)

    alias_name: Mapped[str] = mapped_column(String(255))

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc: Mapped[Hgnc] = relationship("Hgnc", back_populates="alias_names")

    def __str__(self):
        return self.alias_name


class AliasSymbol(Base):
    """Class definition for the hgnc_alias_symbol table."""

    __tablename__ = "hgnc_alias_symbol"
    id: Mapped[int] = mapped_column(primary_key=True)

    alias_symbol: Mapped[str] = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc: Mapped[Hgnc] = relationship("Hgnc", back_populates="alias_symbols")

    def __str__(self):
        return self.alias_symbol


class Ccds(Base):
    """Class definition for the hgnc_ccds table."""

    __tablename__ = "hgnc_ccds"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier: Mapped[str] = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc: Mapped[Hgnc] = relationship("Hgnc", back_populates="ccdss")

    def __str__(self):
        return self.identifier


class Ena(Base):
    """Class definition for the hgnc_ena table."""

    __tablename__ = "hgnc_ena"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier: Mapped[str] = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc: Mapped[Hgnc] = relationship("Hgnc", back_populates="enas")

    def __str__(self):
        return self.identifier


class Enzyme(Base):
    """Class definition for the hgnc_enzyme table."""

    __tablename__ = "hgnc_enzyme"
    id: Mapped[int] = mapped_column(primary_key=True)

    ec_number = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="enzymes")

    def __str__(self):
        return self.ec_number


class GeneGroupName(Base):
    """Class definition for the hgnc_gene_group_name table."""

    __tablename__ = "hgnc_gene_group_name"
    id: Mapped[int] = mapped_column(primary_key=True)

    name = mapped_column(String(255))

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="gene_group_names")

    def __str__(self):
        return self.name

    def as_dict(self):
        """Return obj as dict."""
        return object_as_dict(self)


class GeneGroupId(Base):
    """Class definition for the hgnc_gene_group_id table."""

    __tablename__ = "hgnc_gene_group_id"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier = mapped_column(Integer)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="gene_group_ids")

    def __str__(self):
        return self.identifier


class UniProt(Base):
    """Class definition for the hgnc_uniprot table."""

    __tablename__ = "hgnc_uniprot"
    id: Mapped[int] = mapped_column(primary_key=True)

    accession = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="uniprots")

    def __str__(self):
        return self.accession


class RnaCentral(Base):
    """Class definition for the hgnc_rna_central table."""

    __tablename__ = "hgnc_rna_central"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="rna_centrals")

    def __str__(self):
        return self.identifier


class Rgd(Base):
    """Class definition for the hgnc_rgd table."""

    __tablename__ = "hgnc_rgd"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="rgds")

    def __str__(self):
        return self.identifier


class RefSeq(Base):
    """Class definition for the hgnc_refseq table."""

    __tablename__ = "hgnc_refseq"
    id: Mapped[int] = mapped_column(primary_key=True)

    accession = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="refseqs")

    def __str__(self):
        return self.accession


class PubMed(Base):
    """Class definition for the hgnc_pubmed table."""

    __tablename__ = "hgnc_pubmed"
    id: Mapped[int] = mapped_column(primary_key=True)

    pmid = mapped_column(Integer, index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="pubmeds")

    def __str__(self):
        return self.pmid


class PrevName(Base):
    """Class definition for the hgnc_prev_name table."""

    __tablename__ = "hgnc_prev_name"
    id: Mapped[int] = mapped_column(primary_key=True)

    prev_name = mapped_column(String(255))

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="prev_names")

    def __str__(self):
        return self.prev_name


class Omim(Base):
    """Class definition for the hgnc_omim table."""

    __tablename__ = "hgnc_omim"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier = mapped_column(Integer, index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="omims")

    def __str__(self):
        return self.identifier


class Mgd(Base):
    """Class definition for the hgnc_mgd table."""

    __tablename__ = "hgnc_mgd"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier = mapped_column(String(50), index=True)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="mgds")

    def __str__(self):
        return self.identifier


class Lsdb(Base):
    """Class definition for the hgnc_lsdb table."""

    __tablename__ = "hgnc_lsdb"
    id: Mapped[int] = mapped_column(primary_key=True)

    identifier: Mapped[str] = mapped_column(Text)

    hgnc_id: Mapped[int] = mapped_column(ForeignKey("hgnc.id"))
    hgnc = relationship("Hgnc", back_populates="lsdbs")

    def __str__(self):
        return self.identifier
