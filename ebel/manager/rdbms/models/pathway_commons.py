"""Pathway Commons RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, Table, ForeignKey

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()

pathway_commons__pathway_name = Table('pathway_commons__pathway_name', Base.metadata,
                                      Column('pathway_commons_id', Integer, ForeignKey('pathway_commons.id'),
                                             index=True),
                                      Column('pathway_commons_pathway_name_id', Integer,
                                             ForeignKey('pathway_commons_pathway_name.id'), index=True)
                                      )

pathway_commons__source = Table('pathway_commons__source', Base.metadata,
                                Column('pathway_commons_id', Integer, ForeignKey('pathway_commons.id'), index=True),
                                Column('pathway_commons_source_id', Integer,
                                       ForeignKey('pathway_commons_source.id'), index=True)
                                )


class PathwayCommons(Base):
    """Class definition for the pathway_commons table."""

    __tablename__ = 'pathway_commons'
    id = Column(Integer, primary_key=True)

    participant_a = Column(String(50), index=True)
    interaction_type = Column(String(50), index=True)
    participant_b = Column(String(50), index=True)

    pmids = relationship("Pmid", back_populates="pathway_commons")

    pathway_names = relationship(
        "PathwayName",
        secondary=pathway_commons__pathway_name,
        back_populates="pathway_commonses"
    )

    sources = relationship(
        "Source",
        secondary=pathway_commons__source,
        back_populates="pathway_commonses"
    )

    def __str__(self):
        return f"{self.participant_a} {self.interaction_type} {self.participant_b}"

    def as_dict(self):
        """Convert object values to dictionary."""
        pathway_commons = object_as_dict(self)
        pathway_commons.update({'pmids': [x.pmid for x in self.pmids]})
        pathway_commons.update({'pathway_names': [x.name for x in self.pathway_names]})
        pathway_commons.update({'sources': [x.source for x in self.sources]})
        return pathway_commons


class PathwayName(Base):
    """Class definition for the pathway_commons_pathway_name table."""

    __tablename__ = 'pathway_commons_pathway_name'
    id = Column(Integer, primary_key=True)

    name = Column(String(255), index=True)

    pathway_commonses = relationship(
        "PathwayCommons",
        secondary=pathway_commons__pathway_name,
        back_populates="pathway_names")

    def __str__(self):
        """Class string definition."""
        return self.name


class Pmid(Base):
    """Class definition for the pathway_commons_pmid table."""

    __tablename__ = 'pathway_commons_pmid'
    id = Column(Integer, primary_key=True)

    pmid = Column(BigInteger, index=True)

    pathway_commons_id = Column(Integer, ForeignKey('pathway_commons.id'), index=True)
    pathway_commons = relationship("PathwayCommons", back_populates="pmids")

    def __str__(self):
        """Class string definition."""
        return str(self.pmid)


class Source(Base):
    """Class definition for the pathway_commons_source table."""

    __tablename__ = 'pathway_commons_source'
    id = Column(Integer, primary_key=True)

    source = Column(String(50))

    pathway_commonses = relationship(
        "PathwayCommons",
        secondary=pathway_commons__source,
        back_populates="sources")

    def __str__(self):
        """Class string definition."""
        return self.source
