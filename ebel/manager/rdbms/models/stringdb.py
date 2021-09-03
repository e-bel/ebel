"""StringDB RDBMS model definition."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, SmallInteger, Boolean

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class StringDb(Base):
    """Class definition for the stringdb table."""

    __tablename__ = 'stringdb'

    id = Column(Integer, primary_key=True)

    protein1 = Column(String(50), nullable=False)
    protein2 = Column(String(50), nullable=False)
    symbol1 = Column(String(50), nullable=False, index=True)
    symbol2 = Column(String(50), nullable=False, index=True)
    neighborhood = Column(Integer)
    neighborhood_transferred = Column(SmallInteger)
    fusion = Column(SmallInteger)
    cooccurence = Column(SmallInteger)
    homology = Column(SmallInteger)
    coexpression = Column(SmallInteger)
    coexpression_transferred = Column(SmallInteger)
    experiments = Column(SmallInteger, index=True)
    experiments_transferred = Column(SmallInteger)
    database = Column(Integer)
    database_transferred = Column(SmallInteger)
    textmining = Column(SmallInteger)
    textmining_transferred = Column(SmallInteger)
    combined_score = Column(SmallInteger)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])


class StringDbProtein(Base):
    """Class definition for the stringdb_protein table."""

    __tablename__ = 'stringdb_protein'

    id = Column(Integer, primary_key=True)
    protein_external_id = Column(String(50), nullable=False, index=True)
    preferred_name = Column(String(50), nullable=False, index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])


class StringDbAction(Base):
    """Class definition for the stringdb_action table."""

    __tablename__ = 'stringdb_action'
    id = Column(Integer, primary_key=True)
    item_id_a = Column(String(50), nullable=False)
    item_id_b = Column(String(50), nullable=False)
    symbol1 = Column(String(50), nullable=False, index=True)
    symbol2 = Column(String(50), nullable=False, index=True)
    mode = Column(String(20), nullable=False, index=True)
    action = Column(String(20))
    is_directional = Column(Boolean, nullable=False, index=True)
    a_is_acting = Column(Boolean, nullable=False, index=True)
    score = Column(SmallInteger)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=['id'])
