"""DrugBank RDBMS model definition."""

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date

Base = declarative_base()


class Drugbank(Base):
    """Class definition for the drugbank table."""

    __tablename__ = 'drugbank'
    id = Column(Integer, primary_key=True)
    drugbank_id = Column(String(10), index=True)
    name = Column(String(255))
    description = Column(Text)
    cas_number = Column(String(20))
    unii = Column(String(20))
    state = Column(String(20))
    indication = Column(Text)
    pharmacodynamics = Column(Text)
    toxicity = Column(Text)
    metabolism = Column(Text)
    absorption = Column(Text)
    half_life = Column(Text)
    route_of_elimination = Column(Text)
    volume_of_distribution = Column(Text)
    clearance = Column(Text)
    mechanism_of_action = Column(Text)
    fda_label = Column(Text)

    references = relationship("Reference", back_populates="drugbank", cascade="save-update")
    synonyms = relationship("Synonym", back_populates="drugbank", cascade="save-update")
    targets = relationship("Target", back_populates="drugbank", cascade="save-update")
    external_identifiers = relationship("ExternalIdentifier", back_populates="drugbank", cascade="save-update")
    product_names = relationship("ProductName", back_populates="drugbank", cascade="save-update")
    drug_interactions = relationship("DrugInteraction", back_populates="drugbank", cascade="save-update")
    statuses = relationship("Status", back_populates="drugbank", cascade="save-update")
    patents = relationship("Patent", back_populates="drugbank", cascade="save-update")
    pathways = relationship("Pathway", back_populates="drugbank", cascade="save-update")

    def __str__(self):
        """Class string definition."""
        return self.drugbank_id

    # TODO: add drug_interaction
    def as_dict(self):
        """Convert object values to dictionary."""
        return {'drugbank_id': self.drugbank_id,
                'name': self.name,
                'description': self.description,
                'cas_number': self.cas_number,
                'toxicity': self.toxicity,
                'indication': self.indication,
                'pharmacodynamics': self.pharmacodynamics,
                'metabolism': self.metabolism,
                'absorption': self.absorption,
                'half_life': self.half_life,
                'route_of_elimination': self.route_of_elimination,
                'volume_of_distribution': self.volume_of_distribution,
                'clearance': self.clearance,
                'mechanism_of_action': self.mechanism_of_action,
                'fda_label': self.fda_label,
                'references': [x.pmid for x in self.references],
                'pathways': [x.smpdb_id for x in self.pathways],
                'patents': [x.as_dict() for x in self.patents],
                'targets': [x.as_dict() for x in self.targets],
                'product_names': [x.name for x in self.product_names],
                'external_identifiers': [x.as_dict() for x in self.external_identifiers],
                'statuses': [x.status for x in self.statuses],
                }


class Pathway(Base):
    """Class definition for the drugbank_pathway table."""

    __tablename__ = 'drugbank_pathway'
    id = Column(Integer, primary_key=True)
    smpdb_id = Column(String(255))

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="pathways")

    def __str__(self):
        return self.smpdb_id

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'smpdb_id': self.smpdb_id, 'drugbank_id': self.drugbank.drugbank_id}


class Patent(Base):
    """Class definition for the drugbank_patent table."""

    __tablename__ = 'drugbank_patent'
    id = Column(Integer, primary_key=True)
    number = Column(String(255))
    country = Column(String(255))
    approved = Column(Date)
    expires = Column(Date)
    pediatric_extension = Column(String(255))

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="patents")

    def __str__(self):
        return self.number

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'number': self.number,
                'country': self.country,
                'approved': self.approved.strftime("%Y-%m-%d"),
                'expires': self.expires.strftime("%Y-%m-%d"),
                'pediatric_extension': self.pediatric_extension,
                'drugbank_id': self.drugbank.drugbank_id
                }


class Status(Base):
    """Class definition for the drugbank_status table."""

    __tablename__ = 'drugbank_status'
    id = Column(Integer, primary_key=True)
    status = Column(String(20), index=True)

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="statuses")

    def __str__(self):
        return self.status

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'smpdb_id': self.status, 'drugbank_id': self.drugbank.drugbank_id}


class ExternalIdentifier(Base):
    """Class definition for the drugbank_external_identifier table."""

    __tablename__ = 'drugbank_external_identifier'
    id = Column(Integer, primary_key=True)
    resource = Column(String(255))
    identifier = Column(String(255), index=True)

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="external_identifiers")

    def __str__(self):
        return self.identifier

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'resource': self.resource, 'identifier': self.identifier, 'drugbank_id': self.drugbank.drugbank_id}


class Reference(Base):
    """Class definition for the drugbank_reference table."""

    __tablename__ = 'drugbank_reference'
    id = Column(Integer, primary_key=True)
    pmid = Column(Integer)

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="references")

    def __str__(self):
        return self.pmid

    def as_dict(self):
        """Convert object values to dictionary."""
        return {'pmid': self.pmid, 'drugbank_id': self.drugbank.drugbank_id}


class Target(Base):
    """Class definition for the drugbank_target table."""

    __tablename__ = 'drugbank_target'
    id = Column(Integer, primary_key=True)
    uniprot = Column(String(20), index=True)
    action = Column(String(50), index=True)
    known_action = Column(String(20), index=True)

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="targets")

    def __str__(self):
        return self.uniprot

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'uniprot': self.uniprot,
            'action': self.action,
            'known_action': self.known_action,
            'drugbank_id': self.drugbank.drugbank_id
        }


class DrugInteraction(Base):
    """Class definition for the drugbank_drug_interaction table."""

    __tablename__ = 'drugbank_drug_interaction'
    id = Column(Integer, primary_key=True)
    drugbank_id = Column(String(10), index=True)
    name = Column(Text)
    description = Column(Text)

    db_id = Column(Integer, ForeignKey('drugbank.id'))  # exception because drugbank_id is already a field
    drugbank = relationship("Drugbank", back_populates="drug_interactions")

    def __str__(self):
        return self.drugbank_id

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'drugbank_id': self.drugbank_id,
            'name': self.name,
            'description': self.description,
            'interactor_drugbank_id': self.drugbank.drugbank_id
        }


class ProductName(Base):
    """Class definition for the drugbank_product_name table."""

    __tablename__ = 'drugbank_product_name'
    id = Column(Integer, primary_key=True)
    name = Column(Text)

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="product_names")

    def __str__(self):
        return self.name

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'drugbank_id': self.drugbank.drugbank_id,
            'name': self.name
        }


class Synonym(Base):
    """Class definition for the drugbank_synonym table."""

    __tablename__ = 'drugbank_synonym'
    id = Column(Integer, primary_key=True)
    synonym = Column(Text)

    drugbank_id = Column(Integer, ForeignKey('drugbank.id'))
    drugbank = relationship("Drugbank", back_populates="synonyms")

    def __str__(self):
        return self.synonym

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'drugbank_id': self.drugbank.drugbank_id,
            'synonym': self.synonym
        }
