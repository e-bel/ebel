"""IntAct module."""
import logging
import zipfile
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import INTACT
from ebel.manager.orientdb.biodbs.uniprot import UniProt
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import intact, uniprot


logger = logging.getLogger(__name__)


class IntAct(odb_meta.Graph):
    """IntAct."""

    def __init__(self, client: OrientDB = None, condition_keyword="Alzheimer"):
        """Init IntAct."""
        self.condition_keyword = condition_keyword
        self.client = client
        self.biodb_name = INTACT
        self.urls = {self.biodb_name: urls.INTACT}
        self.file_path = get_file_path(urls.INTACT, self.biodb_name)
        super().__init__(edges=odb_structure.intact_edges,
                         indices=odb_structure.intact_indices,
                         tables_base=intact.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    @staticmethod
    def _intact_list_to_dict(string_list: str) -> dict:
        dict_values = dict()
        split_values = [x.split(":", 1) for x in string_list.split("|")]
        for values in split_values:

            if len(values) == 2:
                key, val = values[0], values[1]

                if key in dict_values:
                    dict_values[key].append(val)
                else:
                    dict_values[key] = [val]

        return dict_values

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class."""
        self.recreate_tables()

        logger.info("Reading and formatting IntAct data.")

        zf = zipfile.ZipFile(self.file_path)

        usecols = {'#ID(s) interactor A': "int_a_uniprot_id",
                   'ID(s) interactor B': "int_b_uniprot_id",
                   'Publication Identifier(s)': "pmid",
                   'Interaction type(s)': "it",
                   'Interaction identifier(s)': "interaction_ids",
                   'Confidence value(s)': "confidence_value",
                   'Interaction detection method(s)': "dm"
                   }

        df = pd.read_csv(zf.open('intact.txt'), sep="\t", usecols=usecols.keys())
        df.rename(columns=usecols, inplace=True)
        regex_accession = r'uniprotkb:([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})'
        df.int_a_uniprot_id = df.int_a_uniprot_id.str.extract(regex_accession)[0]
        df.int_b_uniprot_id = df.int_b_uniprot_id.str.extract(regex_accession)[0]
        df = df[(pd.notnull(df.int_a_uniprot_id) & pd.notnull(df.int_b_uniprot_id))]
        regex_detection_method = r"psi-mi:\"MI:0*(?P<detection_method_psimi_id>\d+)\"\((?P<detection_method>[^)]+)\)"
        df = df.join(df.dm.str.extract(regex_detection_method), how='left')
        df.drop(columns=['dm'], inplace=True)
        df.pmid = df.pmid.str.extract(r"pubmed:(\d+)")
        regex_interaction_type = r"psi-mi:\"MI:0*(?P<interaction_type_psimi_id>\d+)\"\((?P<interaction_type>[^)]+)\)"
        df = df.join(df.it.str.extract(regex_interaction_type), how='left')
        df.drop(columns=['it'], inplace=True)
        df.confidence_value = df.confidence_value.str.extract(r'intact-miscore:(\d+(\.\d+)?)')[0]
        df.index += 1
        df.index.rename('id', inplace=True)

        df.to_sql(intact.Intact.__tablename__, self.engine, if_exists='append')

        self.session.commit()

        return {self.biodb_name: df.shape[0]}

    def get_create_rid_by_uniprot(self, uniprot_accession: str, uniprot_rid_dict: dict) -> str:
        """Create or get rID entry for a given UniProt ID.

        Parameters
        ----------
        uniprot_accession: str
            UniProt accession number.
        uniprot_rid_dict: dict
            Entry parameters matching those of the desired rID entry.

        Returns
        -------
        str
            UniProt accession ID.
        """
        if uniprot_accession not in uniprot_rid_dict:
            nn = self.get_namespace_name_by_uniprot(uniprot_accession)
            if nn:
                namespace, name = nn
                value_dict = {'name': name,
                              'namespace': namespace,
                              'pure': True, 'bel': f'p({namespace}:"{name}")',
                              'uniprot': uniprot_accession}
                uniprot_rid_dict[uniprot_accession] = self.get_create_rid('protein', value_dict, check_for='bel')
        return uniprot_rid_dict.get(uniprot_accession)

    def get_namespace_name_by_uniprot(self, uniprot_accession: str) -> tuple:
        """Get the namespace of a given UniProt ID.

        Parameters
        ----------
        uniprot_accession: str
            UniProt accession number.

        Returns
        -------
        tuple
            namespace, value
        """
        return_value = ()
        sql = f"""Select s.symbol, u.taxid from uniprot u inner join uniprot_gene_symbol s
                  on (u.id=s.uniprot_id) where u.accession='{uniprot_accession}' limit 1"""
        result = self.engine.execute(sql).fetchone()
        taxid_to_namespace = {9606: 'HGNC', 10090: 'MGI', 10116: 'RGD'}
        if result:
            name, taxid = result
            namespace = taxid_to_namespace.get(taxid, 'UNIPROT')
            return_value = (namespace, name)
        else:
            if self.session.query(uniprot.Uniprot).filter(uniprot.Uniprot.accession == uniprot_accession).first():
                return_value = ('UNIPROT', uniprot_accession)
        return return_value

    def update_interactions(self) -> int:
        """Update intact interactions to graph."""
        uniprot = UniProt(self.client)
        uniprot.update()

        uniprot_rid_dict = uniprot.get_pure_uniprot_rid_dict_in_bel_context()

        sql_temp = """SELECT
            int_a_uniprot_id,
            int_b_uniprot_id,
            pmid,
            interaction_ids,
            interaction_type,
            interaction_type_psimi_id,
            detection_method,
            detection_method_psimi_id,
            confidence_value
        FROM
            intact
        WHERE
            int_a_uniprot_id = '{uniprot_accession}' or int_b_uniprot_id = '{uniprot_accession}'
        GROUP BY
            int_a_uniprot_id,
            int_b_uniprot_id,
            pmid,
            interaction_ids,
            interaction_type,
            interaction_type_psimi_id,
            detection_method,
            detection_method_psimi_id,
            confidence_value"""

        updated = 0

        uniprot_accessions = tuple(uniprot_rid_dict.keys())

        for uniprot_accession in tqdm(uniprot_accessions, desc="Update IntAct interactions"):
            sql = sql_temp.format(uniprot_accession=uniprot_accession)
            result = self.engine.execute(sql)

            for up_a, up_b, pmid, ia_ids, ia_type, ia_type_id, d_method, d_method_id, c_value in result.fetchall():
                from_rid = self.get_create_rid_by_uniprot(up_a, uniprot_rid_dict)
                to_rid = self.get_create_rid_by_uniprot(up_b, uniprot_rid_dict)

                if from_rid and to_rid:
                    value_dict = {'interaction_type': ia_type,
                                  'interaction_type_psimi_id': ia_type_id,
                                  'detection_method': d_method,
                                  'detection_method_psimi_id': d_method_id,
                                  'interaction_ids': dict([x.split(':', 1) for x in ia_ids.split('|')]),
                                  'confidence_value': float(c_value),
                                  'pmid': pmid}

                    self.create_edge(class_name='has_ppi_ia',
                                     from_rid=from_rid,
                                     to_rid=to_rid,
                                     value_dict=value_dict)

                    updated += 1

        return updated
