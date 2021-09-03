"""ClinicalTrials.gov RDBMS model definition."""
import re

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, Text, ForeignKey

from ebel.manager.rdbms.models import object_as_dict


Base = declarative_base()

ctg_keyword_n2m = Table('clinical_trials_gov__keyword', Base.metadata,
                        Column('clinical_trials_gov_keyword_id', Integer, ForeignKey('clinical_trials_gov_keyword.id'),
                               index=True),
                        Column('clinical_trials_gov_id', Integer,
                               ForeignKey('clinical_trials_gov.id'), index=True)
                        )

ctg_condition_n2m = Table('clinical_trials_gov__condition', Base.metadata,
                          Column('clinical_trials_gov_condition_id', Integer,
                                 ForeignKey('clinical_trials_gov_condition.id'),
                                 index=True),
                          Column('clinical_trials_gov_id', Integer,
                                 ForeignKey('clinical_trials_gov.id'), index=True)
                          )

ctg_mesh_term_n2m = Table('clinical_trials_gov__mesh_term', Base.metadata,
                          Column('clinical_trials_gov_mesh_term_id', Integer,
                                 ForeignKey('clinical_trials_gov_mesh_term.id'),
                                 index=True),
                          Column('clinical_trials_gov_id', Integer,
                                 ForeignKey('clinical_trials_gov.id'), index=True)
                          )

ctg_intervention_n2m = Table('clinical_trials_gov__intervention', Base.metadata,
                             Column('clinical_trials_gov_intervention_id', Integer,
                                    ForeignKey('clinical_trials_gov_intervention.id'),
                                    index=True),
                             Column('clinical_trials_gov_id', Integer,
                                    ForeignKey('clinical_trials_gov.id'), index=True)
                             )


class ClinicalTrialGov(Base):
    """Class definition for the clinical_trials_gov table."""

    __tablename__ = 'clinical_trials_gov'

    id = Column(Integer, primary_key=True)
    nct_id = Column(String(100), index=True)
    org_study_id = Column(Text)
    brief_title = Column(Text)
    official_title = Column(Text)
    is_fda_regulated_drug = Column(Text)
    brief_summary = Column(Text)
    detailed_description = Column(Text)
    overall_status = Column(Text)
    start_date = Column(Text)
    completion_date = Column(Text)
    phase = Column(Text)
    study_type = Column(Text)
    study_design_intervention_model = Column(Text)
    study_design_primary_purpose = Column(Text)
    study_design_masking = Column(Text)
    # primary_outcomes
    # secondary_outcomes
    patient_data_sharing_ipd = Column(Text)
    patient_data_ipd_description = Column(Text)

    keywords = relationship(
        "Keyword",
        secondary=ctg_keyword_n2m,
        back_populates="trials",
        cascade="save-update"
    )

    conditions = relationship(
        "Condition",
        secondary=ctg_condition_n2m,
        back_populates="trials",
        cascade="save-update"
    )

    mesh_terms = relationship(
        "MeshTerm",
        secondary=ctg_mesh_term_n2m,
        back_populates="trials",
        cascade="save-update"
    )

    interventions = relationship(
        "Intervention",
        secondary=ctg_intervention_n2m,
        back_populates="trials",
        cascade="save-update"
    )

    def as_dict(self):
        """Convert object values to dictionary."""
        basic_dict = object_as_dict(self)
        basic_dict['brief_summary'] = re.sub(r'\r?\n\s*', ' ', basic_dict['brief_summary']).strip()
        basic_dict.update({'keywords': [x.keyword for x in self.keywords]})
        basic_dict.update({'conditions': [x.condition for x in self.conditions]})
        basic_dict.update({'mesh_terms': [x.mesh_term for x in self.mesh_terms]})
        basic_dict.update({'interventions': [
            {'intervention_type': x.intervention_type,
             'intervention_name': x.intervention_name} for x in self.interventions]})
        return basic_dict


class Keyword(Base):
    """Class definition for the clinical_trials_gov_keyword table."""

    __tablename__ = 'clinical_trials_gov_keyword'
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255, collation='utf8_bin'), index=True)
    trials = relationship(
        "ClinicalTrialGov",
        secondary=ctg_keyword_n2m,
        back_populates="keywords")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'keyword': self.keyword,
            'nct_ids': [x.nct_id for x in self.trials]
        }


class Condition(Base):
    """Class definition for the clinical_trials_gov_condition table."""

    __tablename__ = 'clinical_trials_gov_condition'
    id = Column(Integer, primary_key=True)
    condition = Column(Text)
    trials = relationship(
        "ClinicalTrialGov",
        secondary=ctg_condition_n2m,
        back_populates="conditions")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'condition': self.condition,
            'nct_ids': [x.nct_id for x in self.trials]
        }


class MeshTerm(Base):
    """Class definition for the clinical_trials_gov_mesh_term table."""

    __tablename__ = 'clinical_trials_gov_mesh_term'
    id = Column(Integer, primary_key=True)
    mesh_term = Column(String(100), unique=True)
    trials = relationship(
        "ClinicalTrialGov",
        secondary=ctg_mesh_term_n2m,
        back_populates="mesh_terms")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'mesh_term': self.mesh_term,
            'number_of_trials': len(self.trials),
            'nct_ids': [x.nct_id for x in self.trials]
        }


class Intervention(Base):
    """Class definition for the clinical_trials_gov_intervention table."""

    __tablename__ = 'clinical_trials_gov_intervention'
    id = Column(Integer, primary_key=True)
    intervention_type = Column(String(100, collation='utf8_bin'), index=True)
    intervention_name = Column(String(255, collation='utf8_bin'), index=True)
    trials = relationship(
        "ClinicalTrialGov",
        secondary=ctg_intervention_n2m,
        back_populates="interventions")

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            'intervention_type': self.intervention_type,
            'intervention_name': self.intervention_name,
            'nct_ids': [x.nct_id for x in self.trials]
        }
