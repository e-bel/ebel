"""Generic BEL relation API methods."""
import re
import cgi
from collections import namedtuple, defaultdict
from copy import deepcopy
from enum import Enum
from math import ceil
from typing import List, Optional, Dict, Set, NamedTuple, Any, Union, Tuple

from flask import request
from graphviz import Digraph

from ebel import Bel
from ebel.manager.orientdb.odb_structure import get_columns, get_node_view_labels
from ebel.web.api.ebel.v1 import __get_pagination, DataType, SqlOperator

PathLengthDict = Dict[int, List[Dict[str, list]]]
PathLength = int
EdgeInfo = dict
NodeInfo = dict
Rid = str
RidList = List[str]
EdgePathsByLength = Dict[PathLength, RidList]
ErrorMessage = Dict[str, str]

BELishEdge = namedtuple('Edge', ['name', 'direction', 'params_str'])

edge_colours = {
    'increases': "limegreen",
    'directly_increases': "springgreen4",
    'decreases': "orangered",
    'directly_decreases': "red3",
    'rate_limiting_step_of': "lightslateblue",
    'regulates': "lightblue3",
    'causes_no_change': "yellow2",
    'positive_correlation': "darkolivegreen4",
    'negative_correlation': "coral3",
}

node_colours = {
    'protein': "lightblue1",
    'complex': "khaki1",
    'component': "aquamarine",
    'rna': "goldenrod1",
    'gene': "lightslateblue",
    'activity': "palegreen3",
    'abundance': 'darksalmon',
    'pathology': "palegreen",
    'drug_db': "yellow1",
    'biological_process': "snow"
}


class Column:
    """Column definition class."""

    def __init__(self,
                 form_name: str,
                 column: str,
                 sql_operator: SqlOperator = SqlOperator.EQUALS,
                 data_type: DataType = DataType.STRING):
        """Init method for column.

        Parameters
        ----------
        form_name
        column
        sql_operator
        data_type
        """
        self.column = column
        self.display_column = column + ".asString()" if "@" in column else column
        self.sql_operator = sql_operator
        self.form_name = form_name
        self.data_type = data_type
        self.value = None

    def set_search_term(self, value: str):
        """Return value for a given search term."""
        if value:
            self.value = value.strip()

    def get_sql(self):
        """Build the SQL query."""
        column = f"{self.column}.asString()" if "@" in self.column else self.column
        return f"{column} as {self.form_name}"


bel_relation_default_columns: List[Column] = [
    Column('subject_rid', 'out.@rid'),
    Column('subject_node_class', 'out.@class'),
    Column('subject_namespace', 'out.namespace'),
    Column('subject_name', 'out.name', SqlOperator.LIKE),
    Column('subject_bel', 'out.bel', SqlOperator.LIKE),
    Column('subject_gene_symbol_involved_in', 'out.involved_genes', SqlOperator.IN, DataType.LIST_STRING),
    Column('subject_other_involved_in', 'out.involved_other', SqlOperator.IN, DataType.LIST_STRING),
    Column('edge_rid', '@rid'),
    Column('relation', '@class'),
    Column('evidence', 'evidence', SqlOperator.LIKE),
    Column('citation_full_journal_name', 'citation.full_journal_name', SqlOperator.LIKE),
    Column('citation_pub_date', 'citation.pub_date'),
    Column('citation_pub_year', 'citation.pub_year'),
    Column('citation_last_author', 'citation.last_author', SqlOperator.LIKE),
    Column('citation_type', 'citation.type'),
    Column('author_in_author_list', 'citation.author_list', SqlOperator.IN, DataType.LIST_STRING),
    Column('title', 'citation.title', SqlOperator.LIKE),
    Column('doi', 'citation.doi'),
    Column('object_rid', 'in.@rid'),
    Column('object_node_class', 'in.@class'),
    Column('object_namespace', 'in.namespace'),
    Column('object_name', 'in.name', SqlOperator.LIKE),
    Column('object_bel', 'in.bel', SqlOperator.LIKE),
    Column('object_gene_symbol_involved_in', 'in.involved_genes', SqlOperator.IN, DataType.LIST_STRING),
    Column('object_other_involved_in', 'in.involved_other', SqlOperator.IN, DataType.LIST_STRING),
]

Pagination = namedtuple('Pagination', ['page', 'page_size', 'skip'])


