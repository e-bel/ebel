"""StringDB RDBMS model definition."""

from sqlalchemy import Boolean, Column, Integer, SmallInteger, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class StringDb(Base):
    """Class definition for the stringdb table."""

    __tablename__ = "stringdb"

    id = mapped_column(Integer, primary_key=True)

    protein1 = mapped_column(String(50), nullable=False)
    protein2 = mapped_column(String(50), nullable=False)
    symbol1 = mapped_column(String(50), nullable=False, index=True)
    symbol2 = mapped_column(String(50), nullable=False, index=True)
    neighborhood = mapped_column(Integer)
    neighborhood_transferred = mapped_column(SmallInteger)
    fusion = mapped_column(SmallInteger)
    cooccurence = mapped_column(SmallInteger)
    homology = mapped_column(SmallInteger)
    coexpression = mapped_column(SmallInteger)
    coexpression_transferred = mapped_column(SmallInteger)
    experiments = mapped_column(SmallInteger, index=True)
    experiments_transferred = mapped_column(SmallInteger)
    database = mapped_column(Integer)
    database_transferred = mapped_column(SmallInteger)
    textmining = mapped_column(SmallInteger)
    textmining_transferred = mapped_column(SmallInteger)
    combined_score = mapped_column(SmallInteger)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class StringDbProtein(Base):
    """Class definition for the stringdb_protein table."""

    __tablename__ = "stringdb_protein"

    id = mapped_column(Integer, primary_key=True)
    string_protein_id = mapped_column(String(50), nullable=False, index=True)
    preferred_name = mapped_column(String(50), nullable=False, index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class StringDbAction(Base):
    """Class definition for the stringdb_action table."""

    __tablename__ = "stringdb_action"
    id = mapped_column(Integer, primary_key=True)
    item_id_a = mapped_column(String(50), nullable=False)
    item_id_b = mapped_column(String(50), nullable=False)
    symbol1 = mapped_column(String(50), nullable=False, index=True)
    symbol2 = mapped_column(String(50), nullable=False, index=True)
    mode = mapped_column(String(20), nullable=False, index=True)
    action = mapped_column(String(20))
    is_directional = mapped_column(Boolean, nullable=False, index=True)
    a_is_acting = mapped_column(Boolean, nullable=False, index=True)
    score = mapped_column(SmallInteger)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])
