"""HGNC."""
import re
import sys
import json
import logging

import numpy as np
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB
from collections import namedtuple

from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import HGNC
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import hgnc

logger = logging.getLogger(__name__)
HgncEntry4Update = namedtuple("HgncEntrySimple", ['hgnc_rid', 'label', 'location', 'symbol', 'suggested_corrections'])


class Hgnc(odb_meta.Graph):
    """HGNC class definition."""

    def __init__(self, client: OrientDB = None):
        """Init HGNC."""
        self.client = client
        self.biodb_name = HGNC
        self.urls = {self.biodb_name: urls.HGNC_JSON, 'human_ortholog': urls.HCOP_GZIP}
        super().__init__(generics=odb_structure.hgnc_generics,
                         tables_base=hgnc.Base,
                         indices=odb_structure.hgnc_indices,
                         nodes=odb_structure.hgnc_nodes,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __contains__(self, hgnc_id: object) -> bool:
        """Test existence of hgnc_id."""
        if isinstance(hgnc_id, int):
            hgnc_id = "HGNC:{}".format(hgnc_id)
        r = self.execute("Select count(*) from bel where hgnc.id = '{}' limit 1".format(hgnc_id))
        return bool(len(r[0].oRecordData['count']))

    def __len__(self):
        """Count number of hgnc links in BEL graph."""
        r = self.execute("Select count(*) from bel where hgnc IS NOT NULL")
        return r[0].oRecordData['count']

    def __repr__(self) -> str:
        """Represent HGNC."""
        template = "{{BioDatabase:Hgnc}}[url:{url}, nodes:{nodes}, generics:{generics}]"
        representation = template.format(
            url=self.urls,
            nodes=self.number_of_nodes,
            generics=self.number_of_generics
        )
        return representation

    def insert_data(self) -> Dict[str, int]:
        """Check if files missing for download or generic table empty. If True then insert data."""
        inserted = dict()
        inserted['hgnc'] = self.import_hgnc()
        inserted['hgnc_rdbms'] = self.import_hgnc_into_rdbms()
        inserted['human_orthologs'] = self.insert_orthologs()
        self.session.commit()
        return inserted

    def import_hgnc_into_rdbms(self) -> int:
        """Insert HGNC database into RDBMS."""
        logger.info('Insert HGNC database into RDBMS.')
        file_path = get_file_path(self.urls[self.biodb_name], self.biodb_name)

        with open(file_path, "r", encoding="utf8") as hgnc_file:
            raw_content = hgnc_file.read()
            string_encode = raw_content.encode("ascii", "ignore")  # Convert unicode chars to ascii
            hgnc_content = json.loads(string_encode.decode())

        df = pd.DataFrame(hgnc_content['response']['docs'])

        self._standardize_dataframe(df)
        columns = ['hgnc_id', 'version', 'bioparadigms_slc', 'cd', 'cosmic', 'date_approved_reserved', 'date_modified',
                   'date_name_changed', 'date_symbol_changed', 'ensembl_gene_id', 'entrez_id', 'homeodb', 'horde_id',
                   'imgt', 'intermediate_filament_db', 'iuphar', 'lncipedia', 'lncrnadb',
                   'location', 'location_sortable', 'locus_group', 'locus_type', 'mamit_trnadb', 'merops', 'mirbase',
                   'name', 'orphanet', 'pseudogene_org', 'snornabase', 'status', 'symbol', 'ucsc_id', 'uuid',
                   'vega_id', 'agr']

        df['id'] = pd.to_numeric(df.hgnc_id.str.split(':').str[1])
        df.set_index('id', inplace=True)
        df[columns].to_sql(hgnc.Hgnc.__tablename__, self.engine, if_exists='append')

        df.hgnc_id = pd.to_numeric(df.hgnc_id.str.split(':').str[1])

        for df_col, model, m_col in (('prev_symbol', hgnc.PrevSymbol, None),
                                     ('alias_symbol', hgnc.AliasSymbol, None),
                                     ('alias_name', hgnc.AliasName, None),
                                     ('ccds_id', hgnc.Ccds, 'identifier'),
                                     ('ena', hgnc.Ena, 'identifier'),
                                     ('enzyme_id', hgnc.Enzyme, 'ec_number'),
                                     ('gene_group', hgnc.GeneGroupName, 'name'),
                                     ('gene_group_id', hgnc.GeneGroupId, 'identifier'),
                                     ('uniprot_ids', hgnc.UniProt, 'accession'),
                                     ('rna_central_id', hgnc.RnaCentral, 'identifier'),
                                     ('rgd_id', hgnc.Rgd, 'identifier'),
                                     ('refseq_accession', hgnc.RefSeq, 'accession'),
                                     ('pubmed_id', hgnc.PubMed, 'pmid'),
                                     ('prev_name', hgnc.PrevName, None),
                                     ('omim_id', hgnc.Omim, 'identifier'),
                                     ('mgd_id', hgnc.Mgd, 'identifier'),
                                     ('lsdb', hgnc.Lsdb, 'identifier')):
            df_1n_table = df[[df_col, 'hgnc_id']].explode(df_col).dropna()
            if m_col:
                df_1n_table.rename(columns={df_col: m_col}, inplace=True)
            df_1n_table.to_sql(
                model.__tablename__,
                self.engine,
                if_exists='append',
                index=False)

        return df.shape[0]

    def import_hgnc(self) -> int:
        """Import HGNC into OrientDB."""
        # if new hgnc is imported all hgnc links should be reset and hgnc table should be empty
        self.execute('Update genetic_flow set hgnc=null')
        self.execute('Delete from hgnc')

        file_path = get_file_path(self.urls[self.biodb_name], self.biodb_name)

        with open(file_path, "r", encoding="utf8") as hgnc_file:
            raw_content = hgnc_file.read()
            string_encode = raw_content.encode("ascii", "ignore")  # Convert unicode chars to ascii
            hgnc_content = json.loads(string_encode.decode())

        rows = hgnc_content['response']['docs']
        df = pd.DataFrame(rows)
        df = self._standardize_dataframe(df)
        df.rename(columns={'hgnc_id': 'id'}, inplace=True)
        df = df.where(pd.notnull(df), None)
        sql_temp = "INSERT INTO `hgnc` content {}"

        new_entries = df.to_dict('records')

        for row in tqdm(new_entries, desc=f'Import {self.biodb_name.upper()}'):
            sql = sql_temp.format({k: v for k, v in row.items() if v})

            try:
                self.execute(sql)

            except Exception as e:
                print(e)
                print(sql)
                sys.exit()

        return len(rows)

    def insert_orthologs(self) -> int:
        """Import orthologs from European Molecular Biology Laboratory."""
        # table_name = hgnc.HumanOrtholog.__tablename__
        table_name = "human_ortholog"

        file_path = get_file_path(self.urls['human_ortholog'], self.biodb_name)
        used_columns = [
            'hgnc_id',
            'human_entrez_gene',
            'human_ensembl_gene',
            'human_symbol',
            'ortholog_species',
            'ortholog_species_entrez_gene',
            'ortholog_species_ensembl_gene',
            'ortholog_species_db_id',
            'ortholog_species_symbol',
            'support']
        df = pd.read_csv(file_path, sep='\t', low_memory=False, usecols=used_columns)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.replace('-', np.nan, inplace=True)
        df.to_sql(table_name, self.engine, chunksize=100000, if_exists='append')
        return df.shape[0]

    def get_basic_entry_by_symbol(self, symbol: str) -> HgncEntry4Update:
        """Return HgncEntry4Update object."""
        sql_name = """Select
                        @rid.asString() as hgnc_rid,
                        status,
                        name as label,
                        location,
                        symbol
                    from
                        hgnc where symbol='{}' limit 1""".format(symbol)
        result = self.execute(sql_name)

        if result:
            data = result[0].oRecordData
            status = data.pop('status')
            if status == 'Entry Withdrawn':
                data['suggested_corrections'] = f'{status}: Please use correct HGNC symbol'
            else:
                data['suggested_corrections'] = None

            if 'location' in data:
                data['location'] = self.get_location(data['location'])
            else:
                data['location'] = None
            return HgncEntry4Update(**data)

    @staticmethod
    def get_location(location: str) -> dict:
        """Return formatted version of gene location."""
        regex = r"(?P<chromosome>(\d+|X|Y|mitochondria))(((?P<arm>p|q)?(?P<region>\d+))?(\.(?P<band>\d+)))?"
        locus_found = re.match(regex, location)
        # overwrite data['location'] with structured info in dict
        if locus_found:
            locus_dict = locus_found.groupdict()
            lr = locus_dict['region']
            band = locus_dict['band']
            locus_dict['region'] = int(lr) if lr else lr
            locus_dict['band'] = int(band) if band else band
            location_dict = locus_dict
        else:
            location_dict = {'unknown_schema': location}
        return location_dict

    def get_bel_symbols_without_hgnc_link(self):
        """Return set of all gene symbols in database without a link to HGNC."""
        sql_symbols = "Select distinct(name) as symbol from bio_object where namespace='HGNC' and hgnc IS NULL"
        return {x.oRecordData['symbol'] for x in self.execute(sql_symbols)}

    def get_bel_symbols_all(self):
        """Return set of all gene symbols in database."""
        sql_symbols = "Select distinct(name) as symbol from bio_object where namespace='HGNC'"
        return {x.oRecordData['symbol'] for x in self.execute(sql_symbols)}

    def get_correct_symbol(self, symbol: str):
        """Checks if symbol is valid otherwise checks previsous symbols."""
        result_in_symbol = self.session.query(hgnc.Hgnc).filter(hgnc.Hgnc.symbol == symbol).first()
        if not result_in_symbol:
            result_in_prev_symbol = self.session.query(hgnc.PrevSymbol) \
                .filter(hgnc.PrevSymbol.prev_symbol == symbol).first()
            if result_in_prev_symbol:
                symbol = result_in_prev_symbol.hgnc.symbol
            else:
                symbol = None
        return symbol

    def correct_wrong_symbol(self, symbol, bel_symbols_all: set):
        """Corrects the symbol of the node and relinks all edges to existing node if needed."""
        result = self.session.query(hgnc.PrevSymbol).filter_by(prev_symbol=symbol).first()
        if result:
            correct_symbol = result.hgnc.symbol
            if correct_symbol not in bel_symbols_all:
                sql = f"Select @rid.asString(), bel from bio_object where namespace='HGNC' and name='{symbol}'"
                for row in self.execute(sql):
                    r = row.oRecordData
                    rid = r['rid']
                    correct_bel = re.sub(rf'(?<=:")({symbol})(?=")', correct_symbol, r['bel'])
                    sql = f"UPDATE {rid} SET bel='{correct_bel}', name='{correct_symbol}'"
                    self.execute(sql)
            else:
                # TODO: correction only possible if all edges are relinked to the correct node and old node is deleted
                pass

    def update_bel(self) -> int:
        """Update links in protein, rna and gene nodes to HGNC."""
        # check if hgnc is in ODB
        if not self.execute("Select count(*) as num from hgnc")[0].oRecordData['num']:
            self.import_hgnc()

        bel_symbols_all = self.get_bel_symbols_all()
        symbols_without_hgnc = self.get_bel_symbols_without_hgnc_link()
        hgnc_symbols = {x[0] for x in self.session.query(hgnc.Hgnc.symbol).all()}

        for wrong_symbol in (symbols_without_hgnc - hgnc_symbols):
            self.correct_wrong_symbol(wrong_symbol, bel_symbols_all)

        new_bel_symbols = self.get_bel_symbols_without_hgnc_link()

        updated = 0
        for symbol in tqdm(new_bel_symbols, desc="Update HGNC"):
            if self.update_nodes_by_symbol(symbol):
                updated += 1
        return updated

    def update_gene(self, hgnc_rid: str, label: str, location: str, hgnc_symbol: str,
                    suggested_corrections: str) -> int:
        """Update genes in OrientDB and returns number of updates."""
        suggest = ", suggested_corrections={{'wrong name': {}}}".format(
            suggested_corrections) if suggested_corrections else ''
        sql_temp = """Update gene set
                        hgnc = {hgnc_rid},
                        label= {label},
                        location={location} {suggest}
                    where namespace = 'HGNC' and name = '{hgnc_symbol}'"""
        sql = sql_temp.format(hgnc_rid=hgnc_rid,
                              label=json.dumps(label),
                              location=json.dumps(location),
                              hgnc_symbol=hgnc_symbol,
                              suggest=suggest)
        return self.execute(sql)[0]

    def update_rna(self, hgnc_rid: str, label: str, hgnc_symbol: str, suggested_corrections: str) -> int:
        """Update RNAs in OrientDB and returns number of updates."""
        suggest = ", suggested_corrections={{'wrong name': {}}}".format(
            suggested_corrections) if suggested_corrections else ''
        sql_temp = """Update rna set hgnc = {hgnc_rid},label={label} {suggest}
                      where namespace = 'HGNC' and name = '{hgnc_symbol}'"""
        sql = sql_temp.format(hgnc_rid=hgnc_rid,
                              label=json.dumps(label),
                              hgnc_symbol=hgnc_symbol,
                              suggest=suggest)
        return self.execute(sql)[0]

    def update_protein(self, hgnc_rid: str, label: str, hgnc_symbol: str, suggested_corrections: str) -> int:
        """Update proteins in OrientDB and returns number of updates."""
        suggest = ", suggested_corrections={{'wrong name': {}}}".format(
            suggested_corrections) if suggested_corrections else ''
        sql_temp = """Update protein set hgnc = {hgnc_rid},label={label} {suggest}
                      where namespace = 'HGNC' and name = '{hgnc_symbol}'"""
        sql = sql_temp.format(hgnc_rid=hgnc_rid,
                              label=json.dumps(label),
                              hgnc_symbol=hgnc_symbol,
                              suggest=suggest)
        return self.execute(sql)[0]

    def update_nodes_by_symbol(self, symbol) -> dict:
        """Update all nodes by HGNC symbol."""
        hgnc = self.get_basic_entry_by_symbol(symbol)

        if hgnc:
            suggest = json.dumps(hgnc.suggested_corrections) if hgnc.suggested_corrections else None

            num_update_genes = self.update_gene(
                hgnc_symbol=hgnc.symbol,
                hgnc_rid=hgnc.hgnc_rid,
                label=hgnc.label,
                location=hgnc.location,
                suggested_corrections=suggest)
            num_update_rnas = self.update_rna(
                hgnc_symbol=hgnc.symbol,
                hgnc_rid=hgnc.hgnc_rid,
                label=hgnc.label,
                suggested_corrections=suggest)
            num_update_proteins = self.update_protein(
                hgnc_symbol=hgnc.symbol,
                hgnc_rid=hgnc.hgnc_rid,
                label=hgnc.label,
                suggested_corrections=suggest)
            return {'genes': num_update_genes, 'rnas': num_update_rnas, 'proteins': num_update_proteins}

    def get_symbol_entrez_dict(self) -> Dict[str, int]:
        """Return dictionary with gene symbols as keys and entrez IDs as values."""
        query = self.session.query(hgnc.Hgnc.symbol, hgnc.Hgnc.entrez_id).filter(hgnc.Hgnc.entrez_id.isnot(None))
        return {r.symbol: r.entrez_id for r in query.all()}

    def update_interactions(self) -> int:
        """Abstract method."""
        pass