class Query:
    """Generic class for creating a SQL query."""

    def __init__(self, odb_class: str, columns: List[Column]):
        """Init method for hte Query class."""
        self.odb_class: str = odb_class
        self.columns: List[Column] = columns
        self.ebel = Bel()
        self.where = self.get_where()

    @staticmethod
    def get_pagination() -> Pagination:
        """Separate results into pages of a specific length."""
        page_size = request.args.get('page_size', '10')
        page_size = int(page_size) if re.search(r"^\d+$", page_size) else 10
        page_size = 10 if page_size >= 100 else page_size
        page = request.args.get('page', '1')
        page = int(page) if re.search(r"^\d+$", page) else 1
        skip = (page - 1) * page_size
        return Pagination(page=page, page_size=page_size, skip=skip)

    def get_where(self):
        """Generic filter execution method."""
        where = ''
        wheres = []
        for col in self.columns:
            if col.value:
                if col.column.endswith('@rid') and "," in col.value:
                    rids = [x.strip() for x in col.value.split(",") if re.search(r"^#\d+:\d+$", x.strip())]
                    rids_str = "[" + ','.join(rids) + "]"
                    wheres.append(f"{col.column} in {rids_str}")
                elif col.column != "@class":
                    if col.data_type in [DataType.STRING, DataType.LIST_STRING]:
                        value = f'"{col.value}"'
                    else:
                        value = col.value

                    if col.data_type in [DataType.LIST_STRING, DataType.LIST_NUMBER, DataType.LIST_INTEGER]:
                        wheres.append(f'{value} {col.sql_operator.value} {col.column}')
                    else:
                        wheres.append(f'{col.column} {col.sql_operator.value} {value}')
        if wheres:
            where = " WHERE " + ' AND '.join(wheres)
        return where

    @property
    def sql(self):
        """Generic sql execution method."""
        select = "SELECT "
        select += ', '.join([f"{sw.display_column} as {sw.form_name}" for sw in self.columns])
        select += " FROM " + self.odb_class
        sql = select + self.where
        return sql

    def get_number_of_results(self):
        """Count number of results."""
        sql = "SELECT count(*) FROM " + self.odb_class + self.where
        return self.ebel.query_get_dict(sql)[0]['count']

    def get_result(self):
        """Return total number of results."""
        p = self.get_pagination()
        if not (p.page and p.page_size):
            return {'error': "Please add page and page_size to your method."}

        number_of_results = self.get_number_of_results()
        pages = ceil(number_of_results / p.page_size)
        sql_paginated = self.sql + f" skip {p.skip} limit {p.page_size}"

        return {
            'page': p.page,
            'page_size': p.page_size,
            'number_of_results': number_of_results,
            'pages': pages,
            'results': [x for x in self.ebel.query_get_dict(sql_paginated)]
        }


def get_edges():
    """Return data for a BEL relation edge."""
    columns = deepcopy(bel_relation_default_columns)

    for column in bel_relation_default_columns:
        column.set_search_term(request.args.get(column.form_name))

    relation = request.args.get('relation', 'bel_relation')
    sql_builder = Query(relation, columns)

    return sql_builder.get_result()


def get_nodes() -> dict:
    """Return list of nodes with a given namespace."""
    b = Bel()
    where_list: List[str] = []
    params = {k: v for k, v in request.args.items() if k in ['namespace', 'name'] and v}

    if request.args.get('pure') == 'true':
        params.update(pure=True)

    conn2bel_rel = request.args.get('connected_to_bel_relation')
    if conn2bel_rel:
        conn2bel_rel_dir = request.args.get('connected_to_bel_relation_direction', 'both')
        where_list.append(f"{conn2bel_rel_dir}('{conn2bel_rel}').size()>0")

    conn2ebel_rel = request.args.get('connected_to_ebel_relation')
    if conn2ebel_rel:
        conn2ebel_rel_dir = request.args.get('connected_to_ebel_relation_direction', 'both')
        where_list.append(f"{conn2ebel_rel_dir}('{conn2ebel_rel}').size()>0")

    node_class = request.args.get('node_class')
    p = __get_pagination()
    number_of_results = b.query_class(class_name=node_class,
                                      columns=['count(*)'],
                                      with_rid=False,
                                      **params)[0]['count']
    pages = ceil(number_of_results / p.page_size)
    results = b.query_class(class_name=node_class,
                            columns=['namespace', 'name', 'bel', 'pure'],
                            skip=p.skip,
                            limit=p.page_size,
                            where_list=tuple(where_list),
                            print_sql=True,
                            **params)
    return {
        'page': p.page,
        'page_size': p.page_size,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': results
    }


def _get_rid() -> Optional[str]:
    """Get rID."""
    rid = request.args.get('rid')
    if rid:
        rid = rid.strip()
        if re.search(r'#\d+:\d+', rid):
            return rid


def get_by_rid() -> Optional[str]:
    """Return BEL node by rid."""
    result_dict = {}
    rid = _get_rid()
    if rid:
        b = Bel()
        for key, value in b.client.record_load(rid).oRecordData.items():
            if isinstance(value, (str, int, float, dict)):
                result_dict[key] = value
            elif isinstance(value, list):
                if all([isinstance(x, (str, int, float)) for x in value]):
                    result_dict[key] = value
            else:
                print(dir(value))
        return result_dict


def get_adjacent_nodes_by_rid() -> list:
    """Return neighboring nodes of given rID."""
    rid = _get_rid()
    relation = request.args.get('relation', 'bel_relation')
    direction = request.args.get('direction', 'both')
    if rid:
        b = Bel()
        sql = "Select @rid.asString() as rid, @class.asString()as class ,bel, name, namespace" \
              f" from (SELECT expand({direction}('{relation}')) from {rid})"
        return [x.oRecordData for x in b.execute(sql)]


