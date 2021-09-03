"""OFFSIDES module."""

import logging
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorient import OrientDB

from ebel.tools import get_file_path
from ebel.constants import RID
from ebel.manager.orientdb.constants import OFFSIDES
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import offsides

logger = logging.getLogger(__name__)


class Offsides(odb_meta.Graph):
    """Drug side effects and drug-drug interactions were mined from publicly available data.

    Offsides is a database
    of drug side-effects that were found, but are not listed on the official FDA label. Twosides is the only
    comprehensive database drug-drug-effect relationships. Over 3,300 drugs and 63,000 combinations connected to
    millions of potential adverse reactions.

    More information can be found on http://tatonettilab.org/offsides/
    """

    def __init__(self, client: OrientDB = None):
        """Init SIDER."""
        self.client = client
        self.biodb_name = OFFSIDES
        self.urls = {OFFSIDES: urls.OFFSIDES}
        super().__init__(edges=odb_structure.offsides_edges,
                         nodes=odb_structure.offsides_nodes,
                         tables_base=offsides.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class.

        Columns:

        drug_rxnorn_id 	integer 	RxNorm CUI (RxCUI) of each drug
        drug_concept_name 	string 	String name of each drug
        condition_meddra_id 	integer 	MedDRA code of each (adverse event) condition
        condition_concept_name 	string 	String name of each condition
        A 	integer 	Number of reports prescribed the drug that had the condition
        B 	integer 	Number of reports prescribed the drug that did not have the condition
        C 	integer 	Number of reports not prescribed the drug† that had the condition
        D 	integer 	Number of reports not prescribed the drug† that did not have the condition
        PRR 	float 	Proportional reporting ratio*
        PRR_error 	float 	Proportional reporting ratio error*
        mean_reporting_frequency 	float 	a / (a + b)

        Further documentation see here:
        https://github.com/tatonetti-lab/nsides-release/blob/master/release-notes/v0.1.md
        """
        file_path = get_file_path(self.urls[OFFSIDES], self.biodb_name)
        df = pd.read_csv(file_path, low_memory=False)
        # Because of repeating header, we have to delete all rows which are equal to the columns
        df = df[df.ne(df.columns).any(1)]
        df.drop_duplicates(inplace=True)
        df.columns = self._standardize_column_names(df.columns)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(offsides.Offsides.__tablename__,
                  self.engine,
                  if_exists='append',
                  chunksize=10000)
        return {self.biodb_name: df.shape[0]}

    def update_bel(self) -> int:
        """Create has_side_effect edges between drugs (drugbank) and side_effects.

        RxCUI (https://rxnav.nlm.nih.gov/RxNormAPIs.html#) is used as the mapping identifier.
        """
        self.clear_edges()
        self.delete_nodes_with_no_edges('side_effect')
        self.delete_nodes_with_no_edges('drug')

        # TODO: Translate to sqlalchemy query
        sql_temp = """Select
            o.condition_meddra_id,
            o.condition_concept_name,
            o.prr,
            o.mean_reporting_frequency
        from
            drugbank as d inner join
            drugbank_external_identifier as dei on (d.id=dei.drugbank_id) inner join
            offsides as o on (dei.identifier=o.drug_rxnorn_id)
        where
            d.drugbank_id='{}' and resource='RxCUI' and mean_reporting_frequency>=0.01
        group by
            o.condition_meddra_id,
            o.condition_concept_name,
            o.prr,
            o.mean_reporting_frequency
        """

        drugbank_ids = self.query_class('drug', columns=['drugbank_id'])
        drugbank_id_rids = {d['drugbank_id']: d[RID] for d in drugbank_ids}

        side_effects = self.query_class('side_effect', columns=['condition_meddra_id'])
        side_effect_rids = {d['condition_meddra_id']: d[RID] for d in side_effects}

        updated = 0

        for drugbank_id, drugbank_rid in tqdm(drugbank_id_rids.items(), desc=f'Update {self.biodb_name.upper()}'):
            for r in self.engine.execute(sql_temp.format(drugbank_id)):
                (condition_meddra_id,
                 condition_concept_name,
                 prr,
                 mean_reporting_frequency) = r

                if condition_meddra_id not in side_effect_rids:
                    side_effect_rid = self.insert_record(
                        'side_effect',
                        {
                            'label': condition_concept_name,
                            'condition_meddra_id': condition_meddra_id
                        }
                    )
                    side_effect_rids[condition_meddra_id] = side_effect_rid

                value_dict = {
                    'prr': prr,
                    'mean_reporting_frequency': mean_reporting_frequency
                }
                side_effect_rid = side_effect_rids[condition_meddra_id]
                self.create_edge(class_name='has_side_effect',
                                 from_rid=drugbank_rid,
                                 to_rid=side_effect_rid,
                                 value_dict=value_dict)
                updated += 1
        return updated

    def update_interactions(self) -> int:
        """Update edges with OFFSIDES metadata."""
        # not implemented because update_bel is implemented
        pass
