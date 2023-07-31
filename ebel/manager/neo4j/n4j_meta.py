"""Connect to Neo4j database."""

import re
import json

from collections import namedtuple
from typing import Optional, Union

import numpy as np
import pandas as pd
from neo4j import GraphDatabase

Relationship = namedtuple("Relationship", ["subj_id", "edge_id", "obj_id"])


def get_standard_name(name: str) -> str:
    """Return standard name."""
    part_of_name = [x for x in re.findall("[A-Z]*[a-z0-9]*", name) if x]
    new_name = "_".join(part_of_name).lower()
    if re.search(r"^\d+", new_name):
        new_name = "_" + new_name
    return new_name


def get_cypher_props(props: Optional[dict]):
    """Convert dictionary to cypher compliant properties as string."""
    props_str = ""
    props_array = []
    if props:
        for k, v in props.items():
            if (isinstance(v, (str, int, list)) and v) or (
                    isinstance(v, float) and not np.isnan(v)
            ):
                cypher_str = f"`{k}`: " + json.dumps(v)
                props_array.append(cypher_str)
        if props_array:
            props_str = "{" + ", ".join(props_array) + "}"
    return props_str


class GraphElement:
    def __init__(self, labels: Union[str, set[str]], props: Optional[dict] = None):
        if isinstance(labels, str):
            labels = {labels}
        self.labels = labels
        self.props = props

    @property
    def cypher_props(self) -> str:
        return get_cypher_props(self.props)

    @property
    def cypher_labels(self) -> str:
        return ":".join([x.strip() for x in self.labels if x.strip()])

    @staticmethod
    def __get_sql_value(value):
        return json.dumps(value) if isinstance(value, str) else value

    def get_where(self, prefix: str) -> Optional[str]:
        if self.props:
            return " AND ".join(
                [
                    f"{prefix}.{k} = {self.__get_sql_value(v)}"
                    for k, v in self.props.items()
                ]
            )

    def __str__(self):
        return f"<{self.labels}: {self.cypher_props}>"


class Node(GraphElement):
    def __init__(self, labels: Union[str, set[str]], props: Optional[dict] = None):
        super().__init__(labels, props)


class Edge(GraphElement):
    def __init__(self, labels: str, props: Optional[dict] = None):
        super().__init__(labels, props)


