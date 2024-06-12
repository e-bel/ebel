"""BioGRID RDBMS model definition."""
from sqlalchemy import Float, ForeignKey, Integer, String, Text, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, aliased, mapped_column, relationship
from sqlalchemy_utils import create_view

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Biogrid(Base):
    """Class definition for the biogrid table."""

    __tablename__ = "biogrid"
    id = mapped_column(Integer, primary_key=True)

    biogrid_a_id: Mapped[int] = mapped_column(ForeignKey("biogrid_interactor.biogrid_id"))
    biogrid_a: Mapped["Interactor"] = relationship("Interactor", foreign_keys=[biogrid_a_id])
    biogrid_b_id: Mapped[int] = mapped_column(ForeignKey("biogrid_interactor.biogrid_id"))
    biogrid_b: Mapped["Interactor"] = relationship("Interactor", foreign_keys=[biogrid_b_id])
    biogrid_id: Mapped[int] = mapped_column(nullable=True)
    experimental_system_id: Mapped[int] = mapped_column(ForeignKey("biogrid_experimental_system.id"))
    experimental_system: Mapped["ExperimentalSystem"] = relationship(
        "ExperimentalSystem", foreign_keys=[experimental_system_id]
    )
    throughput_id: Mapped[int] = mapped_column(ForeignKey("biogrid_throughput.id"))
    throughput: Mapped["Throughput"] = relationship("Throughput", foreign_keys=[throughput_id])
    score: Mapped[float] = mapped_column(nullable=True)
    modification_id: Mapped[int] = mapped_column(ForeignKey("biogrid_modification.id"), nullable=True)
    modification: Mapped["Modification"] = relationship("Modification", foreign_keys=[modification_id])
    qualifications: Mapped[str] = mapped_column(String(255), nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("biogrid_source.id"))
    source: Mapped["Source"] = relationship("Source", foreign_keys=[source_id])
    publication_id: Mapped[int] = mapped_column(ForeignKey("biogrid_publication.id"))
    publication: Mapped["Publication"] = relationship("Publication", foreign_keys=[publication_id])
    qualification: Mapped[str] = mapped_column(Text, nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "biogrid_a": self.biogrid_a.as_dict(),
            "biogrid_b": self.biogrid_b.as_dict(),
            "experimental_system": self.experimental_system.as_dict() if self.experimental_system else None,
            "throughput": self.throughput.as_dict() if self.throughput else None,
            "biogrid_id": self.biogrid_id,
            "score": self.score if self.score else None,
            "modification": self.modification.as_dict() if self.modification else None,
            "source": self.source.source,
            "publication": self.publication.as_dict(),
            "qualification": self.qualification if self.qualification else None,
        }


class Publication(Base):
    """Class definition for the biogrid_publication table."""

    __tablename__ = "biogrid_publication"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[int] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=True)
    source_identifier: Mapped[str] = mapped_column(String(255), nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class Throughput(Base):
    """Class definition for the biogrid_throughput table."""

    __tablename__ = "biogrid_throughput"
    id: Mapped[int] = mapped_column(primary_key=True)
    throughput: Mapped[str] = mapped_column(String(255))
    count: Mapped[int] = mapped_column()

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class Taxonomy(Base):
    """Class definition for the biogrid_taxonomy table."""

    __tablename__ = "biogrid_taxonomy"
    taxonomy_id: Mapped[int] = mapped_column(primary_key=True)  # == NCBI Taxonomy ID
    organism_name: Mapped[str] = mapped_column(String(1000))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"taxonomy_id": self.taxonomy_id, "organism_name": self.organism_name}


class ExperimentalSystem(Base):
    """Class definition for the biogrid_experimental_system table."""

    __tablename__ = "biogrid_experimental_system"
    id: Mapped[int] = mapped_column(primary_key=True)
    experimental_system: Mapped[str] = mapped_column(String(255), nullable=True)
    experimental_system_type: Mapped[str] = mapped_column(String(255), nullable=True)
    count: Mapped[int] = mapped_column()

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class Interactor(Base):
    """Class definition for the biogrid_interactor table."""

    __tablename__ = "biogrid_interactor"
    biogrid_id: Mapped[int] = mapped_column(primary_key=True)

    entrez: Mapped[int] = mapped_column(nullable=True, index=True)
    systematic_name: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    taxonomy_id: Mapped[int] = mapped_column(ForeignKey("biogrid_taxonomy.taxonomy_id"))
    taxonomy: Mapped["Taxonomy"] = relationship("Taxonomy", foreign_keys=[taxonomy_id])
    uniprot: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    trembl: Mapped[str] = mapped_column(String(1000), nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "entrez": self.entrez,
            "systematic_name": self.systematic_name,
            "symbol": self.symbol,
            "uniprot": self.uniprot,
            "trembl": self.trembl,
            "taxonomy": self.taxonomy.as_dict(),
        }


class Source(Base):
    """Class definition for the biogrid_source table."""

    __tablename__ = "biogrid_source"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(255), nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class Modification(Base):
    """Class definition for the biogrid_modification table."""

    __tablename__ = "biogrid_modification"
    id: Mapped[int] = mapped_column(primary_key=True)
    modification: Mapped[str] = mapped_column(String(255), nullable=True)
    count: Mapped[int] = mapped_column()

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class BiogridView(Base):
    """SQL view for Biogrid."""

    b = Biogrid
    ia = aliased(Interactor)
    ib = aliased(Interactor)
    m = Modification
    p = Publication
    es = ExperimentalSystem
    ta = aliased(Taxonomy)
    tb = aliased(Taxonomy)
    s = Source

    stmt = (
        select(
            b.biogrid_id,
            ia.symbol.label("symbol_a"),
            ia.uniprot.label("uniprot_a"),
            ta.taxonomy_id.label("tax_id_a"),
            ta.organism_name.label("organism_a"),
            ib.symbol.label("symbol_b"),
            ib.uniprot.label("uniprot_b"),
            tb.taxonomy_id.label("tax_id_b"),
            tb.organism_name.label("organism_b"),
            es.experimental_system,
            m.modification,
            s.source,
            b.qualification,
            p.source.label("publication_source"),
            p.source_identifier.label("publication_identifier"),
        )
        .join(ia, b.biogrid_a_id == ia.biogrid_id)
        .join(ib, b.biogrid_b_id == ib.biogrid_id)
        .join(ta, ia.taxonomy_id == ta.taxonomy_id)
        .join(tb, ib.taxonomy_id == tb.taxonomy_id)
        .join(es, b.experimental_system_id == es.id, isouter=True)
        .join(m, m.id == b.modification_id, isouter=True)
        .join(s, b.source_id == s.id, isouter=True)
        .join(p, b.publication_id == p.id, isouter=True)
    )

    view = create_view(name="biogrid_view", selectable=stmt, metadata=Base.metadata)

    __table__ = view
