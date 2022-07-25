"""UniProt module."""
import os
import re
import ftplib
import logging
import pandas as pd

from tqdm import tqdm
from pyorientdb import OrientDB
from lxml.etree import iterparse
from collections import namedtuple
from typing import List, Dict, Tuple, Union

from ebel.defaults import default_tax_ids
from ebel.tools import gunzip, get_file_path
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.orientdb.constants import UNIPROT

from ebel.manager.rdbms.models import uniprot as up

logger = logging.getLogger(__name__)

Xrefs = Dict[Tuple[str, str], int]
Functions = Dict[str, int]
ScLocations = Dict[str, int]
Organisms = Dict[int, str]
Keywords = Dict[int, str]

Xpath = namedtuple('Xpath', ('recommended_name',
                             'gene_name',
                             'organism_scientific',
                             'taxid',
                             'function',
                             'subcellular_locations',
                             'location'
                             ))

XML_URL = 'http://uniprot.org/uniprot'
XML_NAMESPACE = f'{{{XML_URL}}}'
XN = {"n": XML_URL}


class UniProtEntry:
    """Helper class for the import of data into RDMS."""

    column_names = [
        'name',
        'accession',
        'recommended_name',
        'gene_names',
        'taxid',
        'host_taxids',
        'function_id',
        'xref_ids',
        'keyword_ids',
        'subcellular_location_ids'
    ]

    def __init__(self):
        """Init UniProt."""
        self.name: Union[str, None] = None
        self.accession: Union[str, None] = None
        self.recommended_name: Union[str, None] = None
        self.gene_names: List[str] = []
        self.taxid: Union[int, None] = None
        self.host_taxids: List[int] = []
        self.function_id: Union[int, None] = None
        self.xref_ids: List[int] = []
        self.keyword_ids: List[int] = []
        self.subcellular_location_ids: List[int] = []

    def get_data_dict(self):
        """Return dict with column names as keys and their associated value tuples as values."""
        return dict(zip(self.column_names, self.get_data_tuple()))

    def get_data_tuple(self):
        """Return a tuple containing metadata for an entry."""
        return (
            self.name,
            self.accession,
            self.recommended_name,
            self.gene_names,
            self.taxid,
            self.host_taxids,
            self.function_id,
            self.xref_ids,
            self.keyword_ids,
            self.subcellular_location_ids)


