"""DrugBank."""

import os
import platform
import re
import signal
import getpass
import os.path
import logging
import requests

from time import time
from tqdm import tqdm
from typing import Dict
from zipfile import ZipFile
from datetime import datetime
from pyorientdb import OrientDB
from lxml.etree import iterparse
from collections import namedtuple
from configparser import ConfigParser

from ebel.constants import DATA_DIR, RID
from ebel.defaults import config_file_path
from ebel.manager.orientdb.constants import DRUGBANK
from ebel.config import write_to_config, get_config_as_dict
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import drugbank

ACTIONS = 'actions'
SYMBOLS = 'symbols'
KNOWN_ACTION = 'known_action'

logger = logging.getLogger(__name__)

XML_URL = 'http://www.drugbank.ca'
XML_NAMESPACE = f'{{{XML_URL}}}'
XN = {"n": XML_URL}

Xpath = namedtuple('Xpath', ('references', 'synonyms', 'product_names', 'pathways', 'target_known_action',
                             'ex_ids_resourec', 'ex_ids_id', 'target_actions', 'target_uniprot'))


class DrugBank(odb_meta.Graph):
    """Drugbank."""

    def __init__(self, client: OrientDB = None):
        """Drugbank database.

        documentation: https://www.drugbank.ca/documentation
        """
        self.client = client
        self.biodb_name = DRUGBANK
        self.urls = {'drugbank_version': urls.DRUGBANK_VERSION, self.biodb_name: urls.DRUGBANK_DATA}
        super().__init__(nodes=odb_structure.drugbank_nodes,
                         edges=odb_structure.drugbank_edges,
                         tables_base=drugbank.Base,
                         indices=odb_structure.drugbank_indices,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

        self.biodb_dir = os.path.join(DATA_DIR, self.biodb_name)
        os.makedirs(self.biodb_dir, exist_ok=True)

        self.file_path = os.path.join(self.biodb_dir, 'drugbank_all_full_database.xml.zip')
        self.file_name_unzipped = 'full database.xml'
        self.file_path_unzipped = os.path.join(self.biodb_dir, self.file_name_unzipped)

        self.xpath_pattern = Xpath(
            references='./n:articles/n:article/n:pubmed-id/text()',
            synonyms='./n:synonym/text()',
            product_names='./n:product/n:name/text()',
            ex_ids_resourec='./n:resource[1]/text()',
            ex_ids_id='./n:identifier[1]/text()',
            target_actions='./n:actions[1]/n:action[1]/text()',
            target_known_action='./n:known-action[1]/text()',
            target_uniprot="./n:polypeptide[@source='Swiss-Prot']/@id",
            pathways='./n:pathway/n:smpdb-id/text()'
        )

    def __len__(self):
        """Get number of 'has_drug_target' graph edges."""
        return self.execute("Select count(*) from has_drug_target")[0].oRecordData['count']

    def __contains__(self, unique_identifier):
        """Check if drug with identifier '?' exists in graph."""
        pass

    def _unzip_file(self):
        logger.info(f'unzip {self.file_path}')
        with ZipFile(self.file_path, 'r') as zip_ref:
            zip_ref.extract(self.file_name_unzipped, self.biodb_dir)

    def insert_data(self) -> Dict[str, int]:
        """Insert data and returns number of inserts."""
        logger.info('Insert DrugBank data')

        self._unzip_file()

        drug_index = 0
        columns = ['name', 'description', 'cas-number', 'unii', 'state', 'indication', 'pharmacodynamics',
                   'toxicity', 'metabolism', 'absorption', 'half-life', 'route-of-elimination',
                   'volume-of-distribution', 'clearance', 'mechanism-of-action', 'fda-label']

        doc = iterparse(self.file_path_unzipped, events=('end',), tag=f'{XML_NAMESPACE}drug')
        for action, elem in tqdm(doc, desc=f"Import {self.biodb_name.upper()}"):
            if "type" in elem.attrib:
                drug_index += 1
                drug = {'id': drug_index}
                references, synonyms = None, None
                targets = []
                external_identifiers = []
                product_names = []
                drug_interactions = []
                statuses = []
                patents = []
                pathways = []

                for child in elem.iterchildren():
                    ctag = child.tag[len(XML_NAMESPACE):]

                    if ctag in columns:
                        drug[ctag.replace('-', '_')] = child.text

                    elif ctag == 'drugbank-id':
                        primary_id = child.attrib.get('primary')
                        if primary_id:
                            drug['drugbank_id'] = child.text

                    elif ctag == 'general-references':
                        pmid_strs = child.xpath(self.xpath_pattern.references, namespaces=XN)
                        references = [drugbank.Reference(pmid=int(x)) for x in pmid_strs]

                    elif ctag == 'synonyms':
                        syns = child.xpath(self.xpath_pattern.synonyms, namespaces=XN)
                        synonyms = [drugbank.Synonym(synonym=x) for x in set(syns)]

                    elif ctag == 'products':
                        pro_names = child.xpath(self.xpath_pattern.product_names, namespaces=XN)
                        product_names = [drugbank.ProductName(name=x) for x in set(pro_names)]

                    elif ctag == 'drug-interactions':
                        for di_child in child:
                            di = {x.tag[len(XML_NAMESPACE):].replace('-', '_'): x.text for x in di_child}
                            drug_interactions.append(drugbank.DrugInteraction(**di))

                    elif ctag == 'external-identifiers':
                        for ex_ids_child in child:
                            resource = ex_ids_child.xpath(self.xpath_pattern.ex_ids_resourec, namespaces=XN)[0]
                            identifier = ex_ids_child.xpath(self.xpath_pattern.ex_ids_id, namespaces=XN)[0]
                            external_identifiers.append(drugbank.ExternalIdentifier(resource=resource,
                                                                                    identifier=identifier))

                    elif ctag == 'targets':
                        for target in child:
                            u = target.xpath(self.xpath_pattern.target_uniprot, namespaces=XN)
                            uniprot = u[0] if u else None

                            if uniprot:
                                actions = target.xpath(self.xpath_pattern.target_actions, namespaces=XN)
                                action = actions[0] if actions else None

                                kactions = target.xpath(self.xpath_pattern.target_known_action, namespaces=XN)
                                known_action = kactions[0] if kactions else None

                                targets.append(
                                    drugbank.Target(uniprot=uniprot, action=action, known_action=known_action))

                    elif ctag == 'patents':
                        for patent in child:
                            patent_dict = {}
                            for patent_child in patent:
                                patent_key = patent_child.tag[len(XML_NAMESPACE):].replace('-', '_')
                                patent_value = patent_child.text
                                if patent_key in ('expires', 'approved') and re.search(r'^\d{4}-\d{2}-\d{2}$',
                                                                                       patent_value):
                                    patent_value = datetime.strptime(patent_value.strip(), '%Y-%m-%d').date()
                                patent_dict[patent_key] = patent_value
                            if patent_dict:
                                patents.append(drugbank.Patent(**patent_dict))

                    elif ctag == 'groups':
                        for group in child:
                            statuses.append(drugbank.Status(status=group.text))

                    elif ctag == 'pathways':
                        pws = child.xpath(self.xpath_pattern.pathways, namespaces=XN)
                        pathways = [drugbank.Pathway(smpdb_id=x) for x in pws]

                    # TODO: implement reactions, ... (check xsd/xml)

                drugbank_instance = drugbank.Drugbank(
                    references=references,
                    synonyms=synonyms,
                    targets=targets,
                    external_identifiers=external_identifiers,
                    product_names=product_names,
                    drug_interactions=drug_interactions,
                    statuses=statuses,
                    patents=patents,
                    pathways=pathways,
                    **drug
                )
                self.session.add(drugbank_instance)
                # insert in chunks of ...
                if drug_index % 100 == 0:
                    self.session.commit()

            elem.clear()

        self.session.commit()

        os.remove(self.file_path_unzipped)

        return {self.biodb_name: drug_index}

    @staticmethod
    def get_timed_answer(prompt=None, timeout=20, timeout_msg=None):
        """Returns user answer in an allotted amount of time."""

        def timeout_error(*_):
            raise TimeoutError

        if platform.system() == "Windows":
            answer = input(prompt)
            return answer

        else:
            signal.signal(signal.SIGALRM, timeout_error)
            signal.alarm(timeout)
            try:
                answer = input(prompt)
                signal.alarm(0)
                return answer

            except TimeoutError:
                if timeout_msg:
                    logger.error(f"The following error occurred while contacting the DrugBank website: {timeout_msg}")
                signal.signal(signal.SIGALRM, signal.SIG_IGN)
                return None

    def get_user_passwd(self, drugbank_user: str = None, drugbank_password: str = None) -> list:
        """Read username and password from configuration file."""
        section_name = "DRUGBANK"
        conf = None
        section_exists = True
        config_exists = os.path.isfile(config_file_path)

        cfg = ConfigParser()

        if config_exists:
            cfg.read(config_file_path)

            if not cfg.has_section(section_name):
                section_exists = False

            else:
                conf = get_config_as_dict()[section_name]

        if not section_exists and (drugbank_user and drugbank_password):
            conf = {'user': drugbank_user, 'password': drugbank_password}
            write_to_config(section_name, 'user', drugbank_user)
            write_to_config(section_name, 'password', drugbank_password)

        if not section_exists or not config_exists:

            prompt = "Do you have an approved account with DrugBank [y/n]: "
            timeout_msg = "No answer was provided. Skipping DrugBank update...\n"
            timeout = 20
            answer = self.get_timed_answer(prompt=prompt, timeout=timeout, timeout_msg=timeout_msg)

            num_tries = 0
            max_tries = 4

            while num_tries < max_tries and answer not in ['yes', 'y', 'no', 'n'] and answer is not None:

                print("Invalid response!\n")
                answer = self.get_timed_answer(prompt=prompt, timeout=timeout, timeout_msg=timeout_msg)
                num_tries += 1

                if num_tries == max_tries:
                    print("Too many invalid responses. Skipping DrugBank update...\n")
                    num_tries += 1

            if answer in ['yes', 'y']:
                user = input("Insert DrugBank user name:\n")
                passwd = getpass.getpass("Insert DrugBank password:\n")
                write_to_config(section_name, 'user', user)
                write_to_config(section_name, 'password', passwd)
                conf = get_config_as_dict()[section_name]

            elif answer in ['no', 'n'] or num_tries >= max_tries or answer is None:  # If no, write 'NA' to config
                write_to_config(section_name, 'user', 'NA')
                write_to_config(section_name, 'password', 'NA')

        if conf and conf['user'] != 'NA':  # Return None if user in config is 'NA'
            return [conf['user'], conf['password']]

    def insert(self) -> Dict[str, int]:
        """Check if files missing for download or generic table empty. If True then insert data."""
        inserted = {}
        self.download()

        if os.path.exists(self.file_path):
            drugbank_table_exists = self.engine.dialect.has_table(self.engine.connect(),
                                                                  drugbank.Drugbank.__tablename__)
            if not drugbank_table_exists or self.session.query(drugbank.Drugbank.id).count() == 0:
                self.recreate_tables()
                inserted.update(self.insert_data())
        else:
            logger.error('Drugbank data can not be inserted because the file does not exist. Please download manually '
                         f'and move to {self.biodb_dir}')
        return inserted

    def download(self) -> dict:
        """Download DrugBank to standard data dir."""
        secs_100_days = 100 * 60 * 60 * 24
        now = time()
        downloaded = False
        file_exists = os.path.exists(self.file_path)

        if file_exists:
            expired = now - os.path.getmtime(self.file_path) > secs_100_days
        else:
            expired = True

        if not file_exists or expired:
            credentials = self.get_user_passwd()
            if credentials:
                file_to_download = self.__latest_version()
                logger.info(f"Downloading {file_to_download}")
                user, passwd = credentials[0], credentials[1]
                response = requests.get(file_to_download, auth=(user, passwd))

                if response.ok and response.status_code == 200:  # The file is not empty
                    with open(self.file_path, 'wb') as drugbank_data_file:
                        drugbank_data_file.write(response.content)
                    downloaded = True

                else:
                    logger.warning("Invalid username and password. Skipping DrugBank update...")

        return {self.biodb_name: downloaded}

    def __latest_version(self) -> str:
        """Gets latest version of Drugbank and adds it to URL."""
        webpage = requests.get(self.urls['drugbank_version'])
        version = re.findall(r"(DrugBank Release Version) (\d\.\d\.\d)", webpage.text)[0][1]
        return self.urls[self.biodb_name].format(version.replace(".", "-"))

    def get_drugbank_id_rids(self) -> Dict[str, str]:
        """Get dict of DrugBank IDs as keys and their rIDs as values."""
        rows = self.execute("Select drugbank_id, @rid.asString() as rid  from drug")
        return {x.oRecordData['drugbank_id']: x.oRecordData[RID] for x in rows}

    @staticmethod
    def _replace_new_lines(input_string: str) -> str:
        if input_string and input_string.strip():
            return input_string.strip().replace('\r\n', '<br>').replace('\n', '<br>')
        return input_string

    def update_interactions(self) -> int:
        """Updates the edges between drug and pure protein nodes."""
        self.clear_edges()

        drugbank_table_exists = self.engine.dialect.has_table(self.engine.connect(), drugbank.Drugbank.__tablename__)
        if not drugbank_table_exists:
            logger.error('Update failed - DrugBank table does not exist.')
            return 0

        drugbank_id_rids = self.get_drugbank_id_rids()

        inserted = 0

        sql = """Select @rid.asString() as rid, uniprot FROM protein
        WHERE pure=true and uniprot IS NOT NULL AND namespace = 'HGNC'"""
        for row in tqdm(self.execute(sql), desc=f"Update {self.biodb_name.upper()} interaction."):
            r = row.oRecordData
            protein_rid, uniprot = r['rid'], r['uniprot']
            query = self.session.query(drugbank.Target).filter(drugbank.Target.uniprot == uniprot)
            for target in query.all():
                drugbank_id = target.drugbank.drugbank_id

                if drugbank_id in drugbank_id_rids:
                    drug_rid = drugbank_id_rids[drugbank_id]
                else:
                    value_dict_drug = {
                        'drugbank_id': target.drugbank.drugbank_id,
                        'label': target.drugbank.name,
                        'description': self._replace_new_lines(target.drugbank.description),
                        'cas_number': target.drugbank.cas_number,
                        'indication': self._replace_new_lines(target.drugbank.indication),
                        'pharmacodynamics': self._replace_new_lines(target.drugbank.pharmacodynamics),
                        'toxicity': self._replace_new_lines(target.drugbank.toxicity),
                        'metabolism': self._replace_new_lines(target.drugbank.metabolism),
                        'mechanism_of_action': self._replace_new_lines(target.drugbank.mechanism_of_action)
                    }

                    drug_rid = self.insert_record('drug_db', value_dict=value_dict_drug)
                    drugbank_id_rids[drugbank_id] = drug_rid  # update cache

                value_dict_edge = {
                    'action': target.action,
                    'known_action': target.known_action
                }
                self.create_edge('has_drug_target_db',
                                 from_rid=drug_rid,
                                 to_rid=protein_rid,
                                 value_dict=value_dict_edge)
                inserted += 1

        return inserted
