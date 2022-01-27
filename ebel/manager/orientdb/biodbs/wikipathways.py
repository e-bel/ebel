"""WikiPathways module. Depends on HGNC and KEGG."""

import warnings
import pandas as pd
import rdflib

from tqdm import tqdm
from pathlib import Path
from rdflib import Graph
from typing import Dict
from pyorient import OrientDB

from ebel.constants import RID
from ebel.tools import get_file_path
from ebel.manager.orientdb.biodbs.hgnc import Hgnc
from ebel.manager.orientdb.constants import WIKIPATHWAYS
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import wikipathways


warnings.filterwarnings("ignore", 'This pattern has match groups')


class WikiPathways(odb_meta.Graph):
    """Pathway Commons."""

    def __init__(self, client: OrientDB = None):
        """Init Pathway Commons."""
        self.client = client
        self.biodb_name = WIKIPATHWAYS
        self.url = urls.WIKIPATHWAYS
        self.urls = {self.biodb_name: self.url}
        self.file_path = get_file_path(self.url, self.biodb_name)

        super().__init__(generics=odb_structure.wikipathways_generics,
                         edges=odb_structure.wikipathways_edges,
                         tables_base=pc.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)
        self.hgnc = Hgnc(self.client)

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

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class."""
        pass

    @staticmethod
    def parse_nodes(wikipathway: rdflib.Graph) -> dict:
        """Parse nodes in the wikipathway graph."""
        # ";" can be used when same subj/pred/obj used - https://www.stardog.com/tutorials/sparql#ordering-results
        q = """
            SELECT ?ttl_id ?type ?label ?id_source ?identifier
            WHERE {
                ?ttl_id rdf:type wp:DataNode ;
                    rdfs:label ?label ;
                    dc:source ?id_source ;
                    dcterms:identifier ?identifier ;
                    rdf:type ?type .
            }
        """

        nodes = dict()
        for match in wikipathway.query(q):
            result_dict = {key: str(val) for key, val in match.asdict().items()}
            result_dict["type"] = match.type.split("#")[1]

            # rdf type comes after #, don't need "DataNode" since it's a duplicate

            if result_dict["type"] == "DataNode":
                continue

            ttl_id = result_dict.pop("ttl_id")
            nodes[ttl_id] = result_dict

        return nodes

    @staticmethod
    def parse_interactions(wikipathway: rdflib.Graph, nodes: dict) -> dict:
        """Parse interactions in the wikipathway graph."""
