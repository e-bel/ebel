"""Transformer module for the transformation of lark trees."""

import typing
import logging

from lark.tree import Tree
from lark import Transformer
from lark.lexer import Token
from collections import defaultdict, namedtuple, OrderedDict

from ebel.cache import _BelScript
from ebel.constants import FILE, URL, PATTERN, LIST

log = logging.getLogger(__name__)


def get_token_dict2(token_tree_list: list) -> dict:
    """Create a dict out of a mixed list of lark.lexer.Token and tuple('name_of_rule',list(lark.lexer.Token,...)).

    Parameters
    ----------
    token_tree_list : list
        Description of parameter `token_tree_list`.

    Returns
    -------
    type
        Description of returned object.

    """
    ret_dict = defaultdict(list)

    for item in token_tree_list:

        if isinstance(item, Token):
            ret_dict[item.type].append(item.value)

        elif isinstance(item, tuple):
            ret_dict2 = defaultdict(list)

            for item2 in item[1]:
                if isinstance(item2, Token):
                    ret_dict2[item2.type].append(item2.value)

            ret_dict[item[0]] = dict(ret_dict2)
        elif isinstance(item, Tree):
            for item3 in item.children:
                ret_dict[item3.type].append(item3.value)

    return dict(ret_dict)


class _BelTransformer(Transformer):
    """Transformer optimized for JSON output.

    Vertices
    --------
        are tuples with 2 elements
        [0] := vertex name
        [1] := values

    Properties of vertices
    ----------------------
        are in OrderedDict's
        - properties with 1 value => namedtuple
        - properties with * values => List[namedtuple]
    """

    exclude_token_types = ('OB', 'CB', 'QM', 'COLON', 'COMMA', 'OCB', 'CCB')

    nt_frag = namedtuple('fragment', ('range', 'descriptor'))
    nt_nn = namedtuple('nn', ('namespace', 'name'))
    nt_var = namedtuple('variant', ('hgvs',))
    nt_ma = namedtuple('ma', ('namespace', 'name', 'default'))
    nt_pmod = namedtuple('protein_modification', ('namespace', 'name', 'type', 'amino_acid', 'position'))
    nt_support = namedtuple('support', ('text', ))
    nt_citation = namedtuple('citation', ('type', 'title', 'ref', 'pub_date', 'author_list', 'comment'))
    nt_type = namedtuple('function', ('type', 'name'))
    nt_gmod = namedtuple('gene_modification', ('namespace', 'name'))
    named_tuples = (nt_frag,
                    nt_nn,
                    nt_var,
                    nt_pmod,
                    nt_support,
                    nt_citation,
                    nt_type,
                    nt_ma,
                    nt_gmod)

    def __init__(self, force_new_db=False):
        Transformer.__init__(self)
        self.cache = _BelScript(force_new_db=force_new_db)
        self.citations = []

    def script(self, n):
        return n

    def statements_and_sets(self, n):
        return {'statements_and_sets': n}

    def abundance(self, n):
        """Return abundance."""
        return [self.nt_type('abundance', 'abundance'), n]

    def gene(self, n):
        """Return gene."""
        return [self.nt_type('abundance', 'gene'), n]

    def micro_rna(self, n):
        """Return micro_rna."""
        return [self.nt_type('abundance', 'micro_rna'), n]

    def rna(self, n):
        """Return rna."""
        return [self.nt_type('abundance', 'rna'), n]

    def protein(self, n):
        """Return protein."""
        return [self.nt_type('abundance', 'protein'), n]

    def population(self, n):
        """Return protein."""
        return [self.nt_type('abundance', 'population'), n]

    def composite(self, n):
        """Return composite."""
        return [self.nt_type('list', 'composite'), sorted(n)]

    def definitions(self, n):
        """Return definitions of namespace and annotations."""
        return {'definitions': n}

    def sec(self, n):
        """Return cellSecretion."""
        return [self.nt_type('transformation', 'cell_secretion'), [n[0]]]

    def _ns_anno_props(self, n):
        """Return properties of namespace or annotation."""
        token_names = ('KEYWORD', ('URL', 'PATTERN', 'LIST'), ('URL_DEF', 'PATTERN_DEF', 'FILE_PATH'))

        keyword, type_, value = self._get_values(n, token_names)

        value_list = []
        if type_ == 'LIST':
            in_list = self._get_tree(n, 'in_list')
            value_list = self._get_all_values_by_name(in_list, 'ENTRY')

        props = OrderedDict([
            ('keyword', keyword),
            ('type', type_),
            ('value', value),
            ('value_list', sorted(value_list))
        ])
        return props

    def namespace(self, n):
        """Return namespace vertex."""
        token_dict = get_token_dict2(n)

        keyword = token_dict['KEYWORD'][0]
        namespace_type, value = None, None

        if 'LIST' in token_dict:
            value = token_dict['ENTRY']
            namespace_type = LIST

        elif 'URL_DEF' in token_dict:
            value = token_dict['URL_DEF'][0]
            namespace_type = URL

        elif 'FILE_PATH' in token_dict:
            value = token_dict['FILE_PATH'][0]
            namespace_type = FILE

        elif 'PATTERN_DEF' in token_dict:
            value = token_dict['PATTERN_DEF'][0]
            namespace_type = PATTERN

        self.cache.set_namespace_definition(namespace_type, keyword, value)

        props = self._ns_anno_props(n)
        return {'namespace': props}

    def annotation(self, n):
        """Return namespace vertex."""
        token_dict = get_token_dict2(n)

        keyword = token_dict['KEYWORD'][0]
        annotation_type, value = None, None

        if 'LIST' in token_dict:
            value = token_dict['ENTRY']
            annotation_type = LIST

        elif 'URL_DEF' in token_dict:
            value = token_dict['URL_DEF'][0]
            annotation_type = URL

        elif 'FILE_PATH' in token_dict:
            value = token_dict['FILE_PATH'][0]
            annotation_type = FILE

        elif 'PATTERN_DEF' in token_dict:
            value = token_dict['PATTERN_DEF'][0]
            annotation_type = PATTERN

        self.cache.set_annotation_definition(annotation_type, keyword, value)

        props = self._ns_anno_props(n)
        return {'annotation': props}

    def document(self, n):
        """Return Document vertex."""
        return {'document': OrderedDict(sorted(n))}

    def _doc_prop(self, name, n):
        return (name, self._get_values(n, (('STRING_IN_QUOTES', 'WORD'),))[0])

    def document_name(self, n):
        """Return document property as tuple."""
        return self._doc_prop('name', n)

    def document_description(self, n):
        """Return document property as tuple."""
        return self._doc_prop('description', n)

    def document_version(self, n):
        """Return document property as tuple."""
        return self._doc_prop('version', n)

    def document_authors(self, n):
        """Return document property as tuple."""
        return self._doc_prop('authors', n)

    def document_contact_info(self, n):
        """Return document property as tuple."""
        return self._doc_prop('contact_info', n)

    def document_copyright(self, n):
        """Return document property as tuple."""
        return self._doc_prop('copyright', n)

    def document_licences(self, n):
        """Return document property as tuple."""
        return self._doc_prop('licences', n)

    def document_keywords(self, n):
        """Return document property as tuple."""
        return self._doc_prop('keywords', n)

    def deg(self, n):
        """Return degradation."""
        return [self.nt_type('transformation', 'degradation'), [n[0]]]

    def complex_abundance(self, n):
        """Return complex as abundance."""
        return [self.nt_type('abundance', 'complex'), [n[0]]]

    def complex_list(self, n):
        """Return complex as list."""
        return [self.nt_type('list', 'complex'), n]

    def list_complex(self, n):
        """Return abundance list of complex."""
        return sorted(n)

    def list(self, n):
        """Return list."""
        function_type = self._format_sub_obj([self.nt_type('list', 'list')])[0]
        return {'object': [function_type, [self._format_sub_obj(x) for x in sorted(n)]]}

    def act2(self, n):
        """Return activity."""
        abundance = self._get_tree(n, 'act_abundance').children[0]
        ma = self._get_dict_value(n, 'ma')
        if ma:
            return [self.nt_type('process', 'activity'), abundance, ma._asdict()]
        else:
            return [self.nt_type('process', 'activity'), abundance]

    def act(self, n):
        """Return activity."""
        return [self.nt_type('process', 'activity'), n]

    def tloc(self, n):
        """Return tloc."""
        return [self.nt_type('transformation', 'translocation'), n]

    def _get_rel(self, n):
        return {'relation': n[0].data}

    def nested_relation(self, n):
        """Return nested relation."""
        return {'nested_relation': n[0]}

    def relation_with_list(self, n):
        """Return relation."""
        return self._get_rel(n)

    def relation_basic(self, n):
        """Return relation."""
        return self._get_rel(n)

    def rel_with_list_object(self, n):
        """Return relation."""
        return self._get_rel(n)

    def biomarker_relation(self, n):
        """Return relation."""
        return self._get_rel(n)

    def process_relation(self, n):
        """Return relation."""
        return self._get_rel(n)

    def analogous_relation(self, n):
        """Return relation."""
        return self._get_rel(n)

    def additional_relations(self, n):
        """Return relation."""
        return self._get_rel(n)

    def transc_relation(self, n):
        """Return relation."""
        return self._get_rel(n)

    def transl_relation(self, n):
        """Return relation."""
        return self._get_rel(n)

    def has_members(self, n):
        """Return relation."""
        return {'relation': 'has_members'}

    def statement(self, n: list):
        """Return statement."""
        return {'statement': n}

    def subject(self, n):
        """Return subject."""
        return {'subject': self._format_sub_obj(n[0])}

    def nested_subject(self, n):
        """Return nested subject."""
        return {'nested_subject': self._format_sub_obj(n[0])}

    def nested_object(self, n):
        """Return nested subject."""
        return {'nested_object': self._format_sub_obj(n[0])}

    def sets(self, n):
        """Return sets."""
        return {'sets': n}

    def evidence(self, n):
        """Return support.

        support formily known as evidence, supprtingText
        """
        return {'evidence': n[0].value}

    def citation(self, n):
        """Return citation."""
        tv_dict = {x.type: x.value for x in n if isinstance(x, Token)}
        c_title, c_pubdate, c_author_list, c_comment = '', '', '', ''
        c_type = tv_dict['C_TYPE']

        if "ONLY_2_PARAMETERS" in tv_dict:
            c_ref = tv_dict['C_PARAM2']
        else:
            c_title = tv_dict['C_PARAM2']
            c_ref = tv_dict['C_PARAM3']
            c_pubdate = tv_dict['C_PUBDATE'] if 'C_PUBDATE' in tv_dict else ''
            c_author_list = tv_dict['C_AUTHORLIST'] if 'C_AUTHORLIST' in tv_dict else ''
            c_comment = tv_dict['C_COMMENT'] if 'C_COMMENT' in tv_dict else ''

        nt = self.nt_citation(type=c_type,
                              title=c_title,
                              ref=c_ref,
                              pub_date=c_pubdate,
                              author_list=c_author_list,
                              comment=c_comment)

        self.citations.append({'citation_type': c_type, 'citation_id': c_ref})

        return {'citation': nt._asdict()}

    def statement_group(self, n):
        """Return statement group."""
        return {'statement_group': self._get_value(n, 'GROUP_NAME')}

    def set_annotation(self, n):
        """Return annotation sets."""
        entries = []
        annotation_key = ""
        for tkn in n:
            if tkn.type == "KEYWORD":
                annotation_key = tkn.value
            elif tkn.type == "ANNO_SET_ENTRY":
                entries.append(tkn)

        for entry in entries:
            self.cache.set_annotation_entry(
                annotation=annotation_key,
                entry=entry.value,
                token=entry
            )

        keyword = self._get_value(n, 'KEYWORD')
        entries = self._get_all_values_by_name(n, 'ANNO_SET_ENTRY')
        return {'set': {keyword: entries}}

    def unset(self, n):
        """Return unsets."""
        keywords = self._get_all_values_by_name(n, 'ANNO_KEYWORD')
        return {'unset': keywords}

    def object(self, n):
        """Return object."""
        return {'object': self._format_sub_obj(n[0])}

    def molec_process(self, n):
        """Return molecular process."""
        return {'molec_process': self._format_sub_obj(n[0])}

    def act_or_abundance(self, n):
        """Return activity or abundance."""
        return {'act_or_abundance': self._format_sub_obj(n[0])}

    def transformation(self, n):
        """Return transformation."""
        return {'transformation': self._format_sub_obj(n[0])}

    def pat(self, n):
        """Return object."""
        return {'pat': self._format_sub_obj(n[0])}

    def transc_subject(self, n):
        return self.subject(n)

    def transc_object(self, n):
        return self.object(n)

    def transl_subject(self, n):
        return self.subject(n)

    def transl_object(self, n):
        return self.object(n)

    def surf(self, n):
        return [self.nt_type('transformation', 'cell_surface_expression'), n]

    def bp(self, n):
        """Return biological process."""
        return [self.nt_type('process', 'biological_process'), [n[0]]]

    def path(self, n):
        """Return path."""
        return [self.nt_type('process', 'pathology'), [n[0]]]

    def _format_sub_obj(self, obj):
        """Change namedtuples to tuple(name_of_namedtuple,dictionary)."""
        if isinstance(obj, (list, tuple)):
            for i in range(len(obj)):
                if not isinstance(obj[i], self.named_tuples) and isinstance(obj[i], (list, tuple)):
                    self._format_sub_obj(obj[i])
                elif isinstance(obj[i], self.named_tuples):
                    function_type = obj[i].__class__.__name__
                    if function_type == "function":
                        obj[i] = {function_type: obj[i]._asdict()}
                    else:
                        obj[i] = obj[i]._asdict()
        return obj

    def protein_changes(self, n):
        """Create dict of protein changes."""
        return self.changes(n)

    def statement_comment(self, n):
        return {'statement_comment': ' '.join([x.value for x in n]).strip()}

    def changes(self, n):
        """Create dict of abundance changes."""
        return [list((x[0], [x[1]])) for x in sorted(list(set(n)))]

    def gene_changes(self, n):
        """Return gene abundance changes; Only valid in BEL 2.1."""
        return [list((x[0], [x[1]])) for x in sorted(list(set(n)))]

    def gmod(self, n):
        """Return gmod; Only valid in BEL 2.1."""
        nn = [x for x in n if x.__class__.__name__ == 'nn']
        namespace = "TestNS"
        name = "TestName"

        if nn:
            namespace = nn[0].namespace
            name = nn[0].name
        nt = self.nt_gmod(
            namespace=namespace,
            name=name)

        return self.nt_type('modifier', 'gmod'), nt

    def ma(self, n):
        """Transform tokens to dict(function_name: namedtuple)."""
        namespace, name, default = (None,) * 3
        if type(n[0]).__name__ == 'nn':
            nt = n[0]
            namespace = nt.namespace
            name = nt.name

        elif n[0].data == 'ma_default':
            default = n[0].children[0].data

        return self.nt_ma(namespace=namespace, name=name, default=default)

    def frag(self, n) -> tuple:
        """Transform frag tokens to nametuple."""
        frag_range, frag_descriptor = self._get_values(n, ('F_RANGE', 'F_DESCRIPTOR'))
        nt = self.nt_frag(range=frag_range, descriptor=frag_descriptor)

        return self.nt_type('modifier', 'fragment'), nt

    def loc(self, n) -> tuple:
        """Transform tokens to dict(function_name: namedtuple)."""
        return self.nt_type('modifier', 'location'), n[0]

    def var(self, n) -> tuple:
        """Transform tokens to dict(function_name: namedtuple)."""
        return self.nt_type('modifier', 'variant'), self.nt_var(n[0].value)

    def nn(self, n):
        """Transform tokens to dict(function_name: namedtuple)."""
        token_names = ('NAMESPACE_KEYWORD', ('NAME_WITHOUT_QUOTES', 'STRING_SIMPLE'))
        namespace, name = self._get_values(n, token_names)

        token_dict = {x.type: x for x in n}
        name_with_quotes = token_dict.get('NAME_WITHOUT_QUOTES')
        simple_string = token_dict.get('STRING_SIMPLE')
        entry_token = name_with_quotes or simple_string

        self.cache.set_namespace_entry(
            namespace=namespace,
            entry=name,
            token=entry_token
        )

        return self.nt_nn(namespace=namespace, name=name)

    def pmod(self, n) -> dict:
        """Transform tokens to dict(function_name: namedtuple)."""
        namespace, name = '', ''

        pos_value = self._get_value(n, 'POSITION')
        position = int(pos_value) if pos_value else 0

        nn = [x for x in n if x.__class__.__name__ == 'nn']
        if nn:
            namespace = nn[0].namespace
            name = nn[0].name

        aa = self._get_dict_value(n, 'amino_acid')
        amino_acid = aa if aa else ''

        ptype = self._get_dict_value(n, 'pmod_type')
        type_ = ptype if ptype else ''

        nt = self.nt_pmod(
            namespace=namespace,
            name=name,
            type=type_,
            amino_acid=amino_acid,
            position=position)

        return self.nt_type('modifier', 'pmod'), nt

    def amino_acid(self, n):
        """Return amino acid."""
        return {'amino_acid': n[0].data.split('_')[1].upper()}

    def pmod_type(self, n):
        """Return pmod_type."""
        return {'pmod_type': n[0].data}

    def from_loc(self, n):
        """Return tloc."""
        return [self.nt_type('translocation', 'from_location'), n]

    def to_loc(self, n):
        """Return tloc."""
        return [self.nt_type('translocation', 'to_location'), n]

    def rxn(self, n):
        """Return reaction."""
        return [self.nt_type('transformation', 'reaction'), n]

    def reactants(self, n):
        """Return reactants."""
        return [self.nt_type('reaction_partner', 'reactants'), sorted(n)]

    def products(self, n):
        """Return products."""
        return [self.nt_type('reaction_partner', 'products'), sorted(n)]

    def fusion(self, n):
        """Return fusion."""
        return n[0]

    def _fusion_range(self, n):
        """Return fusion."""
        range_types = ('GENE_FUSION_RANGE', 'RNA_FUSION_RANGE', 'PROTEIN_FUSION_RANGE')
        fusion_range = self._get_value(n, range_types)
        return OrderedDict([('fusion_range', fusion_range)])

    def gene_fusion(self, n):
        """Return  gene fusion."""
        return [self.nt_type('other', 'fusion_gene'), n]

    def gene_fusion_range(self, n):
        """Return fusion range."""
        return self._fusion_range(n)

    def fus_gene1(self, n):
        return ['gene1', n]

    def fus_gene2(self, n):
        return ['gene2', n]

    def fus_rna1(self, n):
        return ['rna1', n]

    def fus_rna2(self, n):
        return ['rna2', n]

    def fus_protein1(self, n):
        return ['protein1', n]

    def fus_protein2(self, n):
        return ['protein2', n]

    def rna_fusion(self, n):
        """Return rna fusion."""
        return [self.nt_type('other', 'fusion_rna'), n]

    def rna_fusion_range(self, n):
        """Return fusion range."""
        return self._fusion_range(n)

    def protein_fusion(self, n):
        """Return protein fusion."""
        return [self.nt_type('other', 'fusion_protein'), n]

    def protein_fusion_range(self, n):
        """Return fusion range."""
        return self._fusion_range(n)

    def _get_dict_value(self, n, key_name):
        """Return value of key_name for first dict with key_name."""
        for e in n:
            if type(e) == dict and key_name in e:
                return e[key_name]

    def __get_token_dict(self, tokens: typing.List[Token]) -> dict:
        """Get dictionary of tokens with typs as key."""
        return {t.type: t.value for t in tokens if isinstance(t, Token)}

    def _get_value(self, tokens, token_name):
        """Get first Token value of list with token_name.

        If token_name is a list method checks aginst list.
        """
        token_names = (token_name,) if type(token_name) == str else token_name
        for t in tokens:
            if isinstance(t, Token) and t.type in token_names:
                return t.value

    def _get_values(self, tokens, token_names: typing.Iterable) -> list:
        """Get list of token values in same order then token_names.

        If token name not exists empty str is returned.
        If token_names element is a Iterable of str, first token value is
        return from this list.
        """
        t_dict = self.__get_token_dict(tokens)
        ret_lst = []

        for t_name in token_names:

            if isinstance(t_name, str):
                ret_lst.append(t_dict.get(t_name, ''))

            elif isinstance(t_name, typing.Iterable):
                value = ''
                for name in t_name:
                    value = t_dict.get(name)
                    if value:
                        break
                ret_lst.append(value)

        return ret_lst

    def _get_tree(self, n: list, tree_name):
        """Return first lark.Tree, namedtuple or dict linked to tree_name."""
        for e in n:
            if isinstance(e, Tree) and e.data == tree_name:
                return e
            elif isinstance(e, dict) and len(e.keys()) == 1:
                return e[tree_name]

        raise('type not supported or empty list')

    def _get_all_values_by_name(self, tree_or_tokens, token_name):
        n = tree_or_tokens
        if isinstance(tree_or_tokens, Tree):
            n = tree_or_tokens.children

        return sorted([x.value for x in n if isinstance(x, Token) and x.type == token_name])

    def _first_tree(self, n: list) -> Tree:
        """Return first tree in list."""
        for e in n:
            if isinstance(e, Tree):
                return e
