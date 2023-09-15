"""ClinicalTrials.gov RDBMS model definition."""
import re
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String, Table, Text, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column, Mapped

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()

ctg_keyword_n2m = Table(
    "clinical_trials_gov__keyword",
    Base.metadata,
    Column(
        "clinical_trials_gov_keyword_id",
        Integer,
        ForeignKey("clinical_trials_gov_keyword.id"),
        index=True,
    ),
    Column(
        "clinical_trials_gov_id",
        Integer,
        ForeignKey("clinical_trials_gov.id"),
        index=True,
    ),
)

ctg_condition_n2m = Table(
    "clinical_trials_gov__condition",
    Base.metadata,
    Column(
        "clinical_trials_gov_condition_id",
        Integer,
        ForeignKey("clinical_trials_gov_condition.id"),
        index=True,
    ),
    Column(
        "clinical_trials_gov_id",
        Integer,
        ForeignKey("clinical_trials_gov.id"),
        index=True,
    ),
)

ctg_mesh_term_n2m = Table(
    "clinical_trials_gov__mesh_term",
    Base.metadata,
    Column(
        "clinical_trials_gov_mesh_term_id",
        Integer,
        ForeignKey("clinical_trials_gov_mesh_term.id"),
        index=True,
    ),
    Column(
        "clinical_trials_gov_id",
        Integer,
        ForeignKey("clinical_trials_gov.id"),
        index=True,
    ),
)

ctg_intervention_n2m = Table(
    "clinical_trials_gov__intervention",
    Base.metadata,
    Column(
        "clinical_trials_gov_intervention_id",
        Integer,
        ForeignKey("clinical_trials_gov_intervention.id"),
        index=True,
    ),
    Column(
        "clinical_trials_gov_id",
        Integer,
        ForeignKey("clinical_trials_gov.id"),
        index=True,
    ),
)


class ClinicalTrialGov(Base):
    """Class definition for the clinical_trials_gov table."""

    __tablename__ = "clinical_trials_gov"

    id: Mapped[int] = mapped_column(primary_key=True)
    nct_id = mapped_column(String(100), index=True)
    org_study_id: Mapped[Optional[str]] = mapped_column(Text)
    brief_title: Mapped[Optional[str]] = mapped_column(Text)
    official_title: Mapped[Optional[str]] = mapped_column(Text)
    is_fda_regulated_drug: Mapped[Optional[str]] = mapped_column(Text)
    brief_summary: Mapped[Optional[str]] = mapped_column(Text)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text)
    overall_status: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[str]] = mapped_column(Text)
    completion_date: Mapped[Optional[str]] = mapped_column(Text)
    phase: Mapped[Optional[str]] = mapped_column(Text)
    study_type: Mapped[Optional[str]] = mapped_column(Text)
    study_design_intervention_model: Mapped[Optional[str]] = mapped_column(Text)
    study_design_primary_purpose: Mapped[Optional[str]] = mapped_column(Text)
    study_design_masking: Mapped[Optional[str]] = mapped_column(Text)
    # primary_outcomes
    # secondary_outcomes
    patient_data_sharing_ipd: Mapped[Optional[str]] = mapped_column(Text)
    patient_data_ipd_description: Mapped[Optional[str]] = mapped_column(Text)

    keywords: Mapped[List["Keyword"]] = relationship(
        "Keyword",
        secondary=ctg_keyword_n2m,
        back_populates="trials",
        cascade="save-update",
    )

    conditions: Mapped[List["Condition"]] = relationship(
        "Condition",
        secondary=ctg_condition_n2m,
        back_populates="trials",
        cascade="save-update",
    )

    mesh_terms: Mapped[List["MeshTerm"]] = relationship(
        "MeshTerm",
        secondary=ctg_mesh_term_n2m,
        back_populates="trials",
        cascade="save-update",
    )

    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention",
        secondary=ctg_intervention_n2m,
        back_populates="trials",
        cascade="save-update",
    )

    def as_dict(self):
        """Convert object values to dictionary."""
        basic_dict = object_as_dict(self)
        basic_dict["brief_summary"] = re.sub(r"\r?\n\s*", " ", basic_dict["brief_summary"]).strip()
        basic_dict.update({"keywords": [x.keyword for x in self.keywords]})
        basic_dict.update({"conditions": [x.condition for x in self.conditions]})
        basic_dict.update({"mesh_terms": [x.mesh_term for x in self.mesh_terms]})
        basic_dict.update(
            {
                "interventions": [
                    {
                        "intervention_type": x.intervention_type,
                        "intervention_name": x.intervention_name,
                    }
                    for x in self.interventions
                ]
            }
        )
        return basic_dict


class Keyword(Base):
    """Class definition for the clinical_trials_gov_keyword table."""

    __tablename__ = "clinical_trials_gov_keyword"
    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(255), index=True)
    trials: Mapped[List["ClinicalTrialGov"]] = relationship(
        "ClinicalTrialGov", secondary=ctg_keyword_n2m, back_populates="keywords"
    )

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"keyword": self.keyword, "nct_ids": [x.nct_id for x in self.trials]}


class Condition(Base):
    """Class definition for the clinical_trials_gov_condition table."""

    __tablename__ = "clinical_trials_gov_condition"
    id: Mapped[int] = mapped_column(primary_key=True)
    condition: Mapped[str] = mapped_column(Text)
    trials: Mapped[List["ClinicalTrialGov"]] = relationship(
        "ClinicalTrialGov", secondary=ctg_condition_n2m, back_populates="conditions"
    )

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"condition": self.condition, "nct_ids": [x.nct_id for x in self.trials]}


class MeshTerm(Base):
    """Class definition for the clinical_trials_gov_mesh_term table."""

    __tablename__ = "clinical_trials_gov_mesh_term"
    id: Mapped[int] = mapped_column(primary_key=True)
    mesh_term: Mapped[str] = mapped_column(String(100), unique=True)
    trials: Mapped[List["ClinicalTrialGov"]] = relationship(
        "ClinicalTrialGov", secondary=ctg_mesh_term_n2m, back_populates="mesh_terms"
    )

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "mesh_term": self.mesh_term,
            "number_of_trials": len(self.trials),
            "nct_ids": [x.nct_id for x in self.trials],
        }


class Intervention(Base):
    """Class definition for the clinical_trials_gov_intervention table."""

    __tablename__ = "clinical_trials_gov_intervention"
    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_type: Mapped[str] = mapped_column(String(100), index=True)
    intervention_name: Mapped[str] = mapped_column(String(255), index=True)
    trials: Mapped[List["ClinicalTrialGov"]] = relationship(
        "ClinicalTrialGov",
        secondary=ctg_intervention_n2m,
        back_populates="interventions",
    )

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "intervention_type": self.intervention_type,
            "intervention_name": self.intervention_name,
            "nct_ids": [x.nct_id for x in self.trials],
        }
