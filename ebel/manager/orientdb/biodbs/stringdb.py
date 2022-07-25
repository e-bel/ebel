"""STRING module."""
import logging
import numpy as np
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB
from collections import namedtuple

from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import STRINGDB
from ebel.manager.orientdb.biodbs.hgnc import Hgnc
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import stringdb

logger = logging.getLogger(__name__)


class StringDb(odb_meta.Graph):
    """STRING database."""

    def __init__(self, client: OrientDB = None):
        """Init StringDB database."""
        self.client = client
        self.biodb_name = STRINGDB
        self.table_action = stringdb.StringDbAction.__tablename__
        self.table_strdb = stringdb.StringDb.__tablename__
        self.table_protein = stringdb.StringDbProtein.__tablename__
        self.urls = {self.table_strdb: urls.STRING_INTS,
                     self.table_action: urls.STRING_ACTIONS,
                     self.table_protein: urls.STRING_NAMES}
        super().__init__(edges=odb_structure.stringdb_edges,
                         urls=self.urls,
                         tables_base=stringdb.Base,
                         biodb_name=self.biodb_name)

    def __len__(self) -> dict:
        """Get number of 'biogrid_interaction' graph edges."""
        pass

    def __contains__(self, biogrid_id) -> bool:
        """Check if stringdb edge in graph."""
        pass

    def insert_data(self) -> Dict[str, int]:
        """Insert data from url. Return number of inserted entries."""
        inserted = dict()
        inserted[self.table_protein] = self.insert_protein_data()
        inserted[self.table_strdb] = self.insert_link_data()
        inserted[self.table_action] = self.insert_action_data()

        self.session.commit()
        return inserted

    def insert_link_data(self) -> int:
        """Insert link STRINGDB information into RDBMS."""
        logger.info(f'Insert {self.biodb_name} link data in RDBMS.')

        file_path = get_file_path(self.urls[self.table_protein], self.biodb_name)
        df_protein = pd.read_csv(file_path, sep='\t', usecols=['protein_external_id', 'preferred_name'])

        # Define column types to improve memory efficiency
        cols = ['protein1', 'protein2', 'neighborhood', 'neighborhood_transferred', 'fusion', 'cooccurence',
                'homology', 'coexpression', 'coexpression_transferred', 'experiments', 'experiments_transferred',
                'database', 'database_transferred', 'textmining', 'textmining_transferred', 'combined_score']

        col_types = dict()
        for col in cols:
            if col.startswith('protein'):
                col_types[col] = 'object'
            else:
                col_types[col] = 'uint16'

        file_path = get_file_path(self.urls[self.table_strdb], self.biodb_name)
        df_link = pd.read_csv(file_path, dtype=col_types, sep=" ")

        df = df_link.set_index('protein1').join(df_protein.set_index('protein_external_id'), how='inner')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'protein1', 'preferred_name': 'symbol1'}, inplace=True)
        df = df.set_index('protein2').join(df_protein.set_index('protein_external_id'), how='inner')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'protein2', 'preferred_name': 'symbol2'}, inplace=True)
        df.index += 1
        df.index.rename('id', inplace=True)

        df.to_sql(self.table_strdb, self.engine, if_exists="append", chunksize=10000)

        return df.shape[0]

    def insert_protein_data(self) -> int:
        """Generates a dictionary of STRINGDB identifiers as keys and HGNC symbols as values."""
        file_path = get_file_path(self.urls[self.table_protein], self.biodb_name)
        df = pd.read_csv(file_path, sep='\t', usecols=['protein_external_id', 'preferred_name'])
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(self.table_protein, self.engine, if_exists='append')
        return df.shape[0]

    def insert_action_data(self) -> int:
        """Insert action STRINGDB information into RDGMS."""
        logger.info(f'Insert {self.biodb_name} action data in RDBMS.')

        file_path = get_file_path(self.urls[self.table_protein], self.biodb_name)
        df_protein = pd.read_csv(file_path, sep='\t', usecols=['protein_external_id', 'preferred_name'])

        file_path = get_file_path(self.urls[self.table_action], self.biodb_name)
        df_action = pd.read_csv(file_path, sep="\t")

        # Replace 't' and 'f' values for True/False in appropriate columns
        df_action.replace({'is_directional': {'t': True, 'f': False},
                           'a_is_acting': {'t': True, 'f': False}}, inplace=True)

        # Replace NaN with None
        df_action.replace({np.nan: None}, inplace=True)

        df = df_action.set_index('item_id_a').join(df_protein.set_index('protein_external_id'), how='inner')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'item_id_a', 'preferred_name': 'symbol1'}, inplace=True)
        df = df.set_index('item_id_b').join(df_protein.set_index('protein_external_id'), how='inner')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'item_id_b', 'preferred_name': 'symbol2'}, inplace=True)
        df.index += 1
        df.index.rename('id', inplace=True)

        df.to_sql(self.table_action, self.engine, if_exists="append", chunksize=10000)

        return df.shape[0]

    def get_stringdb_action_hgnc_set(self):
        """Get unique HGNC symbols from stringdb_actions table."""
        sql = f"""(Select distinct( symbol1 ) from {self.table_action})
                union (Select distinct( symbol2 ) from {self.table_action})"""
        return set([x[0] for x in self.engine.execute(sql).fetchall()])

    def update_interactions(self) -> Dict[str, int]:
        """Update the edges with StringDB metadata."""
        hgnc = Hgnc(self.client)
        updated = dict()
        updated["interactions"] = self.update_stringdb_interactions(hgnc)
        updated["actions"] = self.update_action_interactions(hgnc)
        return updated

    def get_stringdb_symbols(self):
        """Return all gene symbols used by StringDB."""
        return {x[0] for x in self.session.query(stringdb.StringDbProtein.preferred_name).all()}

    def update_stringdb_interactions(self, hgnc: Hgnc) -> int:
        """Iterate through BEL proteins and adds stringdb edges to existing proteins in KG."""
        columns = ("neighborhood",
                   "neighborhood_transferred",
                   "fusion",
                   "cooccurence",
                   "homology",
                   "coexpression",
                   "coexpression_transferred",
                   "experiments",
                   "experiments_transferred",
                   "database",
                   "database_transferred",
                   "textmining",
                   "textmining_transferred",
                   "combined_score")

        bel_hgnc_rid_dict = self.get_pure_symbol_rids_dict_in_bel_context(namespace='HGNC')
        bel_hgncs = set(bel_hgnc_rid_dict.keys())
        strdb_hgncs = self.get_stringdb_symbols()
        shared_hgncs = bel_hgncs & strdb_hgncs

        updated = 0
        already_inserted = set()

        strdb = stringdb.StringDb

        for hgnc_a in tqdm(shared_hgncs, desc='Update has_ppi_st edges'):
            query = self.session.query(strdb)
            query = query.filter(strdb.symbol1 == hgnc_a, strdb.experiments > 0)

            for row in query.all():

                sorted_combi = tuple(sorted([row.symbol1, row.symbol2]))

                if sorted_combi not in already_inserted:
                    value_dict = {k: v for k, v in row.__dict__.items() if k in columns}

                    from_rid = self.get_create_rid_by_symbol(row.symbol1, bel_hgnc_rid_dict, hgnc)
                    to_rid = self.get_create_rid_by_symbol(row.symbol2, bel_hgnc_rid_dict, hgnc)

                    if from_rid and to_rid:
                        self.create_edge(class_name='has_ppi_st',
                                         from_rid=from_rid,
                                         to_rid=to_rid,
                                         value_dict=value_dict)
                        already_inserted.add(sorted_combi)
                        updated += 1

        return updated

    def get_create_rid_by_symbol(self, symbol: str, symbol_rid_dict: dict, hgnc: Hgnc) -> str:
        """Create or get rID entry for a given gene symbol.

        Parameters
        ----------
        symbol: str
            Gene symbol.
        symbol_rid_dict: dict
            Entry parameters matching those of the desired rID entry.
        hgnc: Hgnc
            Hgnc model definition.

        Returns
        -------
        str
            rID.
        """
        if symbol not in symbol_rid_dict:
            symbol = hgnc.get_correct_symbol(symbol)
            if symbol:
                value_dict = {'name': symbol, 'namespace': 'HGNC', 'pure': True, 'bel': f'p(HGNC:"{symbol}")'}
                symbol_rid_dict[symbol] = self.get_create_rid('protein', value_dict, check_for='bel')
        return symbol_rid_dict.get(symbol)

    def update_action_interactions(self, hgnc: Hgnc) -> int:
        """Iterate through BEL proteins and add stringdb_action edges to existing proteins in KG.

        Translation of String action/mode combination to ebel-edges

        mode       | action     | ebel edge class
        -----------|------------|-----------
        expression | NULL       | increases-expression-of
        ptmod      | NULL       | controls-pmod-of
        activation | activation | activates
        expression | inhibition | decreases-expression-of
        inhibition | inhibition | inhibits
        """
        translator = {('expression', None): 'increases_expression_of_st',
                      ('ptmod', None): 'controls_pmod_of_st',
                      ('activation', 'activation'): 'activates_st',
                      ('expression', 'inhibition'): 'decreases_expression_of_st',
                      ('inhibition', 'inhibition'): 'inhibits_st'}

        Action = namedtuple('Action', ('symbol1', 'symbol2', 'mode', 'action', 'score'))

        columns = ', '.join(Action._fields)
        sql_temp = f"""Select {columns} from {self.table_action}
                       where mode in ('activation', 'inhibition', 'ptmod', 'expression')
                       and (symbol1='{{symbol}}' or symbol2='{{symbol}}')
                       and is_directional=1 and a_is_acting=1"""

        symbols_rid_dict = self.get_pure_symbol_rids_dict_in_bel_context(namespace='HGNC')
        symbols = tuple(symbols_rid_dict.keys())

        already_inserted = set()

        updated = 0
        for symbol in tqdm(symbols, desc='Update has_action_st edges'):
            rows = self.engine.execute(sql_temp.format(symbol=symbol))
            for row in rows.fetchall():
                action = Action(*row)

                sorted_combi = tuple(sorted([action.symbol1, action.symbol2]))

                if sorted_combi not in already_inserted:

                    from_rid = self.get_create_rid_by_symbol(action.symbol1, symbols_rid_dict, hgnc)
                    to_rid = self.get_create_rid_by_symbol(action.symbol2, symbols_rid_dict, hgnc)

                    if from_rid and to_rid:
                        class_name = translator[(action.mode, action.action)]

                        self.create_edge(class_name=class_name,
                                         from_rid=from_rid,
                                         to_rid=to_rid,
                                         value_dict={'score': action.score})
                        already_inserted.update([sorted_combi])
                        updated += 1

        return updated
