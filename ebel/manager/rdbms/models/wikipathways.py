"""WikiPathways RDBMS model definition."""
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, Table, ForeignKey

from ebel.manager.rdbms.models import object_as_dict

Base = declarative_base()

node_pathway_association = Table(
    'node_pathway_association',
    Base.metadata,
    Column('pathway_id', String(25), ForeignKey('wikipathways_pathway.id'), primary_key=True),
    Column('node_id', String(25), ForeignKey('wikipathways_node.id'), primary_key=True)
)

interaction_pubref_association = Table(
    'interaction_pubref_association',
    Base.metadata,
    Column('pubref_id', String(25), ForeignKey('wikipathways_pub_ref.id'), primary_key=True),
    Column('interaction_id', String(25), ForeignKey('wikipathways_interaction.id'), primary_key=True)
)

interaction_participants = Table(
    'interaction_participants',
    Base.metadata,
    Column('node_id', String(25), ForeignKey('wikipathways_node.id'), primary_key=True),
    Column('interaction_id', String(25), ForeignKey('wikipathways_interaction.id'), primary_key=True)
)

interaction_pathway_association = Table(
    'interaction_pathway_association',
    Base.metadata,
    Column('node_id', String(25), ForeignKey('wikipathways_pathway.id'), primary_key=True),
    Column('interaction_id', String(25), ForeignKey('wikipathways_interaction.id'), primary_key=True)
)


class Node(Base):
    """Class definition for the wikipathways table."""
    __tablename__ = 'wikipathways_node'

    id = Column(String(255), primary_key=True, index=True)

    type = Column(String(25))
    label = Column(String(25))
    data_source = Column(String(50), index=True)
    data_source_id = Column(String(50))

    sources = relationship("Interaction", foreign_keys="Interaction.source_id", backref="source", lazy="dynamic")
    targets = relationship("Interaction", foreign_keys="Interaction.target_id", backref="target", lazy="dynamic")

    pathways = relationship("Pathway", secondary=node_pathway_association, back_populates="nodes")

    # Complexes
    complexes = relationship("Interaction", secondary=interaction_participants, back_populates="participants",)


class Interaction(Base):
    """Class definition for the wikipathways_pub_ref table."""
    __tablename__ = 'wikipathways_interaction'

    id = Column(String(255), primary_key=True, index=True)

    data_source = Column(String(50), index=True)
    data_source_id = Column(String(50))
    link = Column(String(255))

    # Interaction source/target nodes
    source_id = Column(String(255), ForeignKey(Node.id))
    target_id = Column(String(255), ForeignKey(Node.id))

    # PublicationReferences
    references = relationship(
        "PublicationReference",
        secondary=interaction_pubref_association,
        back_populates="interactions",
    )

    # ComplexBinding is an interaction between several "nodes"
    participants = relationship(Node, secondary=interaction_participants, back_populates="complexes",)

    # Pathway links
    pathways = relationship("Pathway", secondary=interaction_pathway_association, back_populates="interactions",)


class Pathway(Base):
    """Class definition for the wikipathways_pathway table."""
    __tablename__ = 'wikipathways_pathway'

    id = Column(String(255), primary_key=True, index=True)

    label = Column(String(25))
    data_source = Column(String(50), index=True)
    data_source_id = Column(String(50))
    description = Column(String(255))
    organism = Column(String(100))

    nodes = relationship(Node, secondary=node_pathway_association, back_populates="pathways")
    interactions = relationship(Interaction, secondary=interaction_pathway_association, back_populates="pathways",)


class PublicationReference(Base):
    """Class definition for the wikipathways_pub_ref table."""
    __tablename__ = 'wikipathways_pub_ref'

    id = Column(String(255), primary_key=True, index=True)

    data_source = Column(String(50), index=True)
    data_source_id = Column(String(50))
    link = Column(String(255))

    interactions = relationship(
        Interaction,
        secondary=interaction_pubref_association,
        back_populates="references",
    )