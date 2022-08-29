"""NSIDES module."""

import tarfile
import logging
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.tools import get_file_path
from ebel.constants import RID
from ebel.manager.orientdb.constants import OFFSIDES, ONSIDES
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import nsides

logger = logging.getLogger(__name__)
pd.options.mode.chained_assignment = None

class Nsides(odb_meta.Graph):
    """Drug side effects and drug-drug interactions were mined from publicly available data.

    Offsides is a database
    of drug side effects that were found, but are not listed on the official FDA label. Twosides is the only
    comprehensive database drug-drug-effect relationships. Over 3,300 drugs and 63,000 combinations connected to
    millions of potential adverse reactions.

    Onsides is a database of adverse reactions and boxed warnings extracted from the FDA structured product labels.
    All labels available to download from DailyMed
    (https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm) as of April 2022 were processed in
    this analysis. In total 2.7 million adverse reactions were extracted from 42,000 labels for just
    under 2,000 drug ingredients or combination of ingredients.

    More information can be found on http://tatonettilab.org/offsides/
    """

    def __init__(self, client: OrientDB = None):
        """Init nSIDES."""
        self.client = client
        self.biodb_name = 'nsides'
        self.urls = {OFFSIDES: urls.OFFSIDES, ONSIDES: urls.ONSIDES}
        super().__init__(edges=odb_structure.nsides_edges,
                         nodes=odb_structure.nsides_nodes,
                         tables_base=nsides.Base,
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
        source  string  The database the information was derived from: OFFSIDES or OnSIDES
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
        offsides_df = pd.read_csv(file_path, low_memory=False)
        # Because of repeating header, we have to delete all rows which are equal to the columns
        offsides_df = offsides_df[offsides_df.ne(offsides_df.columns).any(1)]
        offsides_df.drop_duplicates(inplace=True)
        offsides_df["source"] = "offsides"
        offsides_df.columns = self._standardize_column_names(offsides_df.columns)

        onsides_df = self.__import_onsides()
        combined_df = pd.concat([offsides_df, onsides_df], ignore_index=True, sort=False)

        combined_df.index += 1
        combined_df.index.rename('id', inplace=True)
        combined_df.to_sql(
            nsides.Nsides.__tablename__,
            self.engine,
            if_exists='replace',
            chunksize=10000
        )
        return {self.biodb_name: combined_df.shape[0]}

    def __import_onsides(self):
        """Extract OnSIDES CSV file and format into a DF."""
        file_path = get_file_path(self.urls[ONSIDES], self.biodb_name)
        with tarfile.open(file_path, "r:*") as tar:
            df = pd.read_csv(tar.extractfile("csv/adverse_reactions.csv"), header=0).drop_duplicates()

        df.drop(  # Remove columns that aren't needed
            ['xml_id', 'Unnamed: 10', "omop_concept_id", "drug_concept_ids", "concept_class_id"],
            inplace=True,
            axis=1,
        )

        df.rename(columns={  # Rename columns to match OFFSIDES
            "rxnorm_ids": "drug_rxnorn_id",
            "concept_name": "condition_concept_name",
            "meddra_id": "condition_meddra_id",
            "ingredients": "drug_concept_name",
        }, inplace=True)

        # Keep rows with only 1 ingredient/drug
        single_value_mask = df['drug_concept_name'].apply(lambda x: len(x.split(",")) == 1)
        pruned_df = df.loc[single_value_mask]
        pruned_df["source"] = "onsides"
        return pruned_df

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
            nsides as o on (dei.identifier=o.drug_rxnorn_id)
        where
            d.drugbank_id='{}' and resource='RxCUI' and (mean_reporting_frequency>=0.01 OR mean_reporting_frequency is NULL)
        group by
            o.condition_meddra_id,
            o.condition_concept_name,
            o.prr,
            o.mean_reporting_frequency
        """

        drugbank_ids = self.query_class('drug', columns=['drugbank_id'], drugbank_id='notnull')
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
        """Update edges with NSIDES metadata."""
        # not implemented because update_bel is implemented
        pass