def get_edge_by_annotation() -> list:
    """Return list of edges with a given annotation."""
    columns = deepcopy(bel_relation_default_columns)
    cols_str = ', '.join([x.get_sql() for x in columns])
    annotation_group = request.args.get('annotation')
    mesh_term = request.args.get('mesh_term')
    sql_temp = f"Select {cols_str} from bel_relation where '{{}}' in annotation['{annotation_group}']"
    if mesh_term and annotation_group:
        sql = sql_temp.format(mesh_term)
        print(sql)
        return [x.oRecordData for x in Bel().execute(sql)]


def get_number_of_edges() -> int:
    """Return the number of edges."""
    b = Bel()
    relation = request.args.get('relation', 'bel_relation')
    r = b.execute(f"Select count(*) as number_of_edges from {relation} limit 1")
    return r[0].oRecordData['number_of_edges']


def get_pure_rid() -> Optional[str]:
    """Return None or the rID from the node class."""
    b = Bel()
    node_class = request.args.get('node_class', 'protein')
    namespace = request.args.get('namespace', 'HGNC')
    name = request.args.get('name')

    if name:
        sql = f"Select @rid.asString() as rid from {node_class} " \
              f"where name='{name}' and pure=true and namespace='{namespace}' limit 1"
        return b.execute(sql)[0].oRecordData['rid']


class Position(Enum):
    """Why is there a class for defining constants."""

    FIRST = "first"
    LAST = "last"
    INSIDE = "inside"


class MatchEdge:
    """Class to construct the edge portions of a MATCH query."""

    def __init__(self, edge_class: str, multiple_edge_classes: str, mesh_terms: List[str], pmids: List[int]):
        """Init method."""
        self.position: Optional[Position] = None
        self.node_class = 'bel'
        self.edge_class = edge_class
        self.pmids = pmids
        self.mesh_terms = mesh_terms
        self.multiple_edge_classes = multiple_edge_classes

    def set_last(self, node_class: Optional[str]):
        """Set object to the LAST position."""
        self.position = Position.LAST
        if node_class:
            self.node_class = node_class

    def get_edge(self, alias_number: int) -> str:
        """Return edge based on alias number."""
        mesh_or = ''
        if self.mesh_terms:
            mesh_or = " OR ".join(["'" + x.replace("'", '') + "' in annotation.mesh" for x in self.mesh_terms])
            mesh_or = f"({mesh_or})"

        pmids_in = ''
        if self.pmids:
            if len(self.pmids) == 1:
                pmids_in = f"pmid = {self.pmids[0]}"
            else:
                pmids_in = "pmid in " + str(self.pmids)
            pmids_in = f"{pmids_in}"

        where = ' AND '.join([x for x in [mesh_or, pmids_in] if x])

        where_str = f"where:({where}), " if any([mesh_or, pmids_in]) else ''
        e_class_multi, e_class_single = self.get_edge_classes()

        return f".outE({e_class_multi}){{{e_class_single}{where_str}as:e{alias_number}}}.inV()"

    def get_edge_classes(self):
        """Return edge classes of match query."""
        """"""
        e_class_single = ''
        e_class_multi = ''

        if isinstance(self.multiple_edge_classes, str) and self.multiple_edge_classes.strip():
            edge_classes = [x.strip() for x in self.multiple_edge_classes.split(',') if x.strip()]
            if len(edge_classes) == 1:
                e_class_single = f"class:{edge_classes[0]}, "
            elif len(edge_classes) > 1:
                edge_classes = ["'" + re.sub(r'\W+', "", x) + "'" for x in edge_classes]
                e_class_multi = ",".join(edge_classes)

        elif isinstance(self.edge_class, str) and self.edge_class.strip():
            e_class_single = f"class:{self.edge_class}, "

        return e_class_multi, e_class_single


class MatchNode:
    """Class to construct the node portions of a MATCH query."""

    def __init__(self):
        """Init method."""
        self.name: Optional[str] = None
        self.position: Optional[Position] = None
        self.node_class: Optional[str] = None
        self.namespace: Optional[str] = None
        self.gene_path: bool = False

    def set_outside(self,
                    position: Position,
                    name: Optional[str] = None,
                    node_class: Optional[str] = None,
                    namespace: Optional[str] = None):
        """Assign attributes to the "outside" position."""
        self.position = position
        if name:
            self.name = name
        if node_class:
            self.node_class = node_class
        if namespace:
            self.namespace = namespace

    def set_inside(self, gene_path: bool, node_class: None):
        """Assign attributes to the "inside" position."""
        self.gene_path = gene_path
        self.position = Position.INSIDE
        self.node_class = node_class

    def get_node(self, alias_number: int) -> str:
        """Return node based on alias number."""
        namespace = f"namespace='{self.namespace}'"
        name = f"name = '{self.name}'"
        name_involved = f"('{self.name}' in involved_genes OR '{self.name}' in involved_other)"
        involved_genes = "involved_genes.size()>0"
        not_like_node = "$matched.n{}!=$currentMatch"
        where_inside_list = []

        where_str = ''

        if self.position in (Position.FIRST, Position.LAST):

            if self.namespace and not self.name:
                where_str = namespace
            elif self.name and not self.namespace:
                if self.node_class in ['gene', 'rna', 'protein']:
                    where_str = name
                else:
                    where_str = name_involved
            elif self.name and self.namespace:
                where_str = f'{name} AND {namespace}'

        if self.position == Position.LAST:
            where_inside_list.append(not_like_node.format(1))
        if self.gene_path and not any([self.node_class, self.name, self.namespace]):
            where_inside_list.append(involved_genes)
        where_str = ' AND '.join([x for x in ([where_str] + where_inside_list) if x])

        alias = f"as:n{alias_number}"
        where = f"where:({where_str})" if where_str else ''
        node_class = self.get_node_class()
        node_query_str = ', '.join([x for x in [node_class, where, alias] if x])

        return "{" + node_query_str + "}"

    def get_node_class(self):
        """Return node class of match query."""
        node_class = ''
        if self.node_class:
            node_class = f"class:{self.node_class}"
        return node_class


