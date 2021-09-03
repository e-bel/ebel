"""BioGRID RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey

from ebel.manager.rdbms.models import object_as_dict


Base = declarative_base()


class Biogrid(Base):
    """Class definition for the biogrid table."""

    __tablename__ = 'biogrid'
    id = Column(Integer, primary_key=True)

    biogrid_a_id = Column(Integer, ForeignKey('biogrid_interactor.biogrid_id'))
    biogrid_a = relationship("Interactor", foreign_keys=[biogrid_a_id])
    biogrid_b_id = Column(Integer, ForeignKey('biogrid_interactor.biogrid_id'))
    biogrid_b = relationship("Interactor", foreign_keys=[biogrid_b_id])
    biogrid_id = Column(Integer, nullable=True)
    experimental_system_id = Column(Integer, ForeignKey('biogrid_experimental_system.id'))
    experimental_system = relationship("ExperimentalSystem", foreign_keys=[experimental_system_id])
    throughput_id = Column(Integer, ForeignKey('biogrid_throughput.id'))
    throughput = relationship("Throughput", foreign_keys=[throughput_id])
    score = Column(Float, nullable=True)
    modification_id = Column(Integer, ForeignKey('biogrid_modification.id'))
    modification = relationship("Modification", foreign_keys=[modification_id])
    qualifications = Column(String(255), nullable=True)
    source_id = Column(Integer, ForeignKey('biogrid_source.id'))
    source = relationship("Source", foreign_keys=[source_id])
    publication_id = Column(Integer, ForeignKey('biogrid_publication.id'))
    publication = relationship("Publication", foreign_keys=[publication_id])
    qualification = Column(Text, nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'biogrid_a': self.biogrid_a.as_dict(),
            'biogrid_b': self.biogrid_b.as_dict(),
            'experimental_system': self.experimental_system.as_dict() if self.experimental_system else None,
            'throughput': self.throughput.as_dict() if self.throughput else None,
            'biogrid_id': self.biogrid_id,
            'score': self.score if self.score else None,
            'modification': self.modification.as_dict() if self.modification else None,
            'source': self.source.source,
            'publication': self.publication.as_dict(),
            'qualification': self.qualification if self.qualification else None
        }


class Publication(Base):
    """Class definition for the biogrid_publication table."""

    __tablename__ = 'biogrid_publication'
    id = Column(Integer, primary_key=True)
    author_name = Column(String(255), nullable=True)
    publication_year = Column(Integer, nullable=True)
    source = Column(String(255), nullable=True)
    source_identifier = Column(String(255), nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])


class Throughput(Base):
    """Class definition for the biogrid_throughput table."""

    __tablename__ = 'biogrid_throughput'
    id = Column(Integer, primary_key=True)
    throughput = Column(String(255))
    frequency = Column(Integer)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])


class Taxonomy(Base):
    """Class definition for the biogrid_taxonomy table."""

    __tablename__ = 'biogrid_taxonomy'
    taxonomy_id = Column(Integer, primary_key=True)  # == NCBI Taxonomy ID
    organism_name = Column(String(1000))

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'taxonomy_id': self.taxonomy_id,
            'organism_name': self.organism_name
        }


class ExperimentalSystem(Base):
    """Class definition for the biogrid_experimental_system table."""

    __tablename__ = 'biogrid_experimental_system'
    id = Column(Integer, primary_key=True)
    experimental_system = Column(String(255), nullable=True)
    experimental_system_type = Column(String(255), nullable=True)
    frequency = Column(Integer)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])


class Interactor(Base):
    """Class definition for the biogrid_interactor table."""

    __tablename__ = 'biogrid_interactor'
    biogrid_id = Column(Integer, primary_key=True)

    entrez = Column(Integer, nullable=True, index=True)
    systematic_name = Column(String(255), nullable=True, index=True)
    symbol = Column(String(255), nullable=True, index=True)
    taxonomy_id = Column(Integer, ForeignKey('biogrid_taxonomy.taxonomy_id'))
    taxonomy = relationship("Taxonomy", foreign_keys=[taxonomy_id])
    uniprot = Column(String(255), nullable=True, index=True)
    trembl = Column(String(1000), nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'entrez': self.entrez,
            'systematic_name': self.systematic_name,
            'symbol': self.symbol,
            'uniprot': self.uniprot,
            'trembl': self.trembl,
            'taxonomy': self.taxonomy.as_dict()
        }


class Source(Base):
    """Class definition for the biogrid_source table."""

    __tablename__ = 'biogrid_source'
    id = Column(Integer, primary_key=True)
    source = Column(String(255), nullable=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])


class Modification(Base):
    """Class definition for the biogrid_modification table."""

    __tablename__ = 'biogrid_modification'
    id = Column(Integer, primary_key=True)
    modification = Column(String(255), nullable=True)
    frequency = Column(Integer)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])