class Neo4jClient:

    def __init__(self, uri: str, user: str, password: str, database: Optional[str] = None):
        """Initialize connection to Neo4j database. Defaults to "neo4j" if no database given."""
        db = database or "neo4j"
        self.driver = GraphDatabase.driver(uri, auth=(user, password), database=db)

        self.session = self.driver.session()

    def close(self) -> None:
        """Close connection to database."""
        self.driver.close()

    @property
    def schema(self):
        """Get the database schema."""
        return self.session.run("CALL db.schema.visualization()").data()

    def execute(self, cypher: str):
        """Execute a cypher transaction."""
        return self.session.run(cypher).data()

    def count_nodes(self, node: Node):
        cypher = f"match (n:{node.cypher_labels}) return count(n) as num"
        return self.execute(cypher)[0]["num"]

    def count_edges(self, edge: Edge):
        cypher = f"match ()-[r:{edge.cypher_labels}]->() return count(r) as num"
        return self.execute(cypher)[0]["num"]

    def create_node(self, node: Node) -> int:
        """Create a node with label and properties."""
        cypher = (
            f"CREATE (n:{node.cypher_labels} {node.cypher_props}) return elementId(n) as node_id"
        )
        return self.execute(cypher)[0]["node_id"]

    def create_edge(self, subj: Node, edge: Edge, obj: Node) -> Relationship:
        """Create an edge between the given subject and object."""
        cypher = f"CREATE (subj:{subj.cypher_labels} {subj.cypher_props})"
        cypher += f"-[edge:{edge.cypher_labels} {edge.cypher_props}]->"
        cypher += f"(obj:{obj.cypher_labels} {obj.cypher_props})" ""
        cypher += " RETURN elementId(subj) as subj_id, elementId(edge) as edge_id, elementId(obj) as obj_id"
        r = self.session.run(cypher).values()[0]
        return Relationship(*r)

    def merge_node(self, node: Node):
        """Create a node with given props if it does not exist."""
        cypher = (
            f"""MERGE (n:{node.cypher_labels} {node.cypher_props}) return elementId(n) as id"""
        )

        return self.execute(cypher)[0]["id"]

    def merge_edge(self, subj: Node, rel: Edge, obj: Node):
        """MERGE finds or creates a relationship between the nodes."""
        cypher = f"""
            MERGE (subject:{subj.cypher_labels} {subj.cypher_props})
            MERGE (object:{obj.cypher_labels} {obj.cypher_props})
            MERGE (subject)-[relation:{rel.cypher_labels} {rel.cypher_props}]->(object)
            RETURN subject, relation, object, elementId(relation) as rel_id"""
        return self.session.run(cypher)

    def merge_edge_by_node_ids(self, subj_id: str, rel: Edge, obj_id: str):
        """MERGE finds or creates a relationship between the nodes."""
        cypher = f"""MATCH (subj),(obj) 
WHERE elementId(subj)="{subj_id}" and elementId(obj)="{obj_id}" 
MERGE (subj)-[relation:{rel.cypher_labels} {rel.cypher_props}]->(obj)
RETURN subj, relation, obj, elementId(relation) as rel_id"""
        return self.execute(cypher)

    def delete_edges_by_class(self, edge: Edge) -> int:
        """Delete edges by Edge class."""
        where = f"WHERE {edge.get_where('r')}" if edge.props else ""
        cypher = f"""MATCH ()-[r:{edge.cypher_labels}]->() {where} DELETE r RETURN count(r) AS num"""
        return self.execute(cypher)[0]["num"]

    def delete_edge_by_id(self, edge_id: int):
        """Delete an edge by id."""
        cypher = f"""MATCH ()-[r]->()
            WHERE elementId(r) = "{edge_id}"
            DELETE r"""
        return self.session.run(cypher)

    def delete_all_edges(self):
        """Delete all edges."""
        return self.session.run("MATCH ()-[r]->() DELETE r")

    def delete_nodes_by_label(self, node: Node):
        """Delete all nodes (and connected edges) with a specific label."""
        where = f"WHERE {node.get_where('n')}" if node.props else ""
        cypher = (
            f"""MATCH (n:{node.cypher_labels}) {where} DETACH DELETE n """
            "RETURN count(n) AS num"
        )
        return self.execute(cypher)[0]["num"]

    def delete_node_and_connected_edges(self, node_id: int):
        """Delete a node and all relationships/edges connected to it."""
        cypher = f"""MATCH (n)
            WHERE n.id = {node_id}
            DETACH DELETE n"""
        return self.session.run(cypher)

    def delete_node_edge(self, node_id: int, edge_id: int):
        """Delete a node and a relationship by their IDs.
        This will throw an error if the node is attached
        to more than one relationship."""
        cypher = f"""MATCH (n)-[r]-()
            WHERE elementId(r) = "{edge_id}" AND elementId(n) = "{node_id}"
            DELETE n, r"""
        return self.session.run(cypher)

    def delete_everything(self, node: Optional[Node] = None, transition_size=10000, add_auto=False):
        """Delete all nodes and relationships from the database.

        Parameters
        ----------
        node : Optional[Node], optional
            Use the Node class to specify the Node type (including properties), by default None
        transition_size : int, optional
            Number of node and edges deleted in one transaction, by default 10000
        add_auto: bool
            adds ':auto ' at the beginning of each Cypher query if 'True'[default]
        """        """"""
        auto_str = ':auto ' if add_auto else ''

        if node:
            where = node.get_where("n")
            cypher_where = f" WHERE {where}" if where else ""
            cypher_edges = f"""{auto_str}MATCH (n:{node.cypher_labels})-[r]-() {cypher_where}
                CALL {{ WITH r
                    DELETE r
                }} IN TRANSACTIONS OF {transition_size} ROWS"""
            cypher_nodes = f"""{auto_str}MATCH (n:{node.cypher_labels}) {cypher_where}
                CALL {{ WITH n
                    DETACH DELETE n
                }} IN TRANSACTIONS OF {transition_size} ROWS"""
        else:
            cypher_edges = f"{auto_str}MATCH (n)-[r]-() CALL {{ WITH r DELETE r }} IN TRANSACTIONS OF {transition_size} ROWS"
            cypher_nodes = f"{auto_str}MATCH (n) CALL {{ WITH n DETACH DELETE n}} IN TRANSACTIONS OF {transition_size} ROWS"

        self.session.run(cypher_edges)
        self.session.run(cypher_nodes)

        return

    def delete_nodes_with_no_edges(self, node: Node):
        cypher_where = ""
        if node.props:
            where = node.get_where("n")
            if where:
                cypher_where = " AND " + where
        cypher = f"""MATCH (n: {node.cypher_labels})
            WHERE NOT (n)-[]-() {cypher_where}
            DELETE n RETURN count(n) AS number_of_deleted_nodes"""
        return self.execute(cypher)[0]["number_of_deleted_nodes"]

    def delete_all_nodes_with_no_edges(self):
        cypher = """MATCH (n)
            WHERE NOT (n)-[]-()
            DELETE n RETURN count(n) AS number_of_deleted_nodes"""
        return self.execute(cypher)[0]["number_of_deleted_nodes"]

    def get_number_of_nodes(self, node: Optional[Node] = None) -> int:
        where, label = "", ""
        if node:
            where_str = node.get_where("n")
            where = f" WHERE {where_str}" if where_str else ""
            label = f":`{node.cypher_labels}`"
        cypher = f"MATCH (n{label}) {where} RETURN count(n) AS num" ""
        return self.execute(cypher)[0]["num"]

    def get_node_label_statistics(self):
        data = []
        for label in self.node_labels:
            data.append((label, self.get_number_of_nodes(node=Node(label))))
        df = pd.DataFrame(data, columns=['label', 'number_of_nodes'])
        return df.set_index('label').sort_values(by=['number_of_nodes'], ascending=False)

    def get_relationship_type_statistics(self):
        data = []
        for r_type in self.relationship_types:
            data.append((r_type, self.get_number_of_edges(edge=Edge(r_type))))
        df = pd.DataFrame(data, columns=['type', 'number_of_relationships'])
        return df.set_index('type').sort_values(by=['number_of_relationships'], ascending=False)

    def get_label_statistics(self):
        data = []
        for label in self.node_labels:
            data.append((label, self.get_number_of_nodes(node=Node(label))))
        df = pd.DataFrame(data, columns=['label', 'number_of_nodes'])
        return df.set_index('label').sort_values(by=['number_of_nodes'], ascending=False)

    def get_number_of_edges(self, edge: Optional[Edge] = None) -> int:
        where, label = "", ""
        if edge:
            where_str = edge.get_where("e")
            where = f" WHERE {where_str}" if where_str else ""
            label = f":`{edge.cypher_labels}`"
        cypher = f"MATCH ()-[e{label}]->() {where} RETURN count(e) AS num" ""
        return self.execute(cypher)[0]["num"]

    @property
    def node_labels(self) -> list[str]:
        """Returns list of all node labels

        Returns
        -------
        List[str]
            List of all node labels
        """
        return [x["label"] for x in self.execute("CALL db.labels() YIELD label")]

    @property
    def relationship_types(self) -> list[str]:
        """Returns list of all edge/relationship types

        Returns
        -------
        List[str]
            List of all edge/relationship types
        """
        return [x['relationshipType'] for x in self.execute("CALL db.relationshipTypes")]

    def create_node_index(
            self, label: str, prop_name: str, index_name: Optional[str] = None
    ):
        """Create an index for a given node label on a specific property."""
        if index_name is None:
            index_name = f"ix_{label}__{prop_name}"
        cypher = f"CREATE INDEX {index_name} IF NOT EXISTS FOR (p:{label}) ON (p.{prop_name})"
        return self.session.run(cypher)

    def create_edge_index(
            self, label: str, prop_name: str, index_name: Optional[str] = None
    ):
        if index_name is None:
            index_name = f"ix_{label}__{prop_name}"
        cypher = f"CREATE INDEX {index_name} IF NOT EXISTS FOR ()-[k:{label}]-() ON (k.{prop_name})"
        return self.session.run(cypher)

    def drop_node_index(self, index_name: str):
        cypher = f"DROP INDEX {index_name} IF EXISTS"
        return self.session.run(cypher)

    def create_unique_constraint(
            self, label: str, prop_name: str, constraint_name: Optional[str] = None
    ):
        if constraint_name is None:
            constraint_name = f"uid_{label}__{prop_name}"
        cypher = f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop_name} IS UNIQUE"
        return self.session.run(cypher)

    def delete_unique_constraint(
            self, label, prop_name, constraint_name: Optional[str] = None
    ):
        if constraint_name is None:
            constraint_name = f"uid_{label}__{prop_name}"
        cypher = f"DROP CONSTRAINT {constraint_name} IF EXISTS"
        return self.session.run(cypher)
