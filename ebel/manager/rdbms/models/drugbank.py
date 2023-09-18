"""DrugBank RDBMS model definition."""
import datetime
from typing import List, Optional

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column, Mapped

Base = declarative_base()


class Drugbank(Base):
    """Class definition for the drugbank table."""

    __tablename__ = "drugbank"

    id: Mapped[int] = mapped_column(primary_key=True)
    drugbank_id: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    cas_number: Mapped[Optional[str]] = mapped_column(String(20))
    unii: Mapped[Optional[str]] = mapped_column(String(20))
    state: Mapped[Optional[str]] = mapped_column(String(20))
    indication: Mapped[Optional[str]] = mapped_column(Text)
    pharmacodynamics: Mapped[Optional[str]] = mapped_column(Text)
    toxicity: Mapped[Optional[str]] = mapped_column(Text)
    metabolism: Mapped[Optional[str]] = mapped_column(Text)
    absorption: Mapped[Optional[str]] = mapped_column(Text)
    half_life: Mapped[Optional[str]] = mapped_column(Text)
    route_of_elimination: Mapped[Optional[str]] = mapped_column(Text)
    volume_of_distribution: Mapped[Optional[str]] = mapped_column(Text)
    clearance: Mapped[Optional[str]] = mapped_column(Text)
    mechanism_of_action: Mapped[Optional[str]] = mapped_column(Text)
    fda_label: Mapped[Optional[str]] = mapped_column(Text)

    references: Mapped[List["Reference"]] = relationship("Reference", back_populates="drugbank", cascade="save-update")
    synonyms: Mapped[List["Synonym"]] = relationship("Synonym", back_populates="drugbank", cascade="save-update")
    targets: Mapped[List["Target"]] = relationship("Target", back_populates="drugbank", cascade="save-update")
    external_identifiers: Mapped[List["ExternalIdentifier"]] = relationship(
        "ExternalIdentifier", back_populates="drugbank", cascade="save-update"
    )
    product_names: Mapped[List["ProductName"]] = relationship(
        "ProductName", back_populates="drugbank", cascade="save-update"
    )
    drug_interactions: Mapped[List["DrugInteraction"]] = relationship(
        "DrugInteraction", back_populates="drugbank", cascade="save-update"
    )
    statuses: Mapped[List["Status"]] = relationship("Status", back_populates="drugbank", cascade="save-update")
    patents: Mapped[List["Patent"]] = relationship("Patent", back_populates="drugbank", cascade="save-update")
    pathways: Mapped[List["Pathway"]] = relationship("Pathway", back_populates="drugbank", cascade="save-update")

    def __str__(self):
        """Class string definition."""
        return self.drugbank_id

    # TODO: add drug_interaction
    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "drugbank_id": self.drugbank_id,
            "name": self.name,
            "description": self.description,
            "cas_number": self.cas_number,
            "toxicity": self.toxicity,
            "indication": self.indication,
            "pharmacodynamics": self.pharmacodynamics,
            "metabolism": self.metabolism,
            "absorption": self.absorption,
            "half_life": self.half_life,
            "route_of_elimination": self.route_of_elimination,
            "volume_of_distribution": self.volume_of_distribution,
            "clearance": self.clearance,
            "mechanism_of_action": self.mechanism_of_action,
            "fda_label": self.fda_label,
            "references": [x.pmid for x in self.references],
            "pathways": [x.smpdb_id for x in self.pathways],
            "patents": [x.as_dict() for x in self.patents],
            "targets": [x.as_dict() for x in self.targets],
            "product_names": [x.name for x in self.product_names],
            "external_identifiers": [x.as_dict() for x in self.external_identifiers],
            "statuses": [x.status for x in self.statuses],
        }


class Pathway(Base):
    """Class definition for the drugbank_pathway table."""

    __tablename__ = "drugbank_pathway"

    id: Mapped[int] = mapped_column(primary_key=True)
    smpdb_id: Mapped[str] = mapped_column(String(255))

    drugbank_id: Mapped[str] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped["Drugbank"] = relationship("Drugbank", back_populates="pathways")

    def __str__(self):
        return self.smpdb_id

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"smpdb_id": self.smpdb_id, "drugbank_id": self.drugbank.drugbank_id}


class Patent(Base):
    """Class definition for the drugbank_patent table."""

    __tablename__ = "drugbank_patent"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(255))
    approved: Mapped[datetime.date] = mapped_column(Date)
    expires: Mapped[datetime.date] = mapped_column(Date)
    pediatric_extension: Mapped[str] = mapped_column(String(255))

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="patents")

    def __str__(self):
        return self.number

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "number": self.number,
            "country": self.country,
            "approved": self.approved.strftime("%Y-%m-%d"),
            "expires": self.expires.strftime("%Y-%m-%d"),
            "pediatric_extension": self.pediatric_extension,
            "drugbank_id": self.drugbank.drugbank_id,
        }


class Status(Base):
    """Class definition for the drugbank_status table."""

    __tablename__ = "drugbank_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(20), index=True)

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="statuses")

    def __str__(self):
        return self.status

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"smpdb_id": self.status, "drugbank_id": self.drugbank.drugbank_id}


class ExternalIdentifier(Base):
    """Class definition for the drugbank_external_identifier table."""

    __tablename__ = "drugbank_external_identifier"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource: Mapped[str] = mapped_column(String(255), index=True)
    identifier: Mapped[str] = mapped_column(String(255), index=True)

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="external_identifiers")

    def __str__(self):
        return self.identifier

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "resource": self.resource,
            "identifier": self.identifier,
            "drugbank_id": self.drugbank.drugbank_id,
        }


class Reference(Base):
    """Class definition for the drugbank_reference table."""

    __tablename__ = "drugbank_reference"

    id: Mapped[int] = mapped_column(primary_key=True)
    pmid: Mapped[int] = mapped_column()

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="references")

    def __str__(self):
        return self.pmid

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"pmid": self.pmid, "drugbank_id": self.drugbank.drugbank_id}


class Target(Base):
    """Class definition for the drugbank_target table."""

    __tablename__ = "drugbank_target"

    id: Mapped[int] = mapped_column(primary_key=True)
    uniprot: Mapped[str] = mapped_column(String(20), index=True)
    action: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    known_action: Mapped[str] = mapped_column(String(20), index=True)

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="targets")

    def __str__(self):
        return self.uniprot

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "uniprot": self.uniprot,
            "action": self.action,
            "known_action": self.known_action,
            "drugbank_id": self.drugbank.drugbank_id,
        }


class DrugInteraction(Base):
    """Class definition for the drugbank_drug_interaction table."""

    __tablename__ = "drugbank_drug_interaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    drugbank_id: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)

    db_id: Mapped[str] = mapped_column(ForeignKey("drugbank.id"))  # exception because drugbank_id is already a field
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="drug_interactions")

    def __str__(self):
        return self.drugbank_id

    def as_dict(self):
        """Convert object values to dictionary."""
        return {
            "drugbank_id": self.drugbank_id,
            "name": self.name,
            "description": self.description,
            "interactor_drugbank_id": self.drugbank.drugbank_id,
        }


class ProductName(Base):
    """Class definition for the drugbank_product_name table."""

    __tablename__ = "drugbank_product_name"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="product_names")

    def __str__(self):
        return self.name

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"drugbank_id": self.drugbank.drugbank_id, "name": self.name}


class Synonym(Base):
    """Class definition for the drugbank_synonym table."""

    __tablename__ = "drugbank_synonym"

    id: Mapped[int] = mapped_column(primary_key=True)
    synonym: Mapped[str] = mapped_column(Text)

    drugbank_id: Mapped[int] = mapped_column(ForeignKey("drugbank.id"))
    drugbank: Mapped[Drugbank] = relationship("Drugbank", back_populates="synonyms")

    def __str__(self):
        return self.synonym

    def as_dict(self):
        """Convert object values to dictionary."""
        return {"drugbank_id": self.drugbank.drugbank_id, "synonym": self.synonym}