class GraphType(Enum):
    """Not sure why there is a class for defining constants."""

    NODES = 'nodes'
    EDGES = 'edges'


class PathsResult(NamedTuple):
    """Class to build results of path query."""

    edge_paths_by_length: EdgePathsByLength
    unique_edges: Dict[Rid, EdgeInfo]
    unique_nodes: Dict[Rid, NodeInfo]


class PathQuery:
    """Class for constructing a path-based query."""

    def __init__(self,
                 start_name: str,
                 end_name: str,
                 min_length: int,
                 max_length: int,
                 start_class: Optional[str] = None,
                 end_class: Optional[str] = None,
                 start_ns: Optional[str] = None,
                 end_ns: Optional[str] = None,
                 gene_path: bool = False,
                 edge_class: Optional[str] = None,
                 multiple_edge_classes: Optional[str] = None,
                 inside_node_class: Optional[str] = None,
                 mesh_term: Optional[str] = None,
                 pmids: str = '',
                 belish: Optional[str] = None,
                 limit: int = 0,
                 skip: int = 0):
        """Init method."""
        self.multiple_edge_classes = multiple_edge_classes
        self.limit = limit

        if isinstance(self.limit, str) and self.limit.isnumeric():
            self.limit = int(self.limit)

        self.skip = skip

        if isinstance(self.skip, str) and self.skip.isnumeric():
            self.skip = int(self.skip)

        self.pmids = [int(x.strip()) for x in pmids.split(',') if x.strip().isdigit()]
        self.mesh_terms = [x.strip() for x in mesh_term.split(';') if x.strip()]
        self.execute = Bel().execute
        self.min_length = min_length
        self.max_length = max_length
        self.edge_class = edge_class
        self.belish = belish
        self.max_paths = 100000
        self.max_unique_edges = 1000
        self.nodes = [MatchNode() for _ in range(self.max_length + 1)]

        self.nodes[0].set_outside(position=Position.FIRST,
                                  name=start_name,
                                  node_class=start_class,
                                  namespace=start_ns)

        self.nodes[-1].set_outside(position=Position.LAST,
                                   name=end_name,
                                   node_class=end_class,
                                   namespace=end_ns)

        self.edges = [MatchEdge(self.edge_class,
                                self.multiple_edge_classes,
                                self.mesh_terms,
                                self.pmids) for _ in range(self.max_length)]
        self.edges[-1].set_last(end_class)

        # TODO: why not using normal edge_class?
        for node in self.nodes[1:-1]:
            node.set_inside(gene_path, inside_node_class)

        self.too_many_paths = "With the path length of {} we found already more than " \
                              f"{self.max_paths} pathways. Please specify you query and run again."

        self.too_many_edges = f"We found too many unique edges ({{}}, max allowed={self.max_unique_edges} ) with an " \
                              f"allowed maximum of {self.max_paths} paths. Please specify you query and run again. " \
                              "Decrease max path length, use limit or state start- and end-node more precisely."

    def get_query_str(self, number_of_edges):
        """Create query string by number of edges."""
        query = "match " + self.nodes[0].get_node(1)
        edges = self.edges[-1 * number_of_edges:]
        nodes = self.nodes[-1 * (number_of_edges + 1):]
        for i in range(1, number_of_edges + 1):
            query += edges[i - 1].get_edge(alias_number=i) + nodes[i].get_node(alias_number=i + 1)

        query += self.get_match_return(number_of_edges)
        return query

    @staticmethod
    def _get_unique_rids(graph_type: GraphType, path_length_dict: PathLengthDict) -> Set[Rid]:
        """Get unique node or edge rid set."""
        rids = {w for z in [[x for y in [en[graph_type.value] for en in v] for x in y] for _, v in
                            path_length_dict.items()] for w in z}
        return rids

    def get_unique_edge_list(self, path_length_dict: PathLengthDict) -> Dict[Rid, EdgeInfo]:
        """Get unique list of edges."""
        edge_rids = self._get_unique_rids(GraphType.EDGES, path_length_dict)
        return {rid: self.get_edge_info(rid) for rid in edge_rids}

    def get_unique_node_list(self, path_length_dict: PathLengthDict) -> Dict[Rid, NodeInfo]:
        """Get unique list of nodes."""
        node_rids = self._get_unique_rids(GraphType.NODES, path_length_dict)
        return {rid: self.get_node_info(rid) for rid in node_rids}

    def get_edge_info(self, rid: Rid):
        """Get edge metadata by given rID."""
        sql = f"Select out.@rid.asString() as subject_rid, in.@rid.asString() as object_rid, " \
              f"out.bel as subject_bel, in.bel as object_bel," \
              f"@class.asString() as class, citation, evidence, pmid, annotation.mesh from {rid}"
        return self.execute(sql)[0].oRecordData

    def get_node_info(self, rid: Rid):
        """Get node metadata by given rID."""
        sql = f"Select @class.asString() as class, * from {rid}"
        data = self.execute(sql)[0].oRecordData
        columns = get_columns(data['class']) + ['class']  # serializable
        return {k: v for k, v in data.items() if k in columns}

    @property
    def allowed_edges(self) -> List[str]:
        """Return the number of allowed edges, includes both eBEL and BEL edge types."""
        bel_relations = list(get_bel_relation_types().keys())
        ebel_relations = list(get_ebel_relation_types().keys())
        return list(bel_relations + ebel_relations)

    def get_match_return(self, number_of_edges):
        """Standard way to return node and edges."""
        edges = [f"e{i}.@rid.asString()" for i in range(1, number_of_edges + 1)]
        edges_join = ','.join(edges)
        nodes = [f"n{i}.@rid.asString()" for i in range(1, number_of_edges + 2)]
        nodes_join = ','.join(nodes)

        if self.limit and self.limit <= (self.max_paths + 1):
            limit = self.limit
        else:
            limit = self.max_paths + 1

        skip = f" skip {self.skip} " if self.skip else ''

        return f" return [{edges_join}] as edges, [{nodes_join}] as nodes {skip} limit {limit}"

    def get_query_str_belish_num_edges(self):
        """Find the number of edges that match the BELish query string."""
        node_strings, edges = [], []

        if self.belish:
            node_strings, edges = self.get_belish_nodes_edges()

        if len(node_strings) == len(edges) + 1:
            match_str = self.get_belish_match_str(edges, node_strings)

            return match_str, len(edges)

    def get_belish_match_str(self, edges, node_strings):
        """Build the MATCH string based on the BELish query."""
        # ALERT: if a where in the following node multi class of edge are ignored
        edge_direction = {
            '->': {'one_class': ".outE(){{class:{},as:e{}{}}}.inV()", 'multi_class': ".outE({}){{as:e{}{}}}.inV()"},
            '<-': {'one_class': ".inE(){{class:{},as:e{}{}}}.outV()", 'multi_class': ".inE({}){{as:e{}{}}}.outV()"},
        }
        re_node_in_box = re.compile(
            r'^\[\s*(?P<class_name>\w+)(?P<params>(\s+\w+(\.\w+)?(=|>|<|~|\*)(\d+|\d+\.\d+|[\w%]+|"[^"]+"))*)\s*\]$')

        match_str = 'match '
        for i in range(len(node_strings)):
            found_node_in_box = re_node_in_box.search(node_strings[i])
            if found_node_in_box:
                node_where = ''
                node_groups = found_node_in_box.groupdict()
                if node_groups['params']:
                    node_where = self.get_where_list_by_params(node_groups['params'])
                match_str += f"{{class:{node_groups['class_name']} {node_where}, as:n{i + 1}}}"
            else:
                match_str += f"{{class:bel, where:(bel like '{node_strings[i]}'), as:n{i + 1}}}"
            if i <= len(edges) - 1:
                edge_temp = edge_direction[edges[i].direction]
                edge_class_names = [x.strip() for x in edges[i].name.split(',') if x.strip()]
                edge_where = ''
                if edges[i].params_str:
                    edge_where = self.get_where_list_by_params(edges[i].params_str)
                if len(edge_class_names) == 1:
                    match_str += edge_temp['one_class'].format(edge_class_names[0], i + 1, edge_where)
                else:
                    edge_class_names_joined = ','.join([f'"{x}"' for x in edge_class_names])
                    match_str += edge_temp['multi_class'].format(edge_class_names_joined, i + 1, edge_where)

        match_str += self.get_match_return(len(edges))
        return match_str

    @staticmethod
    def get_where_list_by_params(params_str):
        """Build WHERE section of query based on the passed parameters."""
        where_list = []
        re_params_in_box = re.compile(r'(\w+(\.\w+)?)(=|>|<|~|\*)(\d+|\d+\.\d+|[\w%]+|"[^"]+")')
        for param, sub_param, operator, value in re_params_in_box.findall(params_str):
            operator = 'like' if operator == '~' else operator
            operator = 'in' if operator == '*' else operator
            equals_or_in_and_number = operator in ['=', 'in'] and re.search(r'^\d+(\.\d+)?$', value)
            quotes_surrounded = re.search('^".*"$', value)
            if not (operator in ['>', '<'] or equals_or_in_and_number or quotes_surrounded):
                value = f'"{value}"'
            if operator == 'in':
                where_list.append(f"{value} {operator} {param}")
            else:
                where_list.append(f"{param} {operator} {value}")
        where = ", where:(" + ' AND '.join(where_list) + ")"
        return where

    def get_belish_nodes_edges(self) -> Tuple[List[str], List[BELishEdge]]:
        """Return all BELish nodes and edges."""
        r = re.split(r"\s+(-(([a-z_0-9,]+)(\s+.*?)?)(->)|(<-)(([a-z_0-9,]+)(\s+.*?)?)-|-(->)|(<-)-)\s+", self.belish)
        nodes: List[str] = r[::12]
        edge_zip = zip(r[8::12], r[3::12], r[1::12], r[5::12], r[6::12], r[10::12], r[11::12], r[4::12])
        edges: List[BELishEdge] = [
            BELishEdge(x[0] or x[1] or '', x[3] or x[4] or x[5] or x[6], x[7]) for x in edge_zip
        ]
        print(nodes, edges)
        return nodes, edges

    def get_paths(self) -> Union[PathsResult, Dict]:
        """Get paths by query."""
        self.max_paths = 100000
        if self.edge_class and not (self.edge_class in self.allowed_edges or self.edge_class == 'E'):
            return {'error': "Unknown relation type."}

        path_length_dict: PathLengthDict = {}
        edge_paths_by_length: EdgePathsByLength = {}

        for number_of_edges in range(self.min_length, self.max_length + 1):
            query_str = self.get_query_str(number_of_edges)
            print(query_str)
            paths: List[Dict[str, Any]] = [x.oRecordData for x in self.execute(query_str)]

            if len(paths) > self.max_paths:
                return {'error': self.too_many_paths.format(number_of_edges)}

            path_length_dict[number_of_edges] = paths
            edge_paths_by_length[number_of_edges] = [x['edges'] for x in paths]

        unique_edges: Dict[Rid, EdgeInfo] = self.get_unique_edge_list(path_length_dict)
        if len(unique_edges) > self.max_unique_edges:
            return {'error': self.too_many_edges.format(len(unique_edges))}

        unique_nodes: Dict[Rid, NodeInfo] = self.get_unique_node_list(path_length_dict)
        paths_results = PathsResult(edge_paths_by_length=edge_paths_by_length,
                                    unique_edges=unique_edges,
                                    unique_nodes=unique_nodes)
        return paths_results

    def get_paths_by_belish(self):
        """Get paths by BELish query."""
        self.max_paths = 100
        path_length_dict: PathLengthDict = {}
        edge_paths_by_length: EdgePathsByLength = {}
        query_str_belish_num_edges = self.get_query_str_belish_num_edges()

        if query_str_belish_num_edges:
            query_str, number_of_edges = query_str_belish_num_edges
            print(query_str)
            paths: List[Dict[str, Any]] = [x.oRecordData for x in self.execute(query_str)]
            if len(paths) > self.max_paths:
                return {'error': self.too_many_paths.format(number_of_edges)}

            path_length_dict[number_of_edges] = paths
            edge_paths_by_length[number_of_edges] = [x['edges'] for x in paths]
            unique_edges: Dict[Rid, EdgeInfo] = self.get_unique_edge_list(path_length_dict)
            if len(unique_edges) > self.max_unique_edges:
                return {'error': self.too_many_edges.format(len(unique_edges))}

            unique_nodes: Dict[Rid, NodeInfo] = self.get_unique_node_list(path_length_dict)
            paths_results = PathsResult(edge_paths_by_length=edge_paths_by_length,
                                        unique_edges=unique_edges,
                                        unique_nodes=unique_nodes)
            return paths_results


def _get_number(number_string: str, default_value: int, min_value: int = None, max_value: int = None) -> int:
    """Parse the number string.

    Check if the number_string is numeric and >= min_value or <= max_value, otherwise assign min_value
    respectively max_value.
    """
    return_value: Optional[int] = None
    if number_string is not None and number_string.isnumeric():
        number = int(number_string)
        if min_value:
            return_value = number if number >= min_value else min_value
        elif max_value:
            return_value = number if number <= max_value else max_value
    else:
        if min_value:
            return_value = default_value
        elif max_value:
            return_value = default_value
    return return_value


def _get_path_query() -> Union[PathQuery, ErrorMessage]:
    """Return paths found for query.

    Raises
    ------
    ErrorMessage
    """
    start_name = request.args.get('start_node_name')
    end_name = request.args.get('end_node_name')
    start_class = request.args.get('start_node_class', 'bel')
    end_class = request.args.get('end_node_class')
    start_ns = request.args.get('start_node_namespace')
    end_ns = request.args.get('end_node_namespace')
    edge_class = request.args.get('connecting_relation')
    multiple_edge_classes = request.args.get('multiple_connecting_relations', '')
    inside_node_class = request.args.get('connecting_node_class')
    gene_path = request.args.get('only_gene_related_nodes_on_path')
    pmid = request.args.get('pmid', '')
    mesh_term = request.args.get('mesh_term', '')
    gene_path = True if gene_path == 'true' else False
    limit = request.args.get('limit', '')
    limit = int(limit) if limit.isnumeric() else 0
    belish = request.args.get('belish', '')

    min_value = 1
    max_value = 10
    min_str = request.args.get('min_path_length')
    min_length = _get_number(min_str, 1, min_value=min_value)
    max_str = request.args.get('max_path_length')
    max_length = _get_number(max_str, 3, max_value=max_value)

    if pmid:
        edge_class = 'bel_relation'
        end_class = 'bel'
        max_length = 1

    path_query = PathQuery(start_name=start_name,
                           end_name=end_name,
                           min_length=min_length,
                           max_length=max_length,
                           start_class=start_class,
                           end_class=end_class,
                           start_ns=start_ns,
                           end_ns=end_ns,
                           gene_path=gene_path,
                           edge_class=edge_class,
                           multiple_edge_classes=multiple_edge_classes,
                           inside_node_class=inside_node_class,
                           mesh_term=mesh_term,
                           pmids=pmid,
                           belish=belish,
                           limit=limit)
    return path_query


