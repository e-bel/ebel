"""IntAct RDBMS model definition."""
from typing import Optional

from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Intact(Base):
    """Class definition for the intact table."""

    __tablename__ = "intact"
    id: Mapped[int] = mapped_column(primary_key=True)
    confidence_value: Mapped[float] = mapped_column(index=True)
    detection_method: Mapped[str] = mapped_column(String(100), index=True)
    detection_method_psimi_id: Mapped[int] = mapped_column()
    int_a_uniprot_id: Mapped[str] = mapped_column(String(50), index=True)
    int_b_uniprot_id: Mapped[str] = mapped_column(String(50), index=True)
    interaction_ids: Mapped[str] = mapped_column(Text)
    interaction_type: Mapped[str] = mapped_column(String(100), index=True)
    interaction_type_psimi_id: Mapped[int] = mapped_column()
    pmid: Mapped[Optional[int]] = mapped_column()

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
