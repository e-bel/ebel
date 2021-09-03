"""IntAct RDBMS model definition."""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()


class Intact(Base):
    """Class definition for the intact table."""

    __tablename__ = 'intact'
    id = Column(Integer, primary_key=True)
    confidence_value = Column(Float, index=True)
    detection_method = Column(String(100), index=True)
    detection_method_psimi_id = Column(Integer)
    int_a_uniprot_id = Column(String(50), index=True)
    int_b_uniprot_id = Column(String(50), index=True)
    interaction_ids = Column(Text)
    interaction_type = Column(String(100), index=True)
    interaction_type_psimi_id = Column(Integer)
    pmid = Column(Integer)

    def as_dict(self):
        """Convert object values to dictionary."""
        return object_as_dict(self)