def get_paths() -> Union[dict, PathQuery]:
    """Return paths found for query."""
    path_query = _get_path_query()
    if isinstance(path_query, PathQuery):
        return path_query.get_paths()._asdict()
    else:
        return path_query


def get_paths_by_belish() -> Union[dict, PathQuery]:
    """Find all paths from given BELish query and return results as dictionary."""
    path_query = _get_path_query()
    if isinstance(path_query, PathQuery):
        return path_query.get_paths_by_belish()._asdict()
    else:
        return path_query


def get_paths_as_dot():
    """Execute protected method."""
    path_query = _get_path_query()
    return _get_paths_as_dot(path_query.get_paths())


def get_paths_by_belish_as_dot():
    """Find all paths from given BELish query and return results as DOT."""
    path_query = _get_path_query()
    return _get_paths_as_dot(path_query.get_paths_by_belish())


def _get_paths_as_dot(paths):
    """Find all paths between specified query and return results as DOT."""
    if isinstance(paths, PathsResult):
        edges = defaultdict(int)
        d = Digraph()
        d.attr('graph', fontname="helvetica")
        d.attr('node', shape='note')
        if len(paths.unique_nodes) == 0:
            row_template = '<B><FONT POINT-SIZE="6">{}:</FONT></B>' \
                           '<FONT POINT-SIZE="6">{}</FONT>'
            key_value_dict = {}
            for k, v in request.args.items():
                key_value_dict[k] = cgi.html.escape(v).encode('ascii', 'xmlcharrefreplace').decode("utf-8")
            legend_rows = '<BR/>'.join([row_template.format(k, v) for k, v in key_value_dict.items()])
            d.node('legend', f'<<FONT POINT-SIZE="16">NO PATHS FOUND!</FONT><BR/>{legend_rows}>')

        d.attr('node', shape='box')
        d.attr('node', style='filled')

        for rid, v in paths.unique_nodes.items():
            # print(v['class'])
            node_id = rid.replace(':', '.')
            d.attr('node', fillcolor=node_colours.get(v['class'], 'grey'))
            view_labels = get_node_view_labels(v['class'])

            sub_label = view_labels['sub_label']
            if 'involved_genes' in v:
                involved = ','.join(
                    v['involved_genes'] + v['involved_other']
                ).replace('<', '&lt;').replace('>', '&gt;')
                bel_str = v["bel"].replace('<', '&lt;').replace('>', '&gt;')
                node_label = f'<<FONT POINT-SIZE="10">{v["class"]}</FONT><BR/><FONT POINT-SIZE="16">{involved}</FONT>'\
                             f'<BR/><FONT POINT-SIZE="6">{bel_str}</FONT>>'
            else:
                label_col_list = view_labels['label']
                label_value = ''
                if len(label_col_list) == 1:
                    label_value = v[label_col_list[0]]
                elif len(label_col_list) >= 1:
                    label_value = '; '.join([str(v.get(x, '')) for x in label_col_list])

                sub_label_value = ''
                if sub_label and v.get(sub_label[0]):
                    sub_label_value = '</FONT><BR/><FONT POINT-SIZE="6">' + v[sub_label[0]]
                node_label = f'<<FONT POINT-SIZE="10">{v["class"]}</FONT><BR/>' \
                             f'<FONT POINT-SIZE="16">{label_value}{sub_label_value}</FONT>>'

            d.node(node_id, node_label)

        for v in paths.unique_edges.values():
            s_rid = v['subject_rid'].replace(':', '.')
            o_rid = v['object_rid'].replace(':', '.')
            edges[(s_rid, o_rid, v['class'])] += 1

        for edge, number_of_edge in edges.items():
            s_rid, o_rid, label = edge
            d.attr('edge', color=edge_colours.get(label, 'grey'))
            d.edge(s_rid, o_rid, f'<<FONT POINT-SIZE="8">{label} [{number_of_edge}]</FONT>>')
        return d.source
    else:
        return paths


def get_publication_year_statistics():
    """Return publication counts by year derived from BEL edges."""
    sql = "Select year, count(*) as number_of_edges from (Select citation.pub_date.left(4) as year " \
          "from bel_relation) where year!='' group by year order by year desc"
    return [x.oRecordData for x in Bel().execute(sql)]


def get_class_infos():
    """Return node or edge class metadata."""
    b = Bel()
    sql = "SELECT name, superClass, abstract, properties FROM (select expand(classes) " \
          "FROM metadata:schema) WHERE NOT (name LIKE 'O%' OR name like '_%')"
    class_name_dict = {}
    parent_dict = defaultdict(list)
    in_out_dict = {}
    in_edge_class_dict = defaultdict(list)
    out_edge_class_dict = defaultdict(list)
    for row in b.execute(sql):
        r = dict(row.oRecordData)
        in_out = {p['name']: p['linkedClass'] for p in r['properties'] if
                  'linkedClass' in p and p['name'] in ['in', 'out']}
        if in_out:
            in_out_dict[r['name']] = in_out
            in_edge_class_dict[in_out['in']].append(r['name'])
            out_edge_class_dict[in_out['out']].append(r['name'])
        r.pop('properties')
        class_name_dict[r['name']] = r
        if r.get('superClass'):  # all except roots
            parent_dict[r['superClass']].append({'name': r['name'], 'abstract': r['abstract']})

    results = {}

    for class_name in class_name_dict:
        cnd = class_name_dict[class_name]
        result = {'abstract': cnd['abstract'],
                  'parents_path': [class_name],
                  'children': parent_dict[class_name],
                  }
        check4parent = True
        while check4parent:
            last_parent = result['parents_path'][-1]
            if last_parent not in class_name_dict:
                break
            parent = class_name_dict[last_parent].get('superClass')
            if parent:
                result['parents_path'].append(parent)
            else:
                check4parent = False
        results[class_name] = result

        # get in_out from parents
        for parent in result['parents_path']:
            if parent in in_out_dict:
                results[class_name]['in_out'] = in_out_dict[parent]
                break

        if class_name in in_edge_class_dict:
            results[class_name]['in_relations'] = in_edge_class_dict[class_name]
        if class_name in out_edge_class_dict:
            results[class_name]['out_relations'] = out_edge_class_dict[class_name]
    return results


