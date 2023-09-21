"""StringDB RDBMS model definition."""
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, SmallInteger, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class StringDb(Base):
    """Class definition for the stringdb table."""

    __tablename__ = "stringdb"

    id: Mapped[int] = mapped_column(primary_key=True)

    protein1: Mapped[str] = mapped_column(String(50), nullable=False)
    protein2: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol1: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    symbol2: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    neighborhood: Mapped[int] = mapped_column()
    neighborhood_transferred: Mapped[int] = mapped_column(SmallInteger)
    fusion: Mapped[int] = mapped_column(SmallInteger)
    cooccurence: Mapped[int] = mapped_column(SmallInteger)
    homology: Mapped[int] = mapped_column(SmallInteger)
    coexpression: Mapped[int] = mapped_column(SmallInteger)
    coexpression_transferred: Mapped[int] = mapped_column(SmallInteger)
    experiments: Mapped[int] = mapped_column(SmallInteger, index=True)
    experiments_transferred: Mapped[int] = mapped_column(SmallInteger)
    database: Mapped[int] = mapped_column()
    database_transferred: Mapped[int] = mapped_column(SmallInteger)
    textmining: Mapped[int] = mapped_column(SmallInteger)
    textmining_transferred: Mapped[int] = mapped_column(SmallInteger)
    combined_score: Mapped[int] = mapped_column(SmallInteger)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class StringDbProtein(Base):
    """Class definition for the stringdb_protein table."""

    __tablename__ = "stringdb_protein"

    id: Mapped[int] = mapped_column(primary_key=True)
    string_protein_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    preferred_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])


class StringDbAction(Base):
    """Class definition for the stringdb_action table."""

    __tablename__ = "stringdb_action"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id_a: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id_b: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol1: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    symbol2: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    action: Mapped[Optional[str]] = mapped_column(String(20))
    is_directional: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    a_is_acting: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    score: Mapped[int] = mapped_column(SmallInteger)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self, exclude=["id"])
