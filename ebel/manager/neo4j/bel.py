import logging
from pathlib import Path
from typing import Iterable, Union

from tqdm import tqdm

from ebel.manager.constants import bel_func_short
from ebel.manager.neo4j.n4j_importer import Neo4jImporter
from ebel.manager.neo4j.n4j_meta import Neo4jClient, Edge, Node
from ebel.manager.neo4j.n4j_structure import ABSTRACT_LABELS

logger = logging.getLogger(__name__)


class Neo4jBel:

    def __init__(self, client: Neo4jClient):
        self.client = client

    def import_json(
            self,
            input_path: Union[str, Iterable[str], Path, Iterable[Path]],
            extend_graph: bool = True,
            update_from_protein2gene: bool = True,
            skip_drugbank: bool = False,
            drugbank_user: str = None,
            drugbank_password: str = None,
            include_subfolders: bool = False

    ) -> list:
        """Import BEL JSON file(s) into OrientDB.

        Parameters
        ----------
        input_path: Iterable or str
            A directory containing BEL JSON files, a single BEL JSON file, or a list of JSON files.
        extend_graph: bool (optional)
            If True, enriches the BEL network after importing. Defaults to True.
        update_from_protein2gene: bool (optional)
            Recursively generates RNA nodes and gene nodes for all protein nodes if none exist. Defaults to True.
        include_subfolders: bool
            Boolean flag to indicate whether to traverse subfolders for BEL files.
        skip_drugbank: bool (optional)
            Flag to disable DrugBank update.
        drugbank_user: str (optional)
            DrugBank user name.
        drugbank_password: str (optional)
            DrugBank password.

        Returns
        -------
        list
            List of files imported
        """
        inserted_files = []
        bel_json_ext = "*.bel.json"

        # if not skip_drugbank:
        #     self.drugbank.get_user_passwd(drugbank_user=drugbank_user, drugbank_password=drugbank_password)

        if not isinstance(input_path, list):

            if isinstance(input_path, str):
                input_path = Path(input_path)

            if input_path.is_dir():  # If directory, get a list of all files there
                if include_subfolders:
                    files_to_import = [f for f in input_path.rglob(bel_json_ext)]

                else:
                    files_to_import = [f for f in input_path.glob(bel_json_ext)]

            else:
                files_to_import = [input_path]

        else:  # It is a list
            files_to_import = [Path(fp) for fp in input_path]

        for path in files_to_import:
            if path.is_file():
                logger.info(f"Begin import: {path.name}")

                try:
                    importer = Neo4jImporter(path, self.client)
                    edges_inserted, number_inserted = importer.insert()
                    if edges_inserted:
                        logger.info(f"{path.name} successfully imported")
                        inserted_files.append(path)

                except:
                    logger.error(f"{path} failed to be imported", exc_info=True)

        if inserted_files:
            self._create_and_tag_pure()
            # self.update_document_info()

            if update_from_protein2gene:
                self._update_from_protein2gene()

            # self._update_involved()
            #
            # if extend_graph:
            #     db_skip = [DRUGBANK] if skip_drugbank else []
            #     self.enrich_network(skip=db_skip)
            #
            # self._update_species()
            # self._update_involved()

        return inserted_files

    def _update_from_protein2gene(self) -> dict[str, int]:
        """Adds translated_to and transcribed_to to pure=true proteins and RNAs if not exists."""
        added_translated_to = self._add_missing_translated_to_edges()
        added_transcribed_to = self._add_missing_transcribed_to_edges()
        return {'added_translated_to': added_translated_to, 'added_transcribed_to': added_transcribed_to}

    def _add_missing_translated_to_edges(self) -> int:
        """Add missing RNAs to proteins and translated_to edges."""
        return self.__add_missing_edges(
            from_class='Rna',
            to_class='Protein',
            edge_name='TRANSLATED_TO',
            bel_function='r')

    def _add_missing_transcribed_to_edges(self) -> int:
        """Add missing genes to RNAs and transcribed_to edges."""
        return self.__add_missing_edges(
            from_class='Gene',
            to_class='Rna',
            edge_name='TRANSCRIBED_TO',
            bel_function='g')

    def __add_missing_edges(self, from_class, to_class, edge_name, bel_function) -> int:
        added = 0
        cypher = f"""MATCH (obj:{to_class} {{pure: true}})
WHERE NOT EXISTS((:{from_class})-[:{edge_name}]->(obj))
RETURN elementId(obj) as obj_id, obj.name as obj_name, obj.namespace as obj_namespace"""

        results = self.client.execute(cypher)

        for entry in tqdm(results, desc=f"Adding {edge_name} edges"):
            ns, name = entry["obj_namespace"], entry["obj_name"]
            bel = f'{bel_function}({ns}:"{name}")'

            subj_node = Node(labels=from_class, props={'namespace': ns, 'name': name, 'pure': True, 'bel': bel})
            subj_node_id = self.client.merge_node(node=subj_node)

            self.client.merge_edge_by_node_ids(subj_id=subj_node_id, rel=Edge(labels=edge_name), obj_id=entry["obj_id"])
            added += 1

        return added

    def _create_and_tag_pure(self):
        """Create pure gene, RNA, micro_rna, abundance, complex (as abundance) and protein objects (if not exists).

        Tag all these objects as pure.

        Strategy:
        1. Identify all above mentioned objects with a edges listed below
        2. Check for each object if pure counterpart object exists
        3. If 2=No -> create pure counterpart object
        3. create edge between pure and "modified" objects


        Check for the following modifications (edges):
        out:
        - has__fragment
        - has__variant
        - has__pmod
        - has__location
        in:
        - has_variant
        """
        self._tag_pure()
        self._create_pure_nodes_to_modified()

    def _tag_pure(self) -> int:
        """Tag pure all objects."""
        cypher = """MATCH (n:Protein|Gene|Rna|Abundance|Complex|MicroRna)
WHERE NOT (n)-[:HAS__FRAGMENT|HAS__VARIANT|HAS__PMOD|HAS__GMOD|HAS__LOCATION]->()
SET n.pure = true RETURN count(n) as num_pure"""
        return self.client.execute(cypher)[0]["num_pure"]

    def _create_pure_nodes_to_modified(self) -> int:
        """Create all has_modified_(protein|gene) edges in OrientDB (proteins without a pure counterpart)."""
        edge_classes = {'HAS__PMOD': "HAS_MODIFIED_PROTEIN",
                        'HAS__GMOD': "HAS_MODIFIED_GENE",
                        'HAS__FRAGMENT': "HAS_FRAGMENTED_PROTEIN",
                        'HAS__VARIANT': "HAS_VARIANT_{}",
                        'HAS__LOCATION': "HAS_LOCATED_{}"}

        cypher = f"""MATCH (subj)-[r:{'|'.join(edge_classes.keys())}]->()
RETURN elementId(subj) as node_id, labels(subj) as node_classes, subj.name as node_name, subj.namespace as node_ns,
type(r) as edge_class"""

        results = self.client.execute(cypher)

        created = 0
        for row in tqdm(results, desc="Add edges to pure nodes"):
            obj_id = row["node_id"]
            node_namespace = row['node_ns']
            node_name = row['node_name']
            node_classes = row['node_classes']

            node_class = [x for x in node_classes if x not in ABSTRACT_LABELS][0]  # Should only have 1 non-abstract

            edge_class = row["edge_class"]
            class_name_from_pure = edge_classes[edge_class]

            if '{}' in class_name_from_pure:
                cname_from_pure = class_name_from_pure.format(node_class.upper())

            else:
                cname_from_pure = class_name_from_pure

            bel_function = bel_func_short[node_class]
            bel = f'{bel_function}({node_namespace}:"{node_name}")'

            data = {
                'namespace': node_namespace,
                'name': node_name,
                'pure': True,
                'bel': bel
            }

            subj = Node(labels=set(node_classes), props=data)
            subj_id = self.client.merge_node(node=subj)

            merge_edge = Edge(labels=cname_from_pure)

            self.client.merge_edge_by_node_ids(
                subj_id=subj_id,
                rel=merge_edge,
                obj_id=obj_id,
            )
            created += 1

        return created


if __name__ == "__main__":
    n4j = Neo4jClient("bolt://localhost:7687", user="neo4j", password="password")
    n4j.delete_everything()

    b = Neo4jBel(client=n4j)
    b.import_json(input_path="F:\\scai_git\\bms\\parkinsons.bel.json",)
