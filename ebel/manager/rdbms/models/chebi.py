"""CHEBI RDBMS model definition."""

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index

Base = declarative_base()


class ChemicalData(Base):
    """Class definition for the chebi_chemical_data table."""

    __tablename__ = 'chebi_chemical_data'
    id = Column(Integer, primary_key=True)

    chemical_data = Column(Text, nullable=True)
    source = Column(Text, nullable=False)
    type = Column(Text, nullable=False)

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="chemicalData")

    def __str__(self):
        """Class string definition."""
        return self.chemical_data

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'chemical_data': self.chemical_data,
            'source': self.source,
            'type': self.type,
        }


class Comment(Base):
    """Class definition for the chebi_comment table."""

    __tablename__ = 'chebi_comment'
    id = Column(Integer, primary_key=True)

    text = Column(Text, nullable=False)
    created_on = Column(DateTime, nullable=False)
    datatype = Column(String(80))
    datatype_id = Column(Integer, nullable=False)

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="comments")

    def __str__(self):
        """Class string definition."""
        return self.text

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'text': self.text,
            'datatype': self.datatype,
        }


class Compound(Base):
    """Class definition for the chebi_compound table."""

    __tablename__ = 'chebi_compound'
    id = Column(Integer, primary_key=True)

    name = Column(String(2000))
    source = Column(String(32), nullable=False)
    parent_id = Column(Integer)
    chebi_accession = Column(String(30), nullable=False)
    status = Column(String(1), nullable=False)
    definition = Column(Text)
    star = Column(Integer, nullable=False)
    modified_on = Column(Text)
    created_by = Column(Text)

    chemicalData = relationship("ChemicalData", back_populates="compounds")
    comments = relationship("Comment", back_populates="compounds")
    database_accessions = relationship("DatabaseAccession", back_populates="compounds")
    names = relationship("Name", back_populates="compounds")
    references = relationship("Reference", back_populates="compounds")
    # final_id_relations = relationship("Relation", back_populates="final_id_compounds")
    # init_id_relations = relationship("Relation", back_populates="init_id_compounds")
    structures = relationship("Structure", back_populates="compounds")
    inchis = relationship("Inchi", back_populates="compounds")

    def __str__(self):
        return self.name

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'name': self.name,
            'source': self.source,
            'parent_id': self.parent_id,
            'chebi_accession': self.chebi_accession,
            'status': self.status,
            'definition': self.definition,
            'chemicalData': [x.as_dict() for x in self.chemicalData],
            'comments': [x.as_dict() for x in self.comments],
            'database_accessions': [x.as_dict() for x in self.database_accessions],
            'names': [x.as_dict() for x in self.names],
            'references': [x.as_dict() for x in self.references],
            'inchis': [x.as_dict() for x in self.inchis]
        }


class Inchi(Base):
    """Class definition for the chebi_inchi table."""

    __tablename__ = 'chebi_inchi'
    id = Column(Integer, primary_key=True)

    inchi = Column(Text)

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="inchis")

    def __str__(self):
        return self.inchi

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'inchi': self.inchi
        }


class DatabaseAccession(Base):
    """Class definition for the chebi_database_accession table."""

    __tablename__ = 'chebi_database_accession'
    id = Column(Integer, primary_key=True)

    accession_number = Column(String(255), nullable=True)
    type = Column(Text, nullable=False)
    source = Column(Text, nullable=False)

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="database_accessions")

    def __str__(self):
        return self.accession_number

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'accession_number': self.accession_number,
            'type': self.type,
            'source': self.source,
        }


class Name(Base):
    """Class definition for the chebi_name table."""

    __tablename__ = 'chebi_name'
    id = Column(Integer, primary_key=True)

    name = Column(Text, nullable=True)
    type = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    adapted = Column(Text, nullable=False)
    language = Column(Text, nullable=False)

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="names")

    def __str__(self):
        return self.name

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'name': self.name,
            'type': self.type,
            'source': self.source,
            'adapted': self.adapted,
            'language': self.language
        }


class Reference(Base):
    """Class definition for the chebi_reference table."""

    __tablename__ = 'chebi_reference'

    id = Column(Integer, primary_key=True)

    reference_id = Column(String(60), nullable=False, index=True)
    reference_db_name = Column(String(60), nullable=False, index=True)
    location_in_ref = Column(String(90), index=True)
    reference_name = Column(String(1024))

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="references")

    __table_args__ = (Index('ix_chebi_reference__reference_name', reference_name, mysql_length=500),)

    def __str__(self):
        return f"{self.reference_db_name}:{self.reference_id}"

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'reference_id': self.reference_id,
            'reference_db_name': self.reference_db_name,
            'location_in_ref': self.location_in_ref,
            'reference_name': self.reference_name,
        }

    def as_dict_with_compound_id(self):
        """Convert object values to dictionary with compound ID."""
        return {
            'reference_id': self.reference_id,
            'reference_db_name': self.reference_db_name,
            'location_in_ref': self.location_in_ref,
            'reference_name': self.reference_name,
            'compound_id': self.compound_id
        }


class Relation(Base):
    """Class definition for the chebi_relation table."""

    __tablename__ = 'chebi_relation'
    id = Column(Integer, primary_key=True)

    type = Column(Text, nullable=False)
    status = Column(String(1), nullable=False)

    final_id = Column(Integer, ForeignKey('chebi_compound.id'))
    init_id = Column(Integer, ForeignKey('chebi_compound.id'))

    final_id_compounds = relationship("Compound", foreign_keys=[final_id])
    init_id_compounds = relationship("Compound", foreign_keys=[init_id])

    def __str__(self):
        return f"{self.type} - {self.status}"

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'type': self.type,
            'status': self.status,
            'final_id': self.final_id,
            'init_id': self.init_id
        }


class Structure(Base):
    """Class definition for the chebi_structure table."""

    __tablename__ = 'chebi_structure'
    id = Column(Integer, primary_key=True)

    structure = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    dimension = Column(Text, nullable=False)
    default_structure = Column(String(1), nullable=False)
    autogen_structure = Column(String(1), nullable=False)

    compound_id = Column(Integer, ForeignKey('chebi_compound.id'))
    compounds = relationship("Compound", back_populates="structures")

    def __str__(self):
        return self.structure
