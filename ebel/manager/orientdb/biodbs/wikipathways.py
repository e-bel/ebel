"""WikiPathways module. Depends on HGNC and KEGG."""

import logging
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
from ebel.manager.orientdb.constants import WIKIPATHWAYS, PARTICIPANTS
from ebel.manager.orientdb import odb_meta, urls, odb_structure
from ebel.manager.rdbms.models.wikipathways import Node, Interaction, PublicationReference, Base, Pathway
from ebel.manager.models import reset_tables


warnings.filterwarnings("ignore", 'This pattern has match groups')

logger = logging.getLogger(__name__)

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
        updated_entries = self.__import_data(entries)
        return updated_entries

    def __import_data(self, entries: dict) -> dict:
        """Import data into tables."""
        logger.info("Importing WikiPathways")
        model_mapper = {PATHWAYS: Pathway, PUBREFS: PublicationReference, NODES: Node, INTERACTIONS: Interaction}
        for node_type, model in model_mapper.items():
            for wp_id, metadata in entries[node_type].items():
                if node_type == INTERACTIONS:  # Map participant IDs to objects
                    if metadata[PARTICIPANTS]:
                        metadata[PARTICIPANTS] = [
                            entries[NODES][wp_id]["table_obj"] for wp_id in metadata[PARTICIPANTS]
                        ]

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
        logger.info("Parsing Wikipathways RDF files")
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

    def parse_nodes(self, wikipathway: rdflib.Graph) -> dict:
        """Query and parse nodes."""
        noncomplex_node_query = """
            SELECT ?id (GROUP_CONCAT(?type;SEPARATOR=",") AS ?types) ?label ?data_source ?data_source_id
            WHERE {
                ?id rdf:type wp:DataNode ;
                    rdf:type ?type .
                    ?id rdfs:label ?label .
                    ?id dc:source ?data_source .
                    ?id dcterms:identifier ?data_source_id .
            }
            GROUP BY ?id
        """

        # Need a separate query for complexes because using 2 GROUP_CONCATs where one is optional = missing results
        complex_node_query = """
            SELECT ?id ?types (GROUP_CONCAT(?ps ;SEPARATOR=",") AS ?participants)
            WHERE {
                ?id rdf:type wp:Complex ;
                    rdf:type ?types ;
                    wp:participants ?ps .
            FILTER (STR(?types) = "http://vocabularies.wikipathways.org/wp#Complex") .
            }
            GROUP BY ?id
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
            if "data_source" in result_dict and result_dict["data_source"].startswith("AOP-Wiki"):
                node_types.add("AOP-Wiki")

            # Don't need "DataNode" since it's redundant
            if "DataNode" in node_types:
                node_types.remove("DataNode")

            # Defensive code
            if len(node_types) != 1:  # Should only be one node type
                raise ValueError(f"Too many node types: {node_types}")

            # Parse participants of wp:Complex nodes if present, Reactome complexes sometimes don't have participants
            if "Complex" in node_types and PARTICIPANTS in result_dict:
                result_dict[PARTICIPANTS] = list(set(result_dict[PARTICIPANTS].split(",")))
                # TODO parse participants
                result_dict.pop(PARTICIPANTS)

            result_dict["type"] = list(node_types)[0]

            wp_id = result_dict["id"]
            nodes[wp_id] = result_dict

        return nodes

    @staticmethod
    def parse_interactions(wikipathway: rdflib.Graph) -> dict:
        """Parse interactions in the wikipathway graph."""
        # Get and parse edges
        # ";" can be used when same subj/pred/obj used - https://www.stardog.com/tutorials/sparql#ordering-results
        # OPTIONAL is used for ComplexBinding interactions - they don't have source/target
        int_q = """
            SELECT ?id (GROUP_CONCAT(?type;SEPARATOR=",") AS ?types) ?source_id ?target_id (GROUP_CONCAT(?ps ;SEPARATOR=",") AS ?participants)
            WHERE {
                ?id rdf:type wp:Interaction ;
                    wp:participants ?ps ;
                    rdf:type ?type .
                OPTIONAL {
                    ?id wp:source ?source_id .
                    ?id wp:target ?target_id .
                }
            }
            GROUP BY ?id
        """

        interactions = dict()
        for match in wikipathway.query(int_q):
            result_dict = {key: str(val) for key, val in match.asdict().items()}
            edge_types = result_dict.pop("types")
            edge_types = list({int_type.split("#")[1] for int_type in edge_types.split(",")})

            result_dict[PARTICIPANTS] = list(set(result_dict[PARTICIPANTS].split(",")))

            # Source/Target/Participants can include other interactions - remove them for now
            # TODO add support for interactions with other other interactions as sources/targets
            for key in ("source_id", "target_id"):
                if key in result_dict and "/Interaction/" in result_dict[key]:  # All Interaction identifiers have "/Interaction/"
                    result_dict.pop(key)  # Remove it

            result_dict[PARTICIPANTS] = [wp_id for wp_id in result_dict[PARTICIPANTS] if "/Interaction/" not in wp_id]

            # don't need "Interaction" if there are other types
            if len(edge_types) != 1:
                edge_types.remove("Interaction")

            # Binding always with ComplexBinding so keep only ComplexBinding
            if "ComplexBinding" in edge_types:
                edge_types = ["ComplexBinding"]

            # Only need DirectedInteraction if there are no better types present
            if "DirectedInteraction" in edge_types and len(edge_types) > 1:
                edge_types.remove("DirectedInteraction")

            if len(edge_types) != 1:
                raise ValueError(f"Too many edge types: {edge_types}")

            wp_id = result_dict["id"]
            result_dict["type"] = edge_types[0]
            interactions[wp_id] = result_dict

        return interactions

    def update_interactions(self) -> int:
        pass

if __name__ == "__main__":
    wp = WikiPathways()
    Base.metadata.drop_all(bind=wp.engine)
    Base.metadata.create_all(bind=wp.engine)
    wp.update()
