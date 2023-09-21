"""Pathway Commons RDBMS model definition."""
from typing import List, Optional

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()

pathway_commons__pathway_name = Table(
    "pathway_commons__pathway_name",
    Base.metadata,
    Column("pathway_commons_id", Integer, ForeignKey("pathway_commons.id"), index=True),
    Column(
        "pathway_commons_pathway_name_id",
        Integer,
        ForeignKey("pathway_commons_pathway_name.id"),
        index=True,
    ),
)

pathway_commons__source = Table(
    "pathway_commons__source",
    Base.metadata,
    Column("pathway_commons_id", Integer, ForeignKey("pathway_commons.id"), index=True),
    Column(
        "pathway_commons_source_id",
        Integer,
        ForeignKey("pathway_commons_source.id"),
        index=True,
    ),
)


class PathwayCommons(Base):
    """Class definition for the pathway_commons table."""

    __tablename__ = "pathway_commons"
    id: Mapped[int] = mapped_column(primary_key=True)

    participant_a: Mapped[str] = mapped_column(String(50), index=True)
    interaction_type: Mapped[str] = mapped_column(String(50), index=True)
    participant_b: Mapped[str] = mapped_column(String(50), index=True)

    pmids: Mapped[List["Pmid"]] = relationship("Pmid", back_populates="pathway_commons")

    pathway_names: Mapped[List["PathwayName"]] = relationship(
        "PathwayName",
        secondary=pathway_commons__pathway_name,
        back_populates="pathway_commonses",
    )

    sources: Mapped[List["Source"]] = relationship(
        "Source", secondary=pathway_commons__source, back_populates="pathway_commonses"
    )

    def __str__(self):
        return f"{self.participant_a} {self.interaction_type} {self.participant_b}"

    def as_dict(self):
        """Convert object values to dictionary."""
        pathway_commons = object_as_dict(self)
        pathway_commons.update({"pmids": [x.pmid for x in self.pmids]})
        pathway_commons.update({"pathway_names": [x.name for x in self.pathway_names]})
        pathway_commons.update({"sources": [x.source for x in self.sources]})
        return pathway_commons


class PathwayName(Base):
    """Class definition for the pathway_commons_pathway_name table."""

    __tablename__ = "pathway_commons_pathway_name"
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), index=True)

    pathway_commonses: Mapped[List[PathwayCommons]] = relationship(
        "PathwayCommons",
        secondary=pathway_commons__pathway_name,
        back_populates="pathway_names",
    )

    def __str__(self):
        """Class string definition."""
        return self.name


class Pmid(Base):
    """Class definition for the pathway_commons_pmid table."""

    __tablename__ = "pathway_commons_pmid"
    id: Mapped[int] = mapped_column(primary_key=True)

    pmid: Mapped[int] = mapped_column(index=True)

    pathway_commons_id: Mapped[int] = mapped_column(ForeignKey("pathway_commons.id"), index=True)
    pathway_commons: Mapped[List[PathwayCommons]] = relationship("PathwayCommons", back_populates="pmids")

    def __str__(self):
        """Class string definition."""
        return str(self.pmid)


class Source(Base):
    """Class definition for the pathway_commons_source table."""

    __tablename__ = "pathway_commons_source"
    id: Mapped[int] = mapped_column(primary_key=True)

    source: Mapped[str] = mapped_column(String(50))

    pathway_commonses: Mapped[List[PathwayCommons]] = relationship(
        "PathwayCommons", secondary=pathway_commons__source, back_populates="sources"
    )

    def __str__(self):
        """Class string definition."""
        return self.source
