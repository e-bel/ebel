"""ClinVar."""
import logging
import pandas as pd

from tqdm import tqdm
from pyorientdb import OrientDB
from typing import Dict, List
from collections import namedtuple

from ebel.manager.orientdb.constants import CLINVAR
from ebel.manager.orientdb import odb_meta, urls, odb_structure
from ebel.tools import get_file_path, get_disease_trait_keywords_from_config

from ebel.manager.rdbms.models import clinvar


logger = logging.getLogger(__name__)

Snp = namedtuple('Snp', ('keyword',
                         'phenotype',
                         'rs_number',
                         'hgnc_id',
                         'chromosome',
                         'position',
                         'clinical_significance'))


class ClinVar(odb_meta.Graph):
    """ClinVar (from NCBI)."""

    def __init__(self, client: OrientDB = None):
        """Init ClinVar."""
        self.client = client
        self.biodb_name = CLINVAR
        self.urls = {self.biodb_name: urls.CLINVAR}
        self.file_path = get_file_path(urls.CLINVAR, self.biodb_name)
        super().__init__(nodes=odb_structure.clinvar_nodes,
                         edges=odb_structure.clinvar_edges,
                         indices=odb_structure.clinvar_indices,
                         urls=self.urls,
                         tables_base=clinvar.Base,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def insert_data(self) -> Dict[str, int]:
        """Insert data."""
        inserted = {}
        self.recreate_tables()
        df = pd.read_csv(self.file_path, sep="\t", low_memory=False)
        self._standardize_dataframe(df)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.drop(columns=['phenotype_ids', 'phenotype_list', 'other_ids']).to_sql(
            self.biodb_name, self.engine, if_exists='append', chunksize=10000)

        df_clinvar__phenotype = df['phenotype_list'].str.split(r'[|;]').explode().to_frame() \
            .reset_index().rename(columns={'phenotype_list': 'phenotype', 'id': 'clinvar_id'})
        df_clinvar__phenotype.index += 1
        df_phenotype = pd.DataFrame(df_clinvar__phenotype.phenotype.unique(), columns=['phenotype'])
        df_phenotype.index += 1
        df_phenotype.index.rename('id', inplace=True)
        df_phenotype.to_sql(clinvar.ClinvarPhenotype.__tablename__, self.engine, if_exists='append')
        inserted.update({clinvar.ClinvarPhenotype.__tablename__: df_phenotype.shape[0]})

        df_clinvar__phenotype = df_clinvar__phenotype.set_index('phenotype').join(
            df_phenotype.assign(clinvar_phenotype_id=df_phenotype.index).set_index('phenotype')
        ).reset_index().loc[:, ['clinvar_id', 'clinvar_phenotype_id']]

        df_clinvar__phenotype.index += 1
        df_clinvar__phenotype.index.rename('id', inplace=True)
        df_clinvar__phenotype.to_sql('clinvar__phenotype', self.engine, if_exists='append', index=False)
        inserted.update({clinvar.clinvar__clinvar_phenotype.__dict__['fullname']: df_clinvar__phenotype.shape[0]})

        clinvar_pheno_medgen = df['phenotype_ids'].str.split(r'[|,;]').explode().str.partition(':')[[0, 2]] \
            .rename(columns={0: 'db', 2: 'identifier'})
        clinvar_pheno_medgen['clinvar_id'] = clinvar_pheno_medgen.index
        clinvar_phenotype_medgen = clinvar_pheno_medgen.set_index('db').loc['MedGen'].reset_index().drop(
            columns=['db'])
        clinvar_phenotype_medgen.index += 1
        clinvar_phenotype_medgen.index.rename('id', inplace=True)
        clinvar_phenotype_medgen.to_sql(clinvar.ClinvarPhenotypeMedgen.__tablename__, self.engine, if_exists='append')
        inserted.update({clinvar.ClinvarPhenotypeMedgen.__tablename__: clinvar_phenotype_medgen.shape[0]})

        df_other_ids = df.other_ids.str.split(',').dropna().explode().str.partition(':')[[0, 2]].reset_index().rename(
            columns={0: 'db', 2: 'identifier', 'id': 'clinvar_id'}).rename_axis("id")
        df_other_ids.index += 1
        df_other_ids.to_sql(clinvar.ClinvarOtherIdentifier.__tablename__, self.engine, if_exists='append')
        inserted.update({clinvar.ClinvarOtherIdentifier.__tablename__: df_other_ids.shape[0]})
        return inserted

    def update_bel(self) -> int:
        """Delete and updates all ClinVar edges."""
        logger.info(f"Clear edges for {self.biodb_name.upper()}")
        self.clear_edges()
        logger.info("Clear nodes without edges")
        self.clear_nodes_with_no_edges()

        added_edges = self.update_interactions()
        logger.info(f"Successfully updated interactions for {self.biodb_name.upper()}")
        return added_edges

    def get_disease_snps_dict(self) -> Dict[str, List[Snp]]:
        """Get a dictionary {'disease':[snp,snp,... ]} by disease names."""
        disease_keywords = get_disease_trait_keywords_from_config()

        sql_temp = """Select
            '{keyword}',
            phenotype,
            rs_db_snp as rs_number,
            hgnc_id,
            chromosome,
            start as position,
            clinical_significance
                from clinvar c inner join
                clinvar__phenotype cp on (c.id=cp.clinvar_id) inner JOIN
                clinvar_phenotype p on (cp.clinvar_phenotype_id=p.id)
            where
                p.phenotype like '%%{keyword}%%'
                and rs_db_snp != -1"""

        results = dict()
        for kwd in disease_keywords:
            sql = sql_temp.format(keyword=kwd)
            rows = self.engine.execute(sql)
            results[kwd] = [Snp(*x) for x in rows.fetchall()]

        return results

    def update_interactions(self) -> int:
        """Create SNPs and edges using information from ClinVar."""
        # snp is upstream of a downstream gene
        snp_type = {'mapped': "mapped", 'downstream': "upstream", 'upstream': "downstream"}
        added_edges = 0
        disease_snps_dict = self.get_disease_snps_dict()
        hgnc_id_gene_rid_cache = {}

        for disease, rows in disease_snps_dict.items():

            for snp in tqdm(rows, desc=f'Add has_X_snp_cv edges to BEL for {disease}'):
                if snp.hgnc_id in hgnc_id_gene_rid_cache:
                    gene_mapped_rid = hgnc_id_gene_rid_cache[snp.hgnc_id]
                else:
                    gene_mapped_rid = self._get_set_gene_rid(hgnc_id=snp.hgnc_id)
                    hgnc_id_gene_rid_cache[snp.hgnc_id] = gene_mapped_rid

                if gene_mapped_rid:
                    snp_rid = self.get_create_rid('snp', {'rs_number': "rs" + str(snp.rs_number)})
                    value_dict = {'clinical_significance': snp.clinical_significance,
                                  'phenotype': snp.phenotype,
                                  'keyword': snp.keyword}
                    self.create_edge(class_name='has_mapped_snp_cv',
                                     from_rid=gene_mapped_rid,
                                     to_rid=snp_rid,
                                     value_dict=value_dict,
                                     if_not_exists=True)
                    added_edges += 1

                    # fetch all down and upstream gene_rids
                    gene_type_rids = self.get_set_gene_rids_by_position(
                        chromosome=snp.chromosome,
                        position=snp.position,
                        gene_types=['downstream', 'upstream']
                    )

                    for gene_type, gene_rids in gene_type_rids.items():
                        for gene_rid in gene_rids:
                            class_name = f"has_{snp_type[gene_type]}_snp_cv"
                            self.create_edge(class_name=class_name,
                                             from_rid=gene_rid,
                                             to_rid=snp_rid,
                                             value_dict=value_dict)
                            added_edges += 1
        return added_edges

    def _get_set_gene_rid(self, hgnc_id: str):
        """Insert gene (if not exists) and returns OrientDB @rid."""
        gene_rid = None

        hgnc_rids = self.query_class('hgnc', columns=['symbol'], limit=1, id=hgnc_id)

        if hgnc_rids:
            gene = hgnc_rids[0]
            bel = f'g(HGNC:"{gene["symbol"]}")'
            data = {'pure': True,
                    'bel': bel,
                    'name': gene['symbol'],
                    'namespace': "HGNC"
                    }
            gene_rid = self.get_create_rid('gene', data, check_for='bel')

        return gene_rid