class UniProt(odb_meta.Graph):
    """UniProt Importer and interface."""

    columns2import = [
        'dataset',
        'accession',
        'name',
        'protein',
        'gene',
        'comment',
        'proteinExistence',
        'feature',
        'evidence',
        'dbReference'
    ]

    def __init__(self, client: OrientDB = None, tax_ids: list = default_tax_ids):
        """Init UniProt."""
        self.client = client
        self.biodb_name = UNIPROT
        self.file_path = get_file_path(urls.UNIPROT_SPROT, self.biodb_name)
        self.file_path_gunzipped = self.file_path.split('.gz')[0]
        super().__init__(urls={UNIPROT: urls.UNIPROT_SPROT},
                         tables_base=up.Base,
                         biodb_name=self.biodb_name)
        self.tax_ids = tax_ids

        self.xpath_pattern = Xpath(
            recommended_name='./n:recommendedName/n:fullName[1]/text()',
            gene_name='./n:name/text()',
            organism_scientific="./n:name[@type='scientific'][1]/text()",
            taxid="./n:dbReference[@type='NCBI Taxonomy'][1]/@id",
            function="./n:text/text()",
            subcellular_locations="./n:subcellular_location/n:location/text()",
            location='./n:subcellularLocation/n:location'
        )

    def __contains__(self, accession) -> bool:
        """Check if protein node with accession exists in graph."""
        results = self.execute(f"Select 1 from protein where uniprot = '{accession}'")
        return bool(len(results))

    def __len__(self) -> int:
        """Return number of proteins (nodes) with uniprot accession number."""
        sql = "Select count(*) from protein where uniprot IS NOT NULL"
        return self.execute(sql)[0].oRecordData['count']

    def insert_data(self) -> Dict[str, int]:
        """Insert UniProt data depending on NCBI taxonomy identifier."""
        dialect = self.session.bind.dialect.name
        if dialect == 'mysql':
            self.engine.execute("SET FOREIGN_KEY_CHECKS=0")

        inserted = self.insert_uniprot()
        self.add_gene_symbols()
        self.session.commit()

        if dialect == 'mysql':
            self.engine.execute("SET FOREIGN_KEY_CHECKS=1")

        return {self.biodb_name: inserted}

    def add_gene_symbols(self):
        """Add gene symbols to all tables."""
        self._add_hgnc_symbols()
        self._add_mgi_symbols()
        self._add_rgd_symbols()
        self._add_fly_symbols()

    def _delete_gene_symbols(self, taxid) -> None:
        self.session.query(up.GeneSymbol).filter(up.GeneSymbol.uniprot.has(up.Uniprot.taxid == taxid)) \
            .delete(synchronize_session=False)
        self.session.commit()

    def _add_hgnc_symbols(self) -> int:
        """Add HGNC symbols from genenames.org."""
        inserted = 0
        self._delete_gene_symbols(9606)

        df = pd.read_csv(urls.HGNC_TSV, sep='\t',
                         low_memory=False, usecols=['symbol', 'uniprot_ids']).dropna()

        for row in tqdm(df.itertuples(index=False), desc="Add HGNC symbols to UniProt", total=df.shape[0]):
            uniprot = self.session.query(up.Uniprot).filter(up.Uniprot.accession == row.uniprot_ids).scalar()
            if uniprot:
                self.session.add(up.GeneSymbol(symbol=row.symbol, uniprot_id=uniprot.id))
                inserted += 1
        self.session.commit()

        return inserted

    def _add_mgi_symbols(self) -> int:
        """Add MGI symbols from genenames.org."""
        inserted = 0

        self._delete_gene_symbols(10090)

        df = pd.read_csv(urls.UNIPROT_MGI, sep="\t", usecols=[1, 6], names=['symbol', 'uniprot_accession']).dropna()

        for row in tqdm(df.itertuples(index=False), desc="Add MGI symbols to UniProt", total=df.shape[0]):
            uniprot = self.session.query(up.Uniprot).filter(up.Uniprot.accession == row.uniprot_accession).scalar()

            if uniprot:
                self.session.add(up.GeneSymbol(symbol=row.symbol, uniprot_id=uniprot.id))
                inserted += 1
        self.session.commit()

        return inserted

    def _add_rgd_symbols(self) -> int:
        """Add MGI symbols from genenames.org."""
        inserted = 0

        self._delete_gene_symbols(10116)

        df = pd.read_csv(
            urls.UNIPROT_RGD,
            sep="\t",
            comment='#',
            low_memory=False,
            usecols=['SYMBOL', 'UNIPROT_ID']
        ).dropna()
        df.columns = ['symbol', 'uniprot_accessions']
        df.uniprot_accessions = df.uniprot_accessions.str.split(';')

        for row in tqdm(df.itertuples(index=False), desc="Add RGD symbols to UniProt", total=df.shape[0]):
            for accession in row.uniprot_accessions:
                uniprot = self.session.query(up.Uniprot).filter(up.Uniprot.accession == accession).scalar()
                if uniprot:
                    self.session.add(up.GeneSymbol(symbol=row.symbol, uniprot_id=uniprot.id))
                    inserted += 1
        self.session.commit()

        return inserted

    def _add_fly_symbols(self) -> int:
        """Add MGI symbols from genenames.org."""
        inserted = 0
        ftp_base = "ftp.flybase.org"
        ftp_folder = '/releases/current/precomputed_files/genes/'
        ftp = ftplib.FTP(ftp_base)
        ftp.login("anonymous", "anonymous")
        files = ftp.nlst(ftp_folder)
        file_found = [x for x in files if re.search(r'fbgn_NAseq_Uniprot_fb_\d{4}_\d{2}.tsv.gz', x)]
        if file_found:
            url = f'ftp://{ftp_base}{file_found[0]}'
            inserted = 0

            self._delete_gene_symbols(7227)

            df = pd.read_csv(
                url,
                comment='#',
                sep='\t',
                header=None,
                usecols=[0, 5],
                names=['symbol', 'uniprot_accession']
            ).dropna()

            for row in tqdm(df.itertuples(index=False), desc="Add FlyBase symbols to UniProt", total=df.shape[0]):
                uniprot = self.session.query(up.Uniprot).filter(up.Uniprot.accession == row.uniprot_accession).scalar()
                if uniprot:
                    self.session.add(up.GeneSymbol(symbol=row.symbol, uniprot_id=uniprot.id))
                    inserted += 1
            self.session.commit()
        ftp.close()
        return inserted

    def update_bel(self) -> Dict[str, int]:
        """Update uniprot links in protein nodes to uniprot class."""
        updated = dict()
        updated['HGNC'] = self._update_proteins('HGNC', 9606)
        updated['MGI'] = self._update_proteins('MGI', 10090)
        updated['RGD'] = self._update_proteins('RGD', 10116)
        updated['UNIPROT'] = self._update_uniprot_proteins()
        return updated

    def _update_protein_node(self, uniprot_accession, recommended_name, name, namespace, taxid) -> int:
        """Update all proteins using UNIPROT as namespace. Returns numbers of updated."""
        sql = f'Update protein set uniprot = "{uniprot_accession}", label = "{recommended_name}", ' \
              f'species = {taxid} where namespace = "{namespace}" and name = "{name}"'
        return self.execute(sql)[0]

    def _get_accesssion_recname(self, taxid, gene_symbol) -> Union[Tuple[str, str], None]:
        """Get uniprot accession and recommended name from HGNC.

        If this has no result it tries uniprot by gene symbol and NCBI taxonomy ID.
        """
        # TODO: This is in general a dangerous method because it selects the first accession number, but there could
        # be more than one
        sql = f'Select accession, recommended_name from uniprot as u inner join uniprot_gene_symbol as gs ' \
              f'on (u.id=gs.uniprot_id) where u.taxid={taxid} and gs.symbol="{gene_symbol}" limit 1'
        results = self.engine.execute(sql)
        return results.fetchone() if results else None

    def _update_proteins(self, namespace, taxid) -> int:
        """Update human proteins (namespace HGNC) with uniprot accession and recommended name.

        Returns number of updated proteins.
        """
        sql = f'SELECT distinct(name) as name from protein WHERE namespace="{namespace}"'
        updated = 0
        for protein in self.query(sql).itertuples(index=False):
            acc_rec = self._get_accesssion_recname(taxid, protein.name)
            if acc_rec:
                accession, recommended_name = acc_rec
                num_updated = self._update_protein_node(accession, recommended_name, protein.name, namespace, taxid)
                updated += num_updated
            else:
                err_txt = f'NO MAPPING TO UNIPROT: {namespace}:{protein.name} can not be mapped to uniprot. ' \
                          f'Possible reasons: Withdrawn or only predicted.'
                logging.warning(err_txt)
        return updated

    def _get_recname_taxid_by_accession_from_uniprot_api(self, accession) -> Tuple[str, int]:
        """Fetch uniprot entry by accession and adds to the database. Returns recommended name."""
        sql = f"Select recommended_name,taxid from uniprot where accession='{accession}' limit 1"
        result = self.engine.execute(sql).fetchone()
        if result:
            return result

    def _update_uniprot_proteins(self) -> int:
        """Update all proteins using UNIPROT as namespace. Returns number of updated proteins."""
        updated = 0
        sql_temp = "Select recommended_name, taxid from uniprot where accession='{}' limit 1"
        sql_uniprot = 'SELECT distinct(name) as accession from protein WHERE namespace="UNIPROT"'
        sql_update = 'Update protein set uniprot = name, label = "{}", species = {} ' \
                     'where namespace = "UNIPROT" and name = "{}"'
        for protein in self.query(sql_uniprot).itertuples(index=False):
            sql = sql_temp.format(protein.accession)
            found = self.engine.execute(sql).fetchone()
            if found:
                recommended_name, taxid = found
                num_updated = self.execute(sql_update.format(recommended_name, taxid, protein.accession))[0]
                updated += num_updated
            else:
                recname_taxid = self._get_recname_taxid_by_accession_from_uniprot_api(protein.accession)
                if recname_taxid:
                    recommended_name, taxid = recname_taxid
                    num_updated = self.execute(sql_update.format(recommended_name, taxid, protein.accession))[0]
                    updated += num_updated
        return updated

    def __read_linked_tables(self) -> Tuple[Keywords, Organisms, Xrefs, Functions, ScLocations, int]:
        """Return xref, functions and subcellular locations."""
        xrefs: Xrefs = {}
        functions: Functions = {}
        sclocations: ScLocations = {}
        organisms: Organisms = {}
        xref_index = 0
        function_index = 0
        sclocation_index = 0
        keywords: Keywords = {}

        doc = iterparse(self.file_path_gunzipped, events=('end',), tag=f'{XML_NAMESPACE}entry')

        counter = 0

        logger.info('Read linked UniProt tables')

        for action, elem in tqdm(doc, desc='Get linked UniProt data'):

            counter += 1

            for child in elem.iterchildren():

                ctag = child.tag[len(XML_NAMESPACE):]

                if ctag == 'dbReference':
                    x_type_id = (child.attrib.get('type'),
                                 child.attrib.get('id'))
                    if x_type_id not in xrefs:
                        xref_index += 1
                        xrefs[x_type_id] = xref_index

                elif ctag in ['organismHost', 'organism']:
                    taxid = int(child.xpath(
                        self.xpath_pattern.taxid,
                        namespaces=XN)[0])
                    if taxid not in organisms:
                        organism_scientific = child.xpath(
                            self.xpath_pattern.organism_scientific,
                            namespaces=XN
                        )[0]
                        organisms[taxid] = organism_scientific

                elif ctag == "keyword":
                    keyword_id = int(child.attrib.get('id').split('KW-')[1])
                    if keyword_id not in keywords:
                        keywords[keyword_id] = child.text

                elif ctag == 'comment':
                    ctype = child.attrib.get('type')

                    if ctype == 'function':
                        func = child.xpath(
                            self.xpath_pattern.function,
                            namespaces=XN)[0]

                        if func not in functions:
                            function_index += 1
                            functions[func] = function_index

                    elif ctype == 'subcellular location':
                        scls = child.findall(self.xpath_pattern.location,
                                             namespaces=XN)

                        for scl in [x.text for x in scls]:

                            if scl not in sclocations:
                                sclocation_index += 1
                                sclocations[scl] = sclocation_index
            elem.clear()
        return keywords, organisms, xrefs, functions, sclocations, counter

    def __insert_linked_data(self, keywords: Keywords, organisms: Organisms, xrefs: Xrefs, functions: Functions,
                             sclocations: ScLocations):
        """Insert data from file."""
        if keywords:
            df_kw = pd.DataFrame(keywords.items(), columns=['keywordid', 'keyword_name'])
            self._insert_into_database(df_kw, up.Keyword)

        if organisms:
            df_org = pd.DataFrame(organisms.items(), columns=['taxid', 'scientific_name'])
            self._insert_into_database(df_org, up.Organism)

        if sclocations:
            df_sl = pd.DataFrame([x[::-1] for x in sclocations.items()], columns=['id', 'name'])
            self._insert_into_database(df_sl, up.SubcellularLocation)

        if xrefs:
            df_xr = pd.DataFrame([(v, k[0], k[1]) for k, v in xrefs.items()], columns=['id', 'db', 'identifier'])
            self._insert_into_database(df_xr, up.Xref)

        if functions:
            df_fc = pd.DataFrame([x[::-1] for x in functions.items()], columns=['id', 'description'])
            self._insert_into_database(df_fc, up.Function)

    def _insert_into_database(self, dataframe, model):
        logger.info(f"insert into {model.__tablename__}")
        dataframe.to_sql(model.__tablename__,
                         self.engine,
                         chunksize=100000,
                         if_exists='append',
                         index=False)
        inserted = dataframe.shape[0]
        del dataframe
        return inserted

    def insert_uniprot(self) -> int:
        """Insert UniProt data into database."""
        logger.info("Drop and create Uniprot table in RDBMS")

        logger.info("Insert data linked to Uniprot entry into RDBMS")
        # avoid to use old gunzipped file
        if os.path.exists(self.file_path_gunzipped):
            os.remove(self.file_path_gunzipped)
        if not os.path.exists(self.file_path_gunzipped):
            gunzip(self.file_path, self.file_path_gunzipped)

        keywords, hosts, xrefs, functions, sclocations, number_of_entries = self.__read_linked_tables()
        self.__insert_linked_data(keywords, hosts, xrefs, functions, sclocations)
        inserted = self.__insert_uniprot_data(xrefs, functions, sclocations, number_of_entries)

        # save storage space
        if os.path.exists(self.file_path_gunzipped):
            os.remove(self.file_path_gunzipped)

        # return number_of_entries
        return inserted

    @staticmethod
    def shorten_tag(elem):
        """Shorten the given tag."""
        return elem.tag[len(XML_NAMESPACE):]

    @staticmethod
    def get_tag(name):
        """Get tag based on given name."""
        return f'{XML_NAMESPACE}{name}'

    def __insert_uniprot_data(self, xrefs, functions, sclocations, number_of_entries) -> int:

        doc = iterparse(self.file_path_gunzipped, events=('end',), tag=self.get_tag('entry'))

        counter = 0

        uniprots = []

        for action, elem in tqdm(doc, total=number_of_entries, desc=f"Import {self.biodb_name.upper()}"):
            counter += 1

            uniprot = UniProtEntry()
            for child in elem.iterchildren():
                ctag = self.shorten_tag(child)

                if ctag == 'accession' and not uniprot.accession:
                    uniprot.accession = child.text

                elif ctag == 'name':
                    uniprot.name = child.text

                elif ctag == 'gene':
                    for cchild in child.iterchildren(tag=self.get_tag('name')):
                        uniprot.gene_names.append(cchild.text)

                elif ctag == 'organism':
                    for cchild in child.iterchildren(tag=self.get_tag('dbReference')):
                        if cchild.attrib.get('type') == 'NCBI Taxonomy':
                            uniprot.taxid = int(cchild.attrib.get('id'))
                            break

                elif ctag == 'protein':
                    for cchild in child.iterchildren(tag=self.get_tag('recommendedName')):
                        for ccchild in cchild.iterchildren(tag=self.get_tag('fullName')):
                            uniprot.recommended_name = ccchild.text
                            break

                elif ctag == 'organismHost':
                    for cchild in child.iterchildren(tag=self.get_tag('dbReference')):
                        if cchild.attrib.get('type') == 'NCBI Taxonomy':
                            uniprot.host_taxids.append(int(cchild.attrib.get('id')))

                elif ctag == 'comment':
                    ctype = child.attrib.get('type')

                    if ctype == 'function':
                        for cchild in child.iterchildren(tag=self.get_tag('text')):
                            uniprot.function_id = functions[cchild.text]
                            break

                    elif ctype == 'subcellular location':
                        for cchild in child.iterchildren(tag=self.get_tag('subcellularLocation')):
                            for ccchild in cchild.iterchildren(tag=self.get_tag('location')):
                                uniprot.subcellular_location_ids.append(sclocations[ccchild.text])

                elif ctag == 'dbReference':
                    xref = child.attrib.get('type'), child.attrib.get('id')
                    uniprot.xref_ids.append(xrefs[xref])

                elif ctag == "keyword":
                    keyword_id = int(child.attrib.get('id').split('KW-')[1])
                    uniprot.keyword_ids.append(keyword_id)
            uniprots.append(uniprot)
            elem.clear()

        df = pd.DataFrame([u.get_data_tuple() for u in uniprots], columns=UniProtEntry.column_names)
        df.index += 1
        df.index.rename('id', inplace=True)
        cols_uniprot = ['name', 'accession', 'recommended_name', 'taxid', 'function_id']
        logger.info(f"start insert {up.Uniprot.__tablename__}")
        df[cols_uniprot].to_sql(up.Uniprot.__tablename__, self.engine, if_exists='append', chunksize=100000)

        df['uniprot_id'] = df.index

        logger.info(f"start insert {up.Gene.__tablename__}")
        df[['gene_names', 'uniprot_id']].explode('gene_names').dropna().rename(columns={'gene_names': 'name'}) \
            .to_sql(up.Gene.__tablename__, self.engine, if_exists='append', index=False, chunksize=100000)

        logger.info(f"start insert {up.uniprot__uniprot_keyword.name}")
        df[['keyword_ids', 'uniprot_id']].explode('keyword_ids').dropna() \
            .rename(columns={'keyword_ids': 'uniprot_keyword_id'}) \
            .to_sql(up.uniprot__uniprot_keyword.name, self.engine, if_exists='append', index=False, chunksize=100000)

        logger.info(f"start insert {up.uniprot__uniprot_host.name}")
        df[['host_taxids', 'uniprot_id']].explode('host_taxids').dropna() \
            .rename(columns={'host_taxids': 'uniprot_organism_id'}) \
            .to_sql(up.uniprot__uniprot_host.name, self.engine, if_exists='append', index=False, chunksize=100000)

        logger.info(f"start insert {up.uniprot__uniprot_xref.name}")
        df[['xref_ids', 'uniprot_id']].explode('xref_ids').dropna().rename(columns={'xref_ids': 'uniprot_xref_id'}) \
            .to_sql(up.uniprot__uniprot_xref.name, self.engine, if_exists='append', index=False, chunksize=100000)

        logger.info(f"start insert {up.uniprot__uniprot_subcellular_location.name}")
        df[['subcellular_location_ids', 'uniprot_id']].explode('subcellular_location_ids').dropna() \
            .rename(columns={'subcellular_location_ids': 'uniprot_subcellular_location_id'}) \
            .to_sql(up.uniprot__uniprot_subcellular_location.name, self.engine, if_exists='append', index=False,
                    chunksize=100000)

        return df.shape[0]

    def update_interactions(self) -> int:
        """Abstract method."""
        pass
