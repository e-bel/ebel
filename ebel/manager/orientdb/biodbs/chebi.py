"""Chebi."""
import logging
import re
from typing import Dict

import pandas as pd
from pyorientdb import OrientDB
from tqdm import tqdm

from ebel import tools
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.orientdb.constants import CHEBI
from ebel.manager.rdbms.models import chebi

logger = logging.getLogger(__name__)


class Chebi(odb_meta.Graph):
    """Chebi."""

    def __init__(self, client: OrientDB = None):
        """Init CHEBI."""
        self.client = client
        self.biodb_name = CHEBI
        self.urls = {chebi.Compound.__tablename__: urls.CHEBI_COMPOUND,
                     chebi.Relation.__tablename__: urls.CHEBI_RELATION,
                     chebi.Inchi.__tablename__: urls.CHEBI_INCHI,
                     chebi.ChemicalData.__tablename__: urls.CHEBI_CHEMICALDATA,
                     chebi.Comment.__tablename__: urls.CHEBI_COMMENT,
                     chebi.DatabaseAccession.__tablename__: urls.CHEBI_DATABASEACCESSION,
                     chebi.Name.__tablename__: urls.CHEBI_NAME,
                     chebi.Reference.__tablename__: urls.CHEBI_REFERENCE,
                     chebi.Structure.__tablename__: urls.CHEBI_STRUCTURE}

        super().__init__(urls=self.urls,
                         biodb_name=self.biodb_name,
                         tables_base=chebi.Base)

    def __len__(self) -> int:
        """Get number of edges in OrientDB."""
        sql = "Select count(*) from bel where namespace='CHEBI'"
        return self.execute(sql)[0].oRecordData['count']

    def __contains__(self, name: str) -> bool:
        """Checks if RS number (without prefix RS) exists in BEL graph."""
        sql = f'Select 1 from bel where namespace="CHEBI" and name = "{name}"'
        return bool(self.execute(sql))

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class."""
        logger.info(f'Insert data in {self.biodb_name}')

        inserted = {}

        file_path_compound = tools.get_file_path(urls.CHEBI_COMPOUND, self.biodb_name)
        df_compounds = pd.read_csv(file_path_compound, sep="\t", low_memory=False, on_bad_lines='skip')
        df_compound_ids = df_compounds[['ID']]
        del df_compounds

        for table_name, url in tqdm(self.urls.items(), desc=f'Import {self.biodb_name.upper()}'):

            file_path = tools.get_file_path(url, self.biodb_name)
            seperator = "\t" if re.search(r'.*\.tsv(\.gz)?$', file_path) else ","
            encoding = "ISO-8859-1" if table_name == 'chebi_reference' else None

            dfs = pd.read_csv(file_path, sep=seperator, encoding=encoding, low_memory=False, on_bad_lines='skip',
                              chunksize=100000)
            inserted[table_name] = 0
            for df in dfs:
                df.columns = df.columns.str.lower()

                if table_name == chebi.Inchi.__tablename__:
                    # with_index = True
                    df.index += 1
                    df.index.rename('id', inplace=True)
                    df.rename(columns={'chebi_id': "compound_id"}, inplace=True)

                if 'compound_id' in df.columns:
                    df = df_compound_ids.rename(columns={'ID': 'compound_id'}).set_index('compound_id').join(
                        df.set_index('compound_id'), how='inner').reset_index()

                if 'init_id' in df.columns:
                    df = df_compound_ids.rename(columns={'ID': 'init_id'}).set_index('init_id').join(
                        df.set_index('init_id'), how='inner').reset_index()

                if 'final_id' in df.columns:
                    df = df_compound_ids.rename(columns={'ID': 'final_id'}).set_index('final_id').join(
                        df.set_index('final_id'), how='inner').reset_index()

                df.to_sql(table_name, self.engine, index=False, if_exists='append')

                inserted[table_name] += df.shape[0]
        self.session.commit()
        return inserted

    def update_bel(self) -> int:
        """Update the BEL edges with CHEBI metadata."""
        updated = 0
        sql = "Update {rid} set chebi = {chebi_id}"
        chebi_nodes = self.query_class(class_name='bio_object',
                                       columns=['name', '@class'],
                                       namespace='CHEBI',
                                       pure=True)

        for chebi_node in tqdm(chebi_nodes, desc='Update ChEBI identifier in BEL'):
            chebi_compound = self.session.query(chebi.Compound.id) \
                .filter(chebi.Compound.name == chebi_node['name']).first()

            if chebi_compound:
                updated += self.execute(sql.format(rid=chebi_node['rid'], chebi_id=chebi_compound[0]))[0]

        return updated

    def update_interactions(self) -> int:
        """Abstract method."""
        return 0
