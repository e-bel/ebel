"""Import an eBEL generated JSON file into Neo4j."""

import re
import json
import logging
import traceback

from collections import defaultdict
from tqdm import tqdm

from ebel.manager.constants import normalized_pmod, bel_func_short, NODES, EDGES
from ebel.manager.neo4j.n4j_structure import node_map, edge_map
from ebel.manager.neo4j.n4j_meta import Neo4jClient, Node, Edge

logger = logging.getLogger(__name__)


class Neo4jImporter:
    """Importer for Neo4j."""

    def __init__(self, file_path, n4j_client: Neo4jClient = None):
        """Insert statements and sets from BEL JSON file."""
        self.client = n4j_client
        self.file_path = file_path

        self._cache = {
            NODES: self.get_node_cache(),
            EDGES: self.get_relation_cache(),
        }

    def get_node_cache(self) -> dict[str, str]:
        """Get all nodes in the database."""
        cypher = "MATCH (n) RETURN elementId(n) AS node_id, n.bel as bel"
        nodes = self.client.execute(cypher)
        node_cache = {n["bel"]: n["node_id"] for n in nodes}
        return node_cache

    def get_relation_cache(self) -> dict[tuple, str]:
        """Get all relations in the database."""
        rel_cache = {}

        cypher = """MATCH ()-[r]->() RETURN 
elementId(startNode(r)) as subject_id, elementId(endNode(r)) as object_id, 
TYPE(r) as relation, elementId(r) as rel_id, r.evidence as evidence"""

        rels = self.client.execute(cypher)
        for entry in rels:
            rel_id = entry.pop("rel_id")
            rel_key = tuple(entry.values())
            rel_cache[rel_key] = rel_id

        return rel_cache

    def insert(self) -> tuple[bool, int]:
        """Insert JSON file into Neo4j."""
        with open(self.file_path) as fd:
            bel_python_object = json.load(fd)

        if not bel_python_object:  # May be empty JSON
            logger.warning(f"{self.file_path} is empty")
            return False, 0

        document, definitions, stmts_and_sets = bel_python_object

        add_edges = self.insert_statements_and_sets(stmts_and_sets['statements_and_sets'])

        return bool(add_edges), add_edges

    def insert_statements_and_sets(self, statements_and_sets: dict) -> int:
        """Insert statement and sets."""
        citation = {}
        evidence = ""
        annotation = defaultdict(set)
        pmid = 0
        citation_ref = ""
        citation_type = ""

        new_edges = 0

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
                try:
                    _, subj_class, subject_id = self.get_node_id(data[0]['subject'])
                    if len(data) > 1 and 'object' in data[2]:
                        # TODO: nested statements are missing
                        #print(data)
                        _, obj_class, object_id = self.get_node_id(data[2]['object'])

                        relation = data[1]['relation']
                        neo4j_relation_class = edge_map[relation]

                        new_edges += self.insert_bel_edge(annotation, citation, evidence, pmid, neo4j_relation_class,
                                                        subject_id, object_id)

                    else:
                        print(data[2])
                        logger.warning(f"The following couldn't be imported {data}")
                        print(data)
                        
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(pmid)
                    print(data)
              
        return new_edges

    @staticmethod
    def format_prop(prop_name: str, prop: dict) -> dict:
        """Format property dictionary to be Neo4j compliant."""
        formatted_props = {}
        if prop:
            for key, value in prop.items():
                suffix = "".join([stem.capitalize() for stem in key.split("_")])  # foo_bar -> FooBar

                if value:
                    if isinstance(value, set):
                        formatted_props[f'{prop_name}{suffix}'] = list(value)

                    else:
                        formatted_props[f'{prop_name}{suffix}'] = value

        return formatted_props

    def insert_bel_edge(
            self,
            annotation: dict,
            citation: dict,
            evidence: str,
            pmid: int,
            relation: str,
            subject_id: str,
            object_id: str,
    ) -> int:
        """Insert BEL edge into Neo4j graph"""
        inserted = 0

        form_anno = self.format_prop(prop_name="annotation", prop=annotation)
        form_citation = self.format_prop(prop_name="citation", prop=citation)

        # TODO: check if relation already exists
        anno = {key: sorted(list(annotation[key])) for key in annotation.keys()}
        anno_json = json.dumps(anno, sort_keys=True)

        # Need to clean the properties
        evidence = evidence.replace('\n', ' ')

        edge_profile = (subject_id, object_id, relation, evidence)
        edge_exists = True if edge_profile in self._cache[EDGES] else False

        # edge_props = f'pmid: {pmid}, evidence: "{evidence}"'
        edge_props = {'pmid': pmid, 'evidence': evidence}
        edge_props.update(form_citation)
        edge_props.update(form_anno)

        if not edge_exists:
            new_edge = Edge(labels=relation, props=edge_props)
            record = self.client.merge_edge_by_node_ids(subj_id=subject_id, rel=new_edge, obj_id=object_id)

            # record = self.client.execute(cypher)
            self._cache[EDGES][edge_profile] = record[0]["rel_id"]
            inserted += 1

        return inserted

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
            if bel in self._cache[NODES]:
                node_id = self._cache[NODES][bel]

        return neo4j_class, node_id

    def insert_bel_node(self, node_class, params: dict, bel: str):
        """Insert bel node, return node ID."""
        params["bel"] = bel

        node_labels = set(node_class.split(":"))
        new_node = Node(labels=node_labels, props=params)
        new_node_id = self.client.merge_node(new_node)

        self._cache[NODES][bel] = new_node_id
        return new_node_id

    def get_node_id(self, obj: list) -> tuple[str, str, str]:
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
WHERE elementId(startNode(r)) = "{node_id}" AND elementId(endNode(r)) = "{child_node_id}" RETURN r"""

            exists = self.client.execute(cypher)
            if not exists:
                new_edge = Edge(labels=f"HAS__{child_class.upper()}")
                self.client.merge_edge_by_node_ids(subj_id=node_id, rel=new_edge, obj_id=child_node_id)

        return node_class, neo4j_class, node_id

    @staticmethod
    def get_bel_string(params, function_name=None) -> str:
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

    def get_bel(self, obj, parent_function=None) -> str:
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
