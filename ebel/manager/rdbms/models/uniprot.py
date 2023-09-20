"""UniProt RDBMS model definition."""
from collections import defaultdict
from typing import List

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column, Mapped

Base = declarative_base()

uniprot__uniprot_keyword = Table(
    "uniprot__uniprot_keyword",
    Base.metadata,
    Column("uniprot_id", Integer, ForeignKey("uniprot.id")),
    Column("uniprot_keyword_id", Integer, ForeignKey("uniprot_keyword.keywordid")),
)

uniprot__uniprot_host = Table(
    "uniprot__uniprot_host",
    Base.metadata,
    Column("uniprot_id", Integer, ForeignKey("uniprot.id")),
    Column("uniprot_organism_id", Integer, ForeignKey("uniprot_organism.taxid")),
)

uniprot__uniprot_xref = Table(
    "uniprot__uniprot_xref",
    Base.metadata,
    Column("uniprot_id", Integer, ForeignKey("uniprot.id")),
    Column("uniprot_xref_id", Integer, ForeignKey("uniprot_xref.id")),
)

uniprot__uniprot_subcellular_location = Table(
    "uniprot__uniprot_subcellular_location",
    Base.metadata,
    Column("uniprot_id", Integer, ForeignKey("uniprot.id")),
    Column(
        "uniprot_subcellular_location_id",
        Integer,
        ForeignKey("uniprot_subcellular_location.id"),
    ),
)


class Uniprot(Base):
    """Class definition for the UniProt table."""

    __tablename__ = "uniprot"

    id: Mapped[int] = mapped_column(primary_key=True)

    accession: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    recommended_name: Mapped[str] = mapped_column(String(255), nullable=True)

    taxid: Mapped[int] = mapped_column(ForeignKey("uniprot_organism.taxid"), nullable=False, index=True)
    organism: Mapped["Organism"] = relationship("Organism")

    function_id: Mapped[int] = mapped_column(ForeignKey("uniprot_function.id"), nullable=True)
    function: Mapped["Function"] = relationship("Function")

    gene_names: Mapped[List["Gene"]] = relationship("Gene", back_populates="uniprot")

    gene_symbol: Mapped["GeneSymbol"] = relationship("GeneSymbol", uselist=False, back_populates="uniprot")

    keywords: Mapped[List["Keyword"]] = relationship(
        "Keyword", secondary=uniprot__uniprot_keyword, back_populates="uniprots"
    )

    hosts: Mapped[List["Organism"]] = relationship(
        "Organism", secondary=uniprot__uniprot_host, back_populates="uniprots"
    )

    xrefs: Mapped[List["Xref"]] = relationship("Xref", secondary=uniprot__uniprot_xref, back_populates="uniprots")

    subcellular_locations: Mapped[List["SubcellularLocation"]] = relationship(
        "SubcellularLocation",
        secondary=uniprot__uniprot_subcellular_location,
        back_populates="uniprots",
    )

    def __repr__(self):
        return self.name

    def as_dict(self):
        """Convert object values to dictionary."""
        xrefs_grouped = defaultdict(list)
        for xref in self.xrefs:
            xrefs_grouped[xref.db].append(xref.identifier)
        xrefs_grouped = {k: sorted(v) for k, v in xrefs_grouped.items()}

        return {
            "name": self.name,
            "accession": self.accession,
            "recommended_name": self.recommended_name,
            "taxid": self.taxid,
            "function_description": self.function.description if self.function else self.function,
            "gene_names": [x.name for x in self.gene_names],
            "gene_symbol": self.gene_symbol.symbol if self.gene_symbol else self.gene_symbol,
            "keywords": [{"keyword": x.keyword_name, "id": x.keywordid} for x in self.keywords],
            "hosts": [{"name": x.scientific_name, "taxid": x.taxid} for x in self.hosts],
            "xrefs": xrefs_grouped,
            "subcellular_locations": [x.name for x in self.subcellular_locations],
            "organism": self.organism.scientific_name,
        }


class GeneSymbol(Base):
    """Class definition for the uniprot_gene_symbol table."""

    __tablename__ = "uniprot_gene_symbol"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    uniprot_id: Mapped[int] = mapped_column(ForeignKey("uniprot.id"))
    uniprot: Mapped[Uniprot] = relationship("Uniprot", back_populates="gene_symbol")

    def __repr__(self):
        """Define repr."""
        return self.symbol


class Gene(Base):
    """Class definition for the uniprot_gene table."""

    __tablename__ = "uniprot_gene"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    uniprot_id: Mapped[int] = mapped_column(ForeignKey("uniprot.id"))
    uniprot: Mapped[Uniprot] = relationship("Uniprot", back_populates="gene_names")


class Keyword(Base):
    """Class definition for the uniprot_keyword table."""

    __tablename__ = "uniprot_keyword"

    keywordid: Mapped[int] = mapped_column(primary_key=True)
    keyword_name: Mapped[str] = mapped_column(String(100), index=True)

    uniprots: Mapped[List[Uniprot]] = relationship(
        "Uniprot", secondary=uniprot__uniprot_keyword, back_populates="keywords"
    )

    def __repr__(self):
        """Define repr."""
        return f"{self.keyword_name}[{self.keywordid}]"


class Organism(Base):
    """Class definition for the uniprot_organism table."""

    __tablename__ = "uniprot_organism"

    taxid: Mapped[int] = mapped_column(primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String(255))  # TODO:Check if index=True with  is possible

    uniprots: Mapped[List[Uniprot]] = relationship("Uniprot", secondary=uniprot__uniprot_host, back_populates="hosts")


class SubcellularLocation(Base):
    """Class definition for the uniprot_subcellular_location table."""

    __tablename__ = "uniprot_subcellular_location"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)

    uniprots: Mapped[List[Uniprot]] = relationship(
        "Uniprot",
        secondary=uniprot__uniprot_subcellular_location,
        back_populates="subcellular_locations",
    )


class Xref(Base):
    """Class definition for the uniprot_xref table."""

    __tablename__ = "uniprot_xref"

    id: Mapped[int] = mapped_column(primary_key=True)

    db: Mapped[str] = mapped_column(String(50), index=True)
    identifier: Mapped[str] = mapped_column(String(100), index=True)

    uniprots: Mapped[List[Uniprot]] = relationship("Uniprot", secondary=uniprot__uniprot_xref, back_populates="xrefs")


class Function(Base):
    """Class definition for the uniprot_function table."""

    __tablename__ = "uniprot_function"

    id: Mapped[int] = mapped_column(primary_key=True)

    description: Mapped[str] = mapped_column(Text)

    uniprots: Mapped[List[Uniprot]] = relationship("Uniprot", back_populates="function")