def get_node_type_by_name():
    """Return node type by given name."""
    results = get_class_infos()
    return results.get(request.args.get('name'))


def get_class_infos_by_parent_name(childs_of):
    """Get node or edge class information as DOT."""
    results = get_class_infos()
    return {k: v for k, v in results.items() if childs_of in v['parents_path']}


def _get_class_info_as_dot(get_class_method):
    """Get node or edge class information as DOT."""
    classes = get_class_method()
    graph = Digraph()
    graph.graph_attr['rankdir'] = 'LR'
    graph.node_attr['shape'] = 'plaintext'
    for node_name, v in classes.items():
        for child in [x['name'] for x in v['children']]:
            graph.edge(node_name, child)
    return graph.source


def get_bel_node_types():
    """Return BEL nodes and their metadata."""
    return get_class_infos_by_parent_name('bel')


def get_bel_node_types_as_dot():
    """Return BEL nodes as DOT."""
    return _get_class_info_as_dot(get_bel_node_types)


def get_ebel_node_types():
    """Return eBEL added nodes and their metadata."""
    return get_class_infos_by_parent_name('ebel')


def get_ebel_node_types_as_dot():
    """Return eBEL added nodes as DOT."""
    return _get_class_info_as_dot(get_ebel_node_types)


def get_bel_relation_types():
    """Return BEL edges and their metadata."""
    return get_class_infos_by_parent_name('bel_relation')


def get_bel_relation_types_as_dot():
    """Return BEL edges as DOT."""
    return _get_class_info_as_dot(get_bel_relation_types)


def get_ebel_relation_types():
    """Return eBEL added edges and their metadata."""
    return get_class_infos_by_parent_name('ebel_relation')


def get_ebel_relation_types_as_dot():
    """Return eBEL added edges as DOT."""
    return _get_class_info_as_dot(get_ebel_relation_types)


def get_documents():
    """Return a list of documents that were imported to compile BEL graph."""
    return Bel().get_documents_as_dict()


def get_pmids():
    """Return all PMIDs and their counts from BEL edges."""
    sql = "Select pmid, count(*) as number_of_edges from bel_relation " \
          "where pmid!=0 group by pmid order by number_of_edges desc"
    return [x.oRecordData for x in Bel().execute(sql)]


def get_mesh_list():
    """Return all MeSH terms and their counts from BEL edges."""
    sql = "Select value as mesh_term, count(*) as number_of_edges from " \
          "(Select expand(annotation.mesh) as mesh from bel_relation " \
          "where annotation.mesh is not null) group by value order by number_of_edges desc"
    return [x.oRecordData for x in Bel().execute(sql)]
