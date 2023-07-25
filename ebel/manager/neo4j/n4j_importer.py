"""Import an eBEL generated JSON file into Neo4j."""

import re
import json
import logging

from collections import defaultdict
from tqdm import tqdm

from ebel.manager.constants import normalized_pmod, bel_func_short, NODES, EDGES
from ebel.manager.neo4j.n4j_structure import node_map, edge_map
from ebel.manager.neo4j.n4j_meta import Neo4j, Node, Edge

logger = logging.getLogger(__name__)

n4j = Neo4j(uri="bolt://localhost:7687", user="neo4j", password="password")


class Neo4jImporter:
    """Importer for Neo4j."""

    def __init__(self, file_path, n4j_client: Neo4j = None):
        """Insert statements and sets from BEL JSON file."""
        self.client = n4j_client
        self.file_path = file_path

        self._cache = {
            NODES: self.get_node_cache(),
            EDGES: self.get_relation_cache(),
        }

    def get_node_cache(self):
        """Get all nodes in the database."""
        cypher = "MATCH (n) RETURN ID(n) AS node_id, labels(n) as labels, n.bel as bel"
        nodes = self.client.execute(cypher)
        node_cache = {(n["bel"], ":".join(sorted(n["labels"]))): n["node_id"] for n in nodes}
        return node_cache

    def get_relation_cache(self):
        """Get all relations in the database."""
        rel_cache = {}

        cypher = """MATCH ()-[r]-() RETURN 
ID(startNode(r)) as subject_id, ID(endNode(r)) as object_id, 
TYPE(r) as relation, ID(r) as rel_id, r.evidence as evidence, r.annotation as annotation"""

        rels = self.client.execute(cypher)
        for entry in rels:
            rel_id = entry.pop("rel_id")
            rel_key = tuple(entry.values())
            rel_cache[rel_key] = rel_id

        return rel_cache

    def insert(self) -> int:
        """Insert JSON file into Neo4j."""
        with open(self.file_path) as fd:
            bel_python_object = json.load(fd)

        if not bel_python_object:  # May be empty JSON
            logger.warning(f"{self.file_path} is empty")
            return 0

        document, definitions, stmts_and_sets = bel_python_object

        inserted = self.insert_statements_and_sets(stmts_and_sets['statements_and_sets'])

        return inserted

    def insert_statements_and_sets(self, statements_and_sets: dict) -> int:
        """Insert statement and sets."""
        citation = {}
        evidence = ""
        annotation = defaultdict(set)
        pmid = 0
        citation_ref = ""
        citation_type = ""

        for e in tqdm(statements_and_sets, desc="Insert BEL Statements"):

            dtype, data = tuple(e.items())[0]

            if dtype == "sets":
                for bel_set in data:
                    key, value = tuple(bel_set.items())[0]

                    if key == "citation":
                        citation = dict(value)
                        citation_type = citation['type'].strip()
                        citation_ref = citation['ref'].strip()
                        evidence = ""
                        annotation = defaultdict(set)

                        if citation['type'].lower() == "pubmed" and re.search(r'^\d+$', citation_ref):
                            pmid = citation_ref
                        else:
                            pmid = 0

                    elif key == "evidence":
                        evidence = re.sub(r"\s*\\\s*\n\s*", " ", value)

                    elif key == "set":
                        anno_keyword, anno_entries = tuple(value.items())[0]
                        annotation[anno_keyword] = set(anno_entries)

                    elif key == "unset":
                        for anno_keyword in value:
                            annotation.pop(anno_keyword, None)

            elif dtype == "statement" and len(data) >= 1:

                _, subj_class, subject_id = self.get_node_id(data[0]['subject'])

                if len(data) > 1 and 'object' in data[2]:
                    # TODO: nested statements are missing

                    _, obj_class, object_id = self.get_node_id(data[2]['object'])

                    relation = data[1]['relation']
                    neo4j_relation_class = edge_map[relation]

                    self.insert_bel_edge(annotation, citation, citation_ref, citation_type, evidence, object_id, pmid,
                                         neo4j_relation_class, subject_id, subj_class, obj_class)

        return len(statements_and_sets)

    @staticmethod
    def format_prop(prop_name: str, prop: dict) -> str:
        """Format property dictionary to be Neo4j compliant."""
        formatted_prop = ""
        if prop:
            for key, value in prop.items():
                suffix = "".join([stem.capitalize() for stem in key.split("_")])  # foo_bar -> FooBar

                if value:
                    if isinstance(value, str):
                        new_add = f'{prop_name}{suffix}: "{value}"'

                    elif isinstance(value, set):
                        new_add = f"{prop_name}{suffix}: {list(value)}"

                    else:
                        new_add = f"{prop_name}{suffix}: {value}"

                    if formatted_prop:
                        formatted_prop += f", {new_add}"

                    else:  # If empty, don't add ", "
                        formatted_prop += new_add

        return formatted_prop

    def insert_bel_edge(
            self,
            annotation: dict,
            citation: dict,
            citation_ref: str,
            citation_type: str,
            evidence: str,
            object_id: int,
            pmid: int,
            relation: str,
            subject_id: int,
            subject_class: str,
            object_class: str,
    ):

        form_anno = self.format_prop(prop_name="annotation", prop=annotation)
        form_citation = self.format_prop(prop_name="citation", prop=citation)

        # TODO: check if relation already exists
        anno = {key: sorted(list(annotation[key])) for key in annotation.keys()}
        anno_json = json.dumps(anno, sort_keys=True)

        # Need to clean the properties
        evidence = evidence.replace('\n', ' ')
        citation_ref = citation_ref if citation_ref else None
        citation_type = citation_type if citation_type else None

        edge_profile = (relation, subject_id, object_id, citation_type, citation_ref, evidence, anno_json)
        edge_exists = True if edge_profile in self._cache[EDGES] else False

        edge_props = f'pmid: {pmid}, evidence: "{evidence}"'
        if form_citation:
            edge_props += f", {form_citation}"

        if form_anno:
            edge_props += f", {form_anno}"

        if not edge_exists:
            cypher = f"""MATCH (subj:{subject_class}), (obj:{object_class}) 
WHERE id(subj) = {subject_id} AND id(obj) = {object_id}
CREATE (subj)-[r:{relation} {{{edge_props}}}]->(obj) 
RETURN id(r) as rel_id"""

            record = self.client.execute(cypher)
            self._cache[EDGES][edge_profile] = record[0]["rel_id"]

    @staticmethod
    def is_function(obj) -> bool:
        return isinstance(obj, dict) and 'function' in obj

    def get_node_id_from_cache(self, obj, bel: str):
        """Return @rid if node exists."""
        node_id = None
        neo4j_class = None

        if isinstance(obj[0], dict) and 'function' in obj[0]:
            node_class = obj[0]['function']['name']
            neo4j_class = node_map[node_class]
            if (bel, neo4j_class) in self._cache[NODES]:
                node_id = self._cache[NODES][(bel, neo4j_class)]

        return neo4j_class, node_id

    def insert_bel_node(self, node_class, params: dict, bel: str):
        """Insert bel node, return node ID."""
        params["bel"] = bel

        node_labels = set(node_class.split(":"))
        new_node = Node(labels=node_labels, props=params)
        new_node_id = self.client.create_node(new_node)

        self._cache[NODES][(bel, node_class)] = new_node_id
        return new_node_id

    def get_node_id(self, obj: list) -> tuple[str, str, int]:
        """Return node id of obj."""
        if not isinstance(obj, list):
            raise TypeError(f"Expecting list, but get {type(obj)} for {obj}")

        inserted_nodes = []
        params = {}

        bel = self.get_bel(obj)

        node_class = obj[0]['function']['name']
        neo4j_class = node_map[node_class]

        if node_class not in ['pmod', 'fragment', 'variant']:
            neo4j_class, node_id = self.get_node_id_from_cache(obj, bel)
            if node_id:
                return node_class, neo4j_class, node_id

        [params.update(x) for x in obj[1] if isinstance(x, dict)]

        for e in obj[1]:
            if isinstance(e, list):
                if self.is_function(e[0]):
                    inserted_nodes += [self.get_node_id(e)]
                else:
                    for f in e:
                        inserted_nodes += [self.get_node_id(f)]

        node_id = self.insert_bel_node(neo4j_class, params, bel)

        for child_class, child_neo4j_class, child_node_id in inserted_nodes:
            cypher = f"""MATCH ()-[r:HAS__{child_class.upper()}]->() 
WHERE id(startNode(r)) = {node_id} AND id(endNode(r)) = {child_node_id} RETURN r"""

            exists = self.client.execute(cypher)
            if not exists:
                new_edge_cypher = f"""MATCH (subj:{neo4j_class}), (obj:{child_neo4j_class}) 
WHERE id(subj) = {node_id} AND id(obj) = {child_node_id}
CREATE (subj)-[r:HAS__{child_class.upper()}]->(obj) RETURN r"""
                self.client.execute(new_edge_cypher)

        return node_class, neo4j_class, node_id

    @staticmethod
    def get_bel_string(params, function_name=None):
        """Get BEL formatted string."""
        bels = []

        for param in params:
            if isinstance(param, str):
                bels.append(param)

            elif isinstance(param, dict):
                if set(param.keys()) == {'namespace', 'name'}:
                    bels.append(param['namespace'] + ':"' + param['name'] + '"')

                elif function_name == "fragment":
                    bels.append(','.join(['"' + x + '"' for x in param.values() if x]))

                elif function_name == "activity":
                    if param['namespace']:
                        bel_str = param['namespace'] + ':"' + param['name'] + '"'
                    else:
                        bel_str = param['default']
                    bels.append("ma(" + bel_str + ")")

                elif function_name == "pmod":
                    if param['namespace']:
                        first_part_pmod = param['namespace'] + ':"' + param['name'] + '"'
                    else:
                        first_part_pmod = normalized_pmod[param['type']]
                    position = str(param['position']) if param['position'] else None
                    parts_pmod = [first_part_pmod, param['amino_acid'], position]
                    bels.append(",".join([x for x in parts_pmod if x]))

                else:
                    bels.append(','.join(['"' + str(x) + '"' for x in param.values() if x]))

        joined_params = ",".join(bels)

        if function_name:
            return bel_func_short[function_name] + "(" + joined_params + ")"

        else:
            return joined_params

    def get_bel(self, obj, parent_function=None):
        """Return BEL by python object loaded from JSON."""
        params = []
        function_name = None

        for element in obj:

            if isinstance(element, dict):

                if 'function' in element:
                    function_name = element['function']['name']

                else:
                    params.append(element)

            elif isinstance(element, list):
                params.append(self.get_bel(element, function_name))

        return self.get_bel_string(params, parent_function)


if __name__ == "__main__":
    n4j.delete_everything()
    a = Neo4jImporter(file_path="F:\\scai_git\\bms\\alzheimers.bel.json", n4j_client=n4j)
    a.insert()
