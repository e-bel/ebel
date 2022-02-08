"""WikiPathways module. Depends on HGNC and KEGG."""
import json
import os
import warnings
import pandas as pd
import rdflib
from sqlalchemy import select

from tqdm import tqdm
from pathlib import Path
from rdflib import Graph
from typing import Dict
from zipfile import ZipFile
from pyorient import OrientDB

from ebel.constants import RID, DATA_DIR
from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import WIKIPATHWAYS
from ebel.manager.orientdb import odb_meta, urls, odb_structure
from ebel.manager.rdbms.models.wikipathways import Node, Interaction, PublicationReference, Base, Pathway
from ebel.manager.models import reset_tables


warnings.filterwarnings("ignore", 'This pattern has match groups')

NODES = "nodes"
INTERACTIONS = "interactions"
PUBREFS = "pubrefs"
PATHWAYS = "pathways"

# WikiPathway Type Mapper
wp_mapper = {
    # Nodes
    "Metabolite": "abundance",
    "Complex": "complex",
    "Protein": "protein",
    "Rna": "rna",
    "GeneProduct": "gene",
    # Interactions
    "TranscriptionTranslation": "increases",
    "Stimulation": "increases",
    "Catalysis": "increases",
    "Inhibition": "decreases",
    "Conversion": "increases",
    "DirectedInteraction": "association"
}

