"""Reactome."""
import json
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB
from sqlalchemy import distinct

from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import REACTOME
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import reactome


class Reactome(odb_meta.Graph):
    """Reactome."""

    def __init__(self, client: OrientDB = None):
        """Reactome database."""
        self.client = client
        self.biodb_name = REACTOME
        self.urls = {self.biodb_name: urls.REACTOME}
        super().__init__(nodes=odb_structure.reactome_nodes,
                         tables_base=reactome.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __repr__(self):
        """Represent the class."""
        template = "{{BioDatabase:{class_name}}}[url:{url}, nodes_with_reactome:{num_reactome}, generics:{generics}]"
        num = self.query_get_dict("Select count(*) from V where reactome_pathways is not null")[0]['count']
        representation = template.format(
            class_name=self.__class__.__name__,
            url=self.urls,
            num_reactome=num,
            generics={k: v for k, v in self.number_of_generics.items() if v}
        )
        return representation

    def __len__(self) -> int:
        return self.number_of_nodes

    def __contains__(self, reactome_id: str) -> bool:
        return bool(len(self.execute("Select 1 from reactome where id = '{}' limit 1".format(reactome_id))))

    def insert_data(self) -> Dict[str, int]:
        """Insert data into OrientDB database."""
        columns = ['uniprot_accession', 'identifier', 'url', 'name', 'evidence_type', 'organism']
        # evidence_type are:
        # 1. IEA:= Inferred from Electronic Annotation
        # 2. TAS:= Traceable Author Statement
        df = pd.read_csv(get_file_path(self.urls[self.biodb_name], self.biodb_name),
                         sep="\t", names=columns, usecols=[0, 1, 3, 4, 5])
        df.index += 1
        df.index.rename('id', inplace=True)
        df.name = df.name.str.strip()
        df.to_sql(reactome.Reactome.__tablename__, self.engine, if_exists="append")

        self.session.commit()

        return {self.biodb_name: df.shape[0]}

    def update_interactions(self) -> int:
        """Update all protein.reactome where protein is pure."""
        self.execute("Update protein set reactome_pathways = null")
        sql_update = "Update protein set reactome_pathways = {} where uniprot = '{}' and pure=true"

        sql_accessions = "Select distinct(uniprot) as accession_id from protein " \
                         "where uniprot IS NOT NULL and pure=true"

        proteins = self.execute(sql_accessions)

        updated = 0
        if proteins:
            for unipid_acc in tqdm(proteins, desc="Update Reactome info in pure proteins."):
                accession_id = unipid_acc.oRecordData['accession_id']
                results = self.session.query(distinct(reactome.Reactome.name)).filter(
                    reactome.Reactome.uniprot_accession == accession_id).all()
                if results:
                    reactome_pathways = json.dumps([x[0] for x in results])
                    updated += self.execute(sql_update.format(reactome_pathways, accession_id))[0]

        return updated
