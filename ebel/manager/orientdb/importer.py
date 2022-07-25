"""Methods for importing BEL files into OrientDB."""

import os
import re
import git
import json
import logging

from tqdm import tqdm
from typing import Tuple
from copy import deepcopy
from pyorientdb import OrientDB
from datetime import datetime
from pathlib import Path
from git.exc import InvalidGitRepositoryError
from collections import OrderedDict, defaultdict, namedtuple

from ebel import tools
from ebel.constants import RID
from ebel.manager.orientdb.constants import NODES, EDGES
from .odb_defaults import normalized_pmod, bel_func_short

BEL_GIT_ID = namedtuple('BEL_GIT_ID', ['hexsha', 'repo_path', 'origin_url'])
JsonParts = namedtuple('JsonParts', ['document',
                                     'definitions',
                                     'statements_and_sets'])

logger = logging.getLogger(__name__)


class _BelImporter:
    """BEL importer for OrientDB."""

    _cache = {}

    def __init__(self, file_path, odb_client: OrientDB = None):
        """Insert statements and sets from BEL JSON file."""
        self.client = odb_client
        self.file_path = file_path
        if not _BelImporter._cache:
            _BelImporter._cache[EDGES] = self._get_bel_relation_rid_cache()
            _BelImporter._cache[NODES] = self._get_bel_rid_cache()

    @staticmethod
    def file_is_in_git_repo(path):
        try:
            git.Repo(path, search_parent_directories=True)
            exists = True
        except InvalidGitRepositoryError:
            logger.error(f"{path} is not a valid Git repository")
            exists = False
        return exists

    def _get_bel_rid_cache(self):
        """Get BEL string OrientDB rid dictionary for all bel nodes."""
        sql = "Select @rid.asString(),@class.asString(),bel from bel"
        return {(y['bel'], y['class']): y['rid'] for y in [x.oRecordData for x in self.client.command(sql)]}

    def _get_bel_relation_rid_cache(self):
        """Create a dictionary of all bel_relation edges using their properties as keys and RIDs as values."""
        rel_cache = dict()

        sql = """SELECT @rid.asString(), out.@rid.asString() as subject_id, in.@rid.asString() as object_id,
        evidence, annotation, citation.type as citation_type, citation.ref as citation_ref,
        @class.asString() as relation FROM bel_relation"""
        props = ('relation', 'subject_id', 'object_id', 'citation_type', 'citation_ref', 'evidence', 'annotation')
        results = self.client.command(sql)
        for entry in results:
            r = entry.oRecordData
            edge_profile = []
            for prop in props:
                if prop in r:
                    if prop == 'annotation':
                        edge_profile.append(json.dumps(r[prop], sort_keys=True))
                    else:
                        edge_profile.append(r[prop])

                else:
                    edge_profile.append(None)

            rel_cache[tuple(edge_profile)] = r['rid']

        return rel_cache

    def get_git_info(self) -> BEL_GIT_ID:
        """Get git info identifies the file.

        Returns
        -------
        type
            object with properties hexsha, repo_path and origin_url

        """
        bel_git_id = None
        absolute_path = Path(self.file_path)

        if self.file_is_in_git_repo(absolute_path):
            repo = git.Repo(absolute_path, search_parent_directories=True)
            origin_url_found = re.search("(https?://)([^@]+@)?(.*)", repo.remotes.origin.url)

            origin_url = None
            if origin_url_found:
                protocol, user, origin_url = origin_url_found.groups()

            repo_path = absolute_path.as_posix()[len(repo.working_dir) + 1:]
            commits = list(repo.iter_commits(paths=absolute_path))

            if commits:
                commit = commits[0]
                bel_git_id = BEL_GIT_ID(commit.hexsha, repo_path, origin_url)

        if not bel_git_id:
            bel_git_id = BEL_GIT_ID('', '', '')

        return bel_git_id

    def insert(self) -> Tuple[bool, int]:
        """Insert JSON file in OrientDB."""
        inserted = 0

        with open(self.file_path) as fd:
            bel_python_object = json.load(fd, object_pairs_hook=OrderedDict)

        if not bel_python_object:  # May be empty JSON
            logger.warning(f"{self.file_path} is empty")
            return False, 0

        parts = self.get_json_parts(bel_python_object)
        exists_before, document_id = self.insert_bel_header(parts.document, parts.definitions)

        if not exists_before:
            inserted = self.insert_statements_and_sets(parts.statements_and_sets, document_id)

        return not exists_before, inserted

    def insert_bel_header(self, doc_info, defs) -> Tuple[bool, str]:
        """Insert header info (document_info, namespaces and annotations) plus git info)."""
        data = deepcopy(doc_info)
        data['annotation'] = {}
        data['namespace'] = {}
        for entry in defs:
            anno_or_ns = list(entry.keys())[0]
            keyword = entry[anno_or_ns]['keyword']
            del entry[anno_or_ns]['keyword']
            data[anno_or_ns][keyword] = entry[anno_or_ns]

        if 'authors' in data:
            data['authors'] = [a.strip() for a in data['authors'].split(",")]

        keyword_flag = False
        if 'keywords' in data:
            keyword_flag = True
            data['keywords'] = [k.strip() for k in data['keywords'].split(",")]

            keyword_rids = self.get_keyword_rids(keywords=data['keywords'])
            keyword_linkset = "[" + ",".join(keyword_rids) + "]"  # This feature is a LINKSET
            del data['keywords']  # TODO get so rids can be in JSON and load - see line 131

        now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        data['date'] = {'uploaded': now}
        file_stat = os.stat(self.file_path)
        data['file'] = {
            'path': self.file_path,
            'md5': tools.md5(self.file_path),
            'size': file_stat.st_size,
            'last_modified': file_stat.st_mtime
        }

        git_info_dict = self.get_git_info()

        data['git_info'] = git_info_dict._asdict()

        net_exists_before = self.network_exists(
            data['version'],
            self.file_path,
            data['file']['md5'],
            data['file']['last_modified'],
            git_info_dict)

        if not net_exists_before:
            content = json.dumps(data)
            sql = "insert into bel_document content {}".format(content)
            r = self.client.command(sql)
            document_rid = r[0]._OrientRecord__rid

            # TODO How to include LINKSET in data dict? Fails when trying to load. This is work around
            if keyword_flag:
                keyword_sql = f"UPDATE {document_rid} SET keywords = {keyword_linkset}"
                self.client.command(keyword_sql)
        else:
            document_rid = None
            # TODO: Extract information from database
            logger.warning(f"{self.file_path} was already imported!")

        return net_exists_before, document_rid

    def get_keyword_rids(self, keywords: list) -> list:
        """Get the RID for each keyword set in the BEL document. If keyword does not exist, a new one is made."""
        rid_sql = "SELECT @rid FROM keyword WHERE label = '{}'"

        keyword_rids = []
        for keyword in keywords:
            record = self.client.command(rid_sql.format(keyword.lower()))

            if record:
                rid = record[0].oRecordData[RID].get_hash()

            else:
                insert_sql = f"INSERT INTO keyword CONTENT {{'label': '{keyword.lower()}', 'description': ''}}"
                new_record = self.client.command(insert_sql)[0]
                rid = new_record._OrientRecord__rid

            keyword_rids.append(rid)

        return keyword_rids

    def network_exists(self, version, file_path, md5, last_modified, git_info_dict) -> bool:
        sql = f"""Select 1 from bel_document where
                    version = '{version}' and
                    file.path = '{Path(file_path).as_posix()}' and
                    file.md5 = '{md5}' and
                    file.last_modified = '{last_modified}' and
                    git_info = {json.dumps(git_info_dict)}
                    """
        return not len(self.client.command(sql)) == 0

    @staticmethod
    def insert_definitions(definitions):
        # TODO why is this here
        return definitions

    def insert_statements_and_sets(self, statements_and_sets, document_id) -> int:
        """Insert statement and sets."""
        citation = {}
        evidence = ""
        annotation = defaultdict(set)
        pmid = 0
        citation_ref = ""
        citation_type = ""

        for e in tqdm(statements_and_sets, desc="Insert BEL Statements"):

            dtype, data = tuple(e.items())[0]

            if dtype == "sets":
                for bel_set in data:
                    key, value = tuple(bel_set.items())[0]

                    if key == "citation":
                        citation = dict(value)
                        citation_type = citation['type'].strip()
                        citation_ref = citation['ref'].strip()
                        evidence = ""
                        annotation = defaultdict(set)

                        if citation['type'].lower() == "pubmed" and re.search(r'^\d+$', citation_ref):
                            pmid = citation_ref
                        else:
                            pmid = 0

                    elif key == "evidence":
                        evidence = re.sub(r"\s*\\\s*\n\s*", " ", value)

                    elif key == "set":
                        anno_keyword, anno_entries = tuple(value.items())[0]
                        annotation[anno_keyword] = set(anno_entries)

                    elif key == "unset":
                        for anno_keyword in value:
                            annotation.pop(anno_keyword, None)

            elif dtype == "statement" and len(data) >= 1:

                subject_id = self.get_node_id(data[0]['subject'])[1]

                if len(data) > 1 and 'object' in data[2]:
                    # TODO: nested statements are missing

                    object_id = self.get_node_id(data[2]['object'])[1]

                    relation = data[1]['relation']

                    self.insert_bel_edge(annotation, citation, citation_ref, citation_type, evidence, object_id, pmid,
                                         relation, subject_id, document_id)

        return len(statements_and_sets)

    def insert_bel_edge(self, annotation, citation, citation_ref, citation_type, evidence, object_id, pmid, relation,
                        subject_id, document_id):
        # check if relation already exists
        anno = {key: sorted(list(annotation[key])) for key in annotation.keys()}
        anno_json = json.dumps(anno, sort_keys=True)
        edge_content = {"pmid": pmid,
                        "citation": citation,
                        "annotation": anno,
                        "evidence": evidence,
                        "document": [document_id]}

        # Need to clean the properties
        evidence = evidence.replace('\n', ' ')
        citation_ref = citation_ref if citation_ref else None
        citation_type = citation_type if citation_type else None

        edge_profile = (relation, subject_id, object_id, citation_type, citation_ref, evidence, anno_json)
        edge_exists = True if edge_profile in _BelImporter._cache[EDGES] else False

        if not edge_exists:
            edge_content_json = json.dumps(edge_content, sort_keys=True)
            sql = f"CREATE EDGE {relation} FROM {subject_id} TO {object_id} CONTENT {edge_content_json}"
            record = self.client.command(sql)
            _BelImporter._cache[EDGES][edge_profile] = record[0]._OrientRecord__rid

        else:
            edge_rid = _BelImporter._cache[EDGES][edge_profile]
            sql = f"UPDATE EDGE {edge_rid} ADD document = {document_id}"
            self.client.command(sql)

    @classmethod
    def get_json_parts(cls, bel_python_object) -> JsonParts:
        """Return the parts document,definitions,statements_and_sets from bel_json as python object."""
        doc, defs, ss = bel_python_object
        return JsonParts(document=doc['document'],
                         definitions=defs['definitions'],
                         statements_and_sets=ss['statements_and_sets'])

    @staticmethod
    def get_node_class_rid_from_db(obj, bel: str):
        """Return @rid if node exists."""
        rid = None
        node_class = None

        if isinstance(obj[0], OrderedDict) and 'function' in obj[0]:
            node_class = obj[0]['function']['name']
            if (bel, node_class) in _BelImporter._cache[NODES]:
                rid = _BelImporter._cache[NODES][(bel, node_class)]

        return node_class, rid

    @staticmethod
    def is_function(obj):
        return isinstance(obj, OrderedDict) and 'function' in obj

    def get_node_id(self, obj: list) -> str:
        """Return rid of obj."""
        if not isinstance(obj, list):
            raise TypeError(f"Expecting list, but get {type(obj)} for {obj}")

        inserted_nodes = []
        params = {}

        bel = self.get_bel(obj)

        node_class = obj[0]['function']['name']

        if node_class not in ['pmod', 'fragment', 'variant']:
            node_class, rid_from_db = self.get_node_class_rid_from_db(obj, bel)
            if rid_from_db:
                return node_class, rid_from_db

        [params.update(x) for x in obj[1] if isinstance(x, OrderedDict)]

        for e in obj[1]:
            if isinstance(e, list):
                if self.is_function(e[0]):
                    inserted_nodes += [self.get_node_id(e)]
                else:
                    for f in e:
                        inserted_nodes += [self.get_node_id(f)]

        rid = self.insert_bel_node(node_class, params, bel)

        for child_class, child_rid in inserted_nodes:
            sql = f"Select @rid from has__{child_class} where in.@rid={child_rid} and out.@rid={rid}"
            exists = self.client.command(sql)
            if not exists:
                sql = f"CREATE EDGE has__{child_class} from {rid} to {child_rid}"
                self.client.command(sql)

        return node_class, rid

    def insert_bel_node(self, node_class, params, bel):
        """Insert bel node, return rid."""
        params.update({'bel': bel})
        sql_temp = "insert into {} content {}"
        sql = sql_temp.format(node_class, json.dumps(params))
        record = self.client.command(sql)
        rid = record[0]._OrientRecord__rid
        _BelImporter._cache[NODES][(bel, node_class)] = rid
        return rid

    def get_bel_string(self, params, function_name=None):
        """Get BEL formated string."""
        bels = []

        for param in params:
            if isinstance(param, str):
                bels.append(param)
            elif isinstance(param, dict):
                if set(param.keys()) == {'namespace', 'name'}:
                    bels.append(param['namespace'] + ':"' + param['name'] + '"')

                elif function_name == "fragment":
                    bels.append(','.join(['"' + x + '"' for x in param.values() if x]))

                elif function_name == "activity":
                    if param['namespace']:
                        bel_str = param['namespace'] + ':"' + param['name'] + '"'
                    else:
                        bel_str = param['default']
                    bels.append("ma(" + bel_str + ")")

                elif function_name == "pmod":
                    if param['namespace']:
                        first_part_pmod = param['namespace'] + ':"' + param['name'] + '"'
                    else:
                        first_part_pmod = normalized_pmod[param['type']]
                    position = str(param['position']) if param['position'] else None
                    parts_pmod = [first_part_pmod, param['amino_acid'], position]
                    bels.append(",".join([x for x in parts_pmod if x]))

                else:
                    bels.append(','.join(['"' + str(x) + '"' for x in param.values() if x]))

        joined_params = ",".join(bels)

        if function_name:
            return bel_func_short[function_name] + "(" + joined_params + ")"

        else:
            return joined_params

    def get_bel(self, obj, parent_function=None):
        """Return BEL by python object loaded from JSON."""
        params = []
        function_name = None

        for element in obj:

            if isinstance(element, dict):

                if 'function' in element:
                    function_name = element['function']['name']

                else:
                    params.append(element)

            elif isinstance(element, list):
                params.append(self.get_bel(element, function_name))

        return self.get_bel_string(params, parent_function)
