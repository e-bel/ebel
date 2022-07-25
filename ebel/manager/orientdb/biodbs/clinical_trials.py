"""Clinical Trials."""
import logging

import pandas as pd

from tqdm import tqdm
from lxml import etree
from zipfile import ZipFile
from pyorientdb import OrientDB
from typing import Dict, Optional
from collections import namedtuple


from ebel import tools
from ebel.constants import RID
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.orientdb.constants import CLINICAL_TRIALS

from ebel.manager.rdbms.models import clinical_trials_gov


Intervention = namedtuple('Intervention', ['intervention_type', 'intervention_name'])

logger = logging.getLogger(__name__)


class ClinicalTrials(odb_meta.Graph):
    """ClinicalTrials.gov."""

    def __init__(self, client: OrientDB = None, condition_keyword="Alzheimer"):
        """Init ClinicalTrials."""
        self.condition_keyword = condition_keyword
        self.client = client
        self.biodb_name = CLINICAL_TRIALS
        self.url = urls.CLINICAL_TRIALS_GOV
        self.urls = {self.biodb_name: self.url}
        self.file_path = tools.get_file_path(urls.CLINICAL_TRIALS_GOV, self.biodb_name)
        super().__init__(tables_base=clinical_trials_gov.Base,
                         # nodes=odb_structure.clinical_trials_gov_nodes,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def add_link_to_drugbank(self, data_dict: dict, trial_rid: str):
        """Create LINKSET in drugbank table for associated clinical trials."""
        # Can't check synonyms untils OrientDB 3.0, need to be able to index on collections
        # update_sql = 'UPDATE drugbank ADD clinical_trials = {} WHERE name = "{}" OR "{}" in synonyms'
        # TODO index drugbank.synonyms

        results = self.query_class(class_name='drugbank', limit=1)  # Check if drugbank is there

        if results:
            update_sql = 'UPDATE drugbank ADD clinical_trials = {} WHERE name = "{}"'

            if 'drugs_in_trial' in data_dict.keys():
                for drug in data_dict['drugs_in_trial']:
                    drug = drug.replace('"', "'")  # Have to scrub the string
                    # self.execute(update_sql.format(trial_rid, drug, drug))
                    self.execute(update_sql.format(trial_rid, drug))

    def insert_n2m_tables(self):
        """Inserts mesh_terms and keywords."""
        with ZipFile(self.file_path, "r") as zip_file:
            xml_files = [x for x in zip_file.filelist if x.filename.endswith('.xml')]

            d = {'keyword': set(), 'mesh_term': set(), 'condition': set(), 'intervention': set()}
            interventions = set()

            for f in tqdm(xml_files, desc="Get and set unique values tables in ClinicalTrials.gov"):

                with zip_file.open(f.filename) as xml_file:
                    xml_content = xml_file.read()

                doc = etree.fromstring(xml_content)

                for child in doc:
                    if child.tag in ['keyword', 'condition']:
                        d[child.tag].add(child.text)

                    elif child.tag == 'condition_browse':
                        d['mesh_term'].update(set(child.xpath('./mesh_term//text()')))

                    elif child.tag == 'intervention':
                        itype, iname = self.__parse_intervention(child)
                        interventions.add(
                            Intervention(
                                intervention_type=(itype.strip() if itype else itype),
                                intervention_name=(iname.strip() if iname else iname)
                            )
                        )

        df_interventions = pd.DataFrame(interventions)
        df_interventions.index += 1
        df_interventions.index.rename('id', inplace=True)
        df_interventions.to_sql(
            clinical_trials_gov.Intervention.__tablename__,
            self.engine,
            if_exists="append"
        )

        for column_name, data in d.items():
            df = pd.DataFrame(data, columns=[column_name])
            df.index += 1
            df.index.rename('id', inplace=True)
            df.to_sql(
                'clinical_trials_gov_' + column_name,
                self.engine,
                if_exists='append'
            )

    @staticmethod
    def __parse_intervention(interventions) -> tuple:
        """Extract the intervention type and intervention name from the xml child."""
        intervention = dict()

        for cchild in interventions:
            intervention[cchild.tag] = cchild.text.strip()

        itype = intervention.get('intervention_type')
        iname = intervention.get('intervention_name')

        return itype, iname

    @staticmethod
    def __get_first(element: list) -> Optional[str]:
        if len(element):
            return str(element[0])

    def insert_mesh_terms(self, df):
        """Insert mesh_terms into database."""
        columns = {'id': 'clinical_trials_gov_id',
                   'mesh_terms': 'clinical_trials_gov_mesh_term_id'}
        table = clinical_trials_gov.ctg_mesh_term_n2m.name
        df[['mesh_terms', 'id']] \
            .explode('mesh_terms') \
            .rename(columns=columns).to_sql(table, index=False, if_exists='append', con=self.engine)

    def insert_keywords(self, df):
        """Insert keywords into database."""
        columns = {'id': 'clinical_trials_gov_id',
                   'keywords': 'clinical_trials_gov_keyword_id'}
        table = clinical_trials_gov.ctg_keyword_n2m.name
        df[['keywords', 'id']] \
            .explode('keywords') \
            .rename(columns=columns).to_sql(table, index=False, if_exists='append', con=self.engine)

    def insert_conditions(self, df):
        """Insert conditions into database."""
        columns = {'id': 'clinical_trials_gov_id',
                   'conditions': 'clinical_trials_gov_condition_id'}
        table = clinical_trials_gov.ctg_condition_n2m.name
        df[['conditions', 'id']] \
            .explode('conditions') \
            .rename(columns=columns).to_sql(table, index=False, if_exists='append', con=self.engine)

    def insert_interventions(self, df):
        """Insert interventions into database."""
        columns = {'id': 'clinical_trials_gov_id',
                   'interventions': 'clinical_trials_gov_intervention_id'}
        table = clinical_trials_gov.ctg_intervention_n2m.name
        df[['interventions', 'id']] \
            .explode('interventions') \
            .rename(columns=columns).to_sql(table, index=False, if_exists='append', con=self.engine)

    def insert_data(self) -> Dict[str, int]:
        """Insert Clinical Trial metadata into database."""
        self.recreate_tables()
        with ZipFile(self.file_path, "r") as zip_file:
            xml_files = [x for x in zip_file.filelist if x.filename.endswith('.xml')]

            self.insert_n2m_tables()
            conditions = {x.condition: x.id for x in self.session.query(clinical_trials_gov.Condition).all()}
            keywords = {x.keyword: x.id for x in self.session.query(clinical_trials_gov.Keyword).all()}
            mesh_terms = {x.mesh_term: x.id for x in self.session.query(clinical_trials_gov.MeshTerm).all()}
            interventions = {(x.intervention_type, x.intervention_name): x.id for x in
                             self.session.query(clinical_trials_gov.Intervention).all()}

            trials = []
            index = 0

            for index, f in tqdm(enumerate(xml_files, 1),
                                 desc=f"Import {self.biodb_name.upper()}",
                                 total=len(xml_files)):

                with zip_file.open(f.filename) as xml_file:
                    xml_content = xml_file.read()

                doc = etree.fromstring(xml_content)
                data_dict = self.get_data_as_dict(doc, conditions, keywords, mesh_terms, interventions)
                data_dict['id'] = index
                trials.append(data_dict)

                if index % 10000 == 0:
                    self.insert_trials(trials)
                    trials = []

            self.insert_trials(trials)

        return {self.biodb_name: index}

    def insert_trials(self, trials):
        """Insert select Clinical Trial entries into database."""
        cols_multi = ['primary_outcomes', 'secondary_outcomes', 'interventions',
                      'mesh_terms', 'keywords', 'conditions']
        df = pd.DataFrame(trials)
        cols = list(set(df.columns) - set(cols_multi))
        df[cols].to_sql(clinical_trials_gov.ClinicalTrialGov.__tablename__, self.engine, if_exists='append',
                        index=False)
        self.insert_mesh_terms(df)
        self.insert_keywords(df)
        self.insert_conditions(df)
        self.insert_interventions(df)

    def get_data_as_dict(self, doc, conditions, keywords, mesh_terms, interventions):
        """Get metadata as dict based on passed parameters."""
        d = {'primary_outcomes': [], 'secondary_outcomes': [], 'keywords': [], 'conditions': [], 'interventions': [],
             'mesh_terms': []}
        for child in doc:
            if child.tag == 'id_info':
                d['nct_id'] = self.__get_first(child.xpath('./nct_id[1]/text()'))
                d['org_study_id'] = self.__get_first(child.xpath('./org_study_id[1]/text()'))

            elif child.tag in ['brief_title', 'official_title', 'overall_status', 'start_date', 'completion_date',
                               'phase', 'study_type']:
                d[child.tag] = child.text

            elif child.tag in ['brief_summary', 'detailed_description']:
                d[child.tag] = self.__get_first(child.xpath('./textblock[1]/text()'))

            elif child.tag == 'oversight_info':
                d['is_fda_regulated_drug'] = self.__get_first(child.xpath('./is_fda_regulated_drug[1]/text()'))

            elif child.tag == 'condition':
                d['conditions'].append(conditions[child.text])

            elif child.tag == 'condition_browse':
                d['mesh_terms'] = [mesh_terms[x] for x in child.xpath('./mesh_term//text()')]

            elif child.tag == 'study_design_info':
                d['study_design_intervention_model'] = self.__get_first(child.xpath('./intervention_model[1]/text()'))
                d['study_design_primary_purpose'] = self.__get_first(child.xpath('./primary_purpose[1]/text()'))
                d['study_design_masking'] = self.__get_first(child.xpath('./masking[1]/text()'))

            elif child.tag in ['primary_outcome', 'secondary_outcome']:
                outcomes = dict()
                for cchild in child:
                    outcomes[cchild.tag] = cchild.text
                d[child.tag + "s"] = outcomes

            elif child.tag == 'keyword':
                d['keywords'].append(keywords[child.text])

            elif child.tag == 'intervention':
                itype, iname = self.__parse_intervention(child)
                formatted_intervention = interventions[(itype, iname)]
                d['interventions'].append(formatted_intervention)

            elif child.tag == 'patient_data':
                d['patient_data_sharing_ipd'] = self.__get_first(child.xpath('./sharing_ipd[1]/text()'))
                d['patient_data_ipd_description'] = self.__get_first(child.xpath('./ipd_description[1]/text()'))

        return d

    def update_bel(self):
        """Update the BEL relations with links to pathologies."""
        # TODO FIX: Too slow!! Need to be able to index on collections
        # self.update_pathology_links()
        pass

    def update_pathology_links(self) -> int:
        """Update the pathology class to link to associated clinical trials."""
        trial_sql = "SELECT @rid.asString() FROM clinical_trial WHERE '{}' in mesh_conditions"
        update_sql = "UPDATE {} SET clinical_trials = {}"

        paths = self.query_class(class_name='pathology', columns=['name'], )

        updated = 0
        for path in tqdm(paths, desc="Update pathology nodes"):
            path_rid, path_name = path[RID], path['name']

            trial_results = self.client.query(trial_sql.format(path_name))
            trial_rids = [x.oRecordData[RID] for x in trial_results]
            trial_linkset = "[" + ",".join(trial_rids) + "]"  # This feature is a LINKSET

            self.execute(update_sql.format(path_rid, trial_linkset))
            updated += 1

        return updated

    def update_interactions(self) -> int:
        """Abstract method."""
        pass