class WikiPathways(odb_meta.Graph):
    """Pathway Commons."""

    def __init__(self, client: OrientDB = None):
        """Init Pathway Commons."""
        self.client = client
        self.biodb_name = WIKIPATHWAYS
        self.url = urls.WIKIPATHWAYS
        self.urls = {self.biodb_name: self.__get_current_data_download_path()}
        self.file_path = get_file_path(self.urls[self.biodb_name], self.biodb_name)

        super().__init__(
            # generics=odb_structure.wikipathways_generics,
            # edges=odb_structure.wikipathways_edges,
            urls=self.urls,
            biodb_name=self.biodb_name,
            tables_base=Base,
        )

    def __repr__(self) -> str:
        """Represent WikiPathways Integration as string."""
        template = "{{BioDatabase:WikiPathways}}[url:{url}, edges:{edges}, nodes:{generics}]"
        representation = template.format(
            url=self.url,
            edges=self.number_of_edges,
            generics=self.number_of_generics
        )
        return representation

    def __contains__(self, rs_number: int) -> bool:
        """Checks if RS number (without prefix RS) exists in BEL graph."""
        return self.entry_exists(self.biodb_name, rs_number=rs_number)

    def __get_current_data_download_path(self):
        """Read the WikiPathways Data website and get file names for current data dumps."""
        current_files_df = pd.read_html(self.url)[0]
        for file_name in current_files_df.Filename:
            if file_name.endswith("-rdf-wp.zip"):
                return self.url + file_name

    @staticmethod
    def parse_pubrefs(wikipathway: rdflib.Graph) -> dict:
        """Parse and import PublicationReference data from graph."""
        pubref_query = """
        SELECT ?id ?data_source ?data_source_id ?link
            WHERE {
                ?id rdf:type wp:PublicationReference ;
                    rdf:type ?type .
                    ?id foaf:page ?link .
                    ?id dc:source ?data_source .
                    ?id dcterms:identifier ?data_source_id .
            }
        """

        pubrefs = dict()
        for match in wikipathway.query(pubref_query):
            result_dict = {key: str(val) for key, val in match.asdict().items()}
            pubrefs[result_dict["id"]] = result_dict

        return pubrefs

    @staticmethod
    def parse_pathways(wikipathway: rdflib.Graph) -> dict:
        """Parse and import Pathway data from graph."""
        pathway_query = """
        SELECT ?id ?data_source ?data_source_id ?description ?organism
            WHERE {
                ?id rdf:type wp:Pathway .
                ?id rdf:type ?type .
                ?id dc:source ?data_source .
                ?id dcterms:identifier ?data_source_id .
                OPTIONAL {
                    ?id dcterms:description ?description .
                    ?id wp:organismName ?organism . 
                }
            FILTER (STR(?type) = "http://vocabularies.wikipathways.org/wp#Pathway") .
            }
        """

        pathways = dict()
        for match in wikipathway.query(pathway_query):
            result_dict = {key: str(val) for key, val in match.asdict().items()}
            pathways[result_dict["id"]] = result_dict

        return pathways

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class."""
        db_dir = Path(DATA_DIR, self.biodb_name)
        ttl_dir = db_dir.joinpath("wp", "Human")

        if not ttl_dir.is_dir() or not any(ttl_dir.iterdir()):  # If folder is empty
            with ZipFile(self.file_path) as zf:
                for file_name in zf.namelist():
                    if file_name.startswith("wp/Human"):
                        zf.extract(member=file_name, path=db_dir)

        entries = self.parse_rdf_files(directory=ttl_dir)
        return entries

    def import_data(self, entries: dict) -> dict:
        """Import data into tables."""
        model_mapper = {PATHWAYS: Pathway, PUBREFS: PublicationReference, INTERACTIONS: Interaction, NODES: Node}
        for node_type in (PATHWAYS, PUBREFS):
            model = model_mapper[node_type]
            for wp_id, metadata in entries[node_type].items():
                new_table_row = model(**metadata)

                if node_type == NODES:
                    # new_node.pathways = _  # TODO add pathway links by parsing dcterms:isPartOf
                    pass

                self.session.add(new_table_row)
                entries[node_type][wp_id]["table_obj"] = new_table_row

        self.session.commit()
        return entries

    def parse_rdf_files(self, directory: Path) -> dict:
        """Wrapper function for parsing individual TTL files."""
        entries = {NODES: dict(), INTERACTIONS: dict(), PUBREFS: dict(), PATHWAYS: dict()}
        for ttl_file in tqdm(directory.iterdir(),
                             desc="Parsing WikiPathway files",
                             total=len(os.listdir(str(directory)))):
            graph = Graph()
            wp = graph.parse(ttl_file)
            entries[NODES] = {**entries[NODES], **self.parse_nodes(wikipathway=wp)}
            entries[INTERACTIONS] = {**entries[INTERACTIONS], **self.parse_interactions(wikipathway=wp)}
            entries[PUBREFS] = {**entries[PUBREFS], **self.parse_pubrefs(wikipathway=wp)}
            entries[PATHWAYS] = {**entries[PATHWAYS], **self.parse_pathways(wikipathway=wp)}

        return entries

    def parse_nodes(self, wikipathway: rdflib.Graph) -> dict:
        """Query and parse nodes."""
        noncomplex_node_query = """
            SELECT ?wp_id (GROUP_CONCAT(?type;SEPARATOR=",") AS ?types) ?label ?id_source ?identifier
            WHERE {
                ?wp_id rdf:type wp:DataNode ;
                    rdf:type ?type .
                    ?wp_id rdfs:label ?label .
                    ?wp_id dc:source ?id_source .
                    ?wp_id dcterms:identifier ?identifier .
            }
            GROUP BY ?wp_id
        """

        # Need a separate query for complexes because using 2 GROUP_CONCATs where one is optional = missing results
        complex_node_query = """
            SELECT ?wp_id ?types (GROUP_CONCAT(?ps ;SEPARATOR=",") AS ?participants)
            WHERE {
                ?wp_id rdf:type wp:Complex ;
                    rdf:type ?types ;
                    wp:participants ?ps .
            FILTER (STR(?type) = "http://vocabularies.wikipathways.org/wp#Complex") .
            }
            GROUP BY ?wp_id
        """

        noncomplex_nodes = self.__format_node_metadata(wikipathway=wikipathway, query=noncomplex_node_query)
        complex_nodes = self.__format_node_metadata(wikipathway=wikipathway, query=complex_node_query)
        nodes = {**noncomplex_nodes, **complex_nodes}
        return nodes

    @staticmethod
    def __format_node_metadata(wikipathway: rdflib.Graph, query: str) -> dict:
        """Parse nodes in the wikipathway graph."""
        nodes = dict()
        query_results = wikipathway.query(query)
        for match in query_results:
            result_dict = {key: str(val) for key, val in match.asdict().items()}
            node_types = {int_type.split("#")[1] for int_type in result_dict.pop("types").split(",")}

            # AOP nodes only have "DataNode" type
            if "id_source" in result_dict and result_dict["id_source"].startswith("AOP-Wiki"):
                node_types.add("AOP-Wiki")

            # don't need "DataNode" since it's a duplicate
            node_types.remove('DataNode')

            # Defensive code
            if len(node_types) != 1:  # Should only be one node type
                raise ValueError(f"Too many node types: {node_types}")

            # Parse participants of wp:Complex nodes if present, Reactome complexes sometimes don't have participants
            if "Complex" in node_types and "participants" in result_dict:
                result_dict["participants"] = set(result_dict["participants"].split(","))

            result_dict["type"] = list(node_types)[0]

            wp_id = result_dict["wp_id"]
            nodes[wp_id] = result_dict

        return nodes

    @staticmethod
    def parse_interactions(wikipathway: rdflib.Graph) -> dict:
        """Parse interactions in the wikipathway graph."""
        # Get and parse edges
        # ";" can be used when same subj/pred/obj used - https://www.stardog.com/tutorials/sparql#ordering-results
        # OPTIONAL is used for ComplexBinding interactions - they don't have source/target
        int_q = """
            SELECT ?wp_id (GROUP_CONCAT(?type;SEPARATOR=",") AS ?types) ?source ?target ?identifier (GROUP_CONCAT(?ps ;SEPARATOR=",") AS ?participants)
            WHERE {
                ?wp_id rdf:type wp:Interaction ;
                    wp:participants ?ps ;
                    rdf:type ?type .
                OPTIONAL {
                    ?wp_id wp:source ?source .
                    ?wp_id wp:target ?target .
                }
            }
            GROUP BY ?wp_id
        """

        interactions = dict()
        for match in wikipathway.query(int_q):
            result_dict = {key: str(val) for key, val in match.asdict().items()}
            result_dict["types"] = {int_type.split("#")[1] for int_type in result_dict["types"].split(",")}
            result_dict["participants"] = set(result_dict["participants"].split(","))

            # don't need "Interaction"
            result_dict["types"].remove("Interaction")

            # Binding always with ComplexBinding so keep only ComplexBinding
            if "ComplexBinding" in result_dict["types"]:
                result_dict["types"] = {"ComplexBinding"}

            wp_id = result_dict["wp_id"]
            interactions[wp_id] = result_dict

        return interactions

    def update_interactions(self) -> int:
        pass

if __name__ == "__main__":
    wp = WikiPathways()
    reset_tables(engine=wp.engine, force_new_db=False)
    wp.insert_data()
