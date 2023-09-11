"""Transformer module for the transformation of lark trees."""

import logging
import re
import typing
from collections import Counter, OrderedDict, defaultdict, namedtuple
from typing import DefaultDict, Dict, Generator, List, Set

from lark import Transformer
from lark.lexer import Token
from lark.tree import Tree

from ebel.cache import logger
from ebel.constants import ALLOWED_TYPES, FILE, GRAMMAR_START_ANNO, GRAMMAR_START_NS, LIST, PATTERN, URL
from ebel.errors import (
    NotDownloadedFromUrl,
    NotInAnnotationList,
    NotInAnnotationPattern,
    NotInAnnotationUrl,
    NotInNamespaceList,
    NotInNamespacePattern,
    NotInNamespaceUrl,
    WithoutDefinedAnnotation,
    WithoutDefinedNamespace,
    _Error,
)
from ebel.manager.models import Annotation as AnnotationModel
from ebel.manager.models import AnnotationEntry, AnnotationManager
from ebel.manager.models import Namespace as NamespaceModel
from ebel.manager.models import NamespaceEntry, NamespaceManager, reset_tables
from ebel.tools import BelRdb
from ebel.warning_definitions import AlsoUsedInOtherNamespace, _Warning

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

    exclude_token_types = ("OB", "CB", "QM", "COLON", "COMMA", "OCB", "CCB")

    nt_frag = namedtuple("fragment", ("range", "descriptor"))
    nt_nn = namedtuple("nn", ("namespace", "name"))
    nt_var = namedtuple("variant", ("hgvs",))
    nt_ma = namedtuple("ma", ("namespace", "name", "default"))
    nt_pmod = namedtuple("protein_modification", ("namespace", "name", "type", "amino_acid", "position"))
    nt_support = namedtuple("support", ("text",))
    nt_citation = namedtuple("citation", ("type", "title", "ref", "pub_date", "author_list", "comment"))
    nt_type = namedtuple("function", ("type", "name"))
    nt_gmod = namedtuple("gene_modification", ("namespace", "name"))
    named_tuples = (
        nt_frag,
        nt_nn,
        nt_var,
        nt_pmod,
        nt_support,
        nt_citation,
        nt_type,
        nt_ma,
        nt_gmod,
    )

    def __init__(self, force_new_db=False):
        Transformer.__init__(self)
        self.cache = _BelScript(force_new_db=force_new_db)
        self.citations = []

    @staticmethod
    def script(n):
        return n

    @staticmethod
    def statements_and_sets(n):
        return {"statements_and_sets": n}

    def abundance(self, n):
        """Return abundance."""
        return [self.nt_type("abundance", "abundance"), n]

    def gene(self, n):
        """Return gene."""
        return [self.nt_type("abundance", "gene"), n]

    def micro_rna(self, n):
        """Return micro_rna."""
        return [self.nt_type("abundance", "micro_rna"), n]

    def rna(self, n):
        """Return rna."""
        return [self.nt_type("abundance", "rna"), n]

    def protein(self, n):
        """Return protein."""
        return [self.nt_type("abundance", "protein"), n]

    def population(self, n):
        """Return protein."""
        return [self.nt_type("abundance", "population"), n]

    def composite(self, n):
        """Return composite."""
        return [self.nt_type("list", "composite"), sorted(n)]

    @staticmethod
    def definitions(n):
        """Return definitions of namespace and annotations."""
        return {"definitions": n}

    def sec(self, n):
        """Return cellSecretion."""
        return [self.nt_type("transformation", "cell_secretion"), [n[0]]]

    def _ns_anno_props(self, n):
        """Return properties of namespace or annotation."""
        token_names = (
            "KEYWORD",
            ("URL", "PATTERN", "LIST"),
            ("URL_DEF", "PATTERN_DEF", "FILE_PATH"),
        )

        keyword, type_, value = self._get_values(n, token_names)

        value_list = []
        if type_ == "LIST":
            in_list = self._get_tree(n, "in_list")
            value_list = self._get_all_values_by_name(in_list, "ENTRY")

        props = OrderedDict(
            [
                ("keyword", keyword),
                ("type", type_),
                ("value", value),
                ("value_list", sorted(value_list)),
            ]
        )
        return props

    def namespace(self, n):
        """Return namespace vertex."""
        token_dict = get_token_dict2(n)

        keyword = token_dict["KEYWORD"][0]
        namespace_type, value = None, None

        if "LIST" in token_dict:
            value = token_dict["ENTRY"]
            namespace_type = LIST

        elif "URL_DEF" in token_dict:
            value = token_dict["URL_DEF"][0]
            namespace_type = URL

        elif "FILE_PATH" in token_dict:
            value = token_dict["FILE_PATH"][0]
            namespace_type = FILE

        elif "PATTERN_DEF" in token_dict:
            value = token_dict["PATTERN_DEF"][0]
            namespace_type = PATTERN

        self.cache.set_namespace_definition(namespace_type, keyword, value)

        props = self._ns_anno_props(n)
        return {"namespace": props}

    def annotation(self, n):
        """Return namespace vertex."""
        token_dict = get_token_dict2(n)

        keyword = token_dict["KEYWORD"][0]
        annotation_type, value = None, None

        if "LIST" in token_dict:
            value = token_dict["ENTRY"]
            annotation_type = LIST

        elif "URL_DEF" in token_dict:
            value = token_dict["URL_DEF"][0]
            annotation_type = URL

        elif "FILE_PATH" in token_dict:
            value = token_dict["FILE_PATH"][0]
            annotation_type = FILE

        elif "PATTERN_DEF" in token_dict:
            value = token_dict["PATTERN_DEF"][0]
            annotation_type = PATTERN

        self.cache.set_annotation_definition(annotation_type, keyword, value)

        props = self._ns_anno_props(n)
        return {"annotation": props}

    @staticmethod
    def document(n):
        """Return Document vertex."""
        return {"document": OrderedDict(sorted(n))}

    def _doc_prop(self, name, n):
        return (name, self._get_values(n, (("STRING_IN_QUOTES", "WORD"),))[0])

    def document_name(self, n):
        """Return document property as tuple."""
        return self._doc_prop("name", n)

    def document_description(self, n):
        """Return document property as tuple."""
        return self._doc_prop("description", n)

    def document_version(self, n):
        """Return document property as tuple."""
        return self._doc_prop("version", n)

    def document_authors(self, n):
        """Return document property as tuple."""
        return self._doc_prop("authors", n)

    def document_contact_info(self, n):
        """Return document property as tuple."""
        return self._doc_prop("contact_info", n)

    def document_copyright(self, n):
        """Return document property as tuple."""
        return self._doc_prop("copyright", n)

    def document_licences(self, n):
        """Return document property as tuple."""
        return self._doc_prop("licences", n)

    def document_keywords(self, n):
        """Return document property as tuple."""
        return self._doc_prop("keywords", n)

    def deg(self, n):
        """Return degradation."""
        return [self.nt_type("transformation", "degradation"), [n[0]]]

    def complex_abundance(self, n):
        """Return complex as abundance."""
        return [self.nt_type("abundance", "complex"), [n[0]]]

    def complex_list(self, n):
        """Return complex as list."""
        return [self.nt_type("list", "complex"), n]

    @staticmethod
    def list_complex(n):
        """Return abundance list of complex."""
        return sorted(n)

    def list(self, n):
        """Return list."""
        function_type = self._format_sub_obj([self.nt_type("list", "list")])[0]
        return {"object": [function_type, [self._format_sub_obj(x) for x in sorted(n)]]}

    def act2(self, n):
        """Return activity."""
        abundance = self._get_tree(n, "act_abundance").children[0]
        ma = self._get_dict_value(n, "ma")
        if ma:
            return [self.nt_type("process", "activity"), abundance, ma._asdict()]
        else:
            return [self.nt_type("process", "activity"), abundance]

    def act(self, n):
        """Return activity."""
        return [self.nt_type("process", "activity"), n]

    def tloc(self, n):
        """Return tloc."""
        return [self.nt_type("transformation", "translocation"), n]

    @staticmethod
    def _get_rel(n):
        return {"relation": n[0].data}

    @staticmethod
    def nested_relation(n):
        """Return nested relation."""
        return {"nested_relation": n[0]}

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

    def orthologous_relation(self, n):
        """Return orthologous relation."""
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

    @staticmethod
    def has_members(n):
        """Return relation."""
        return {"relation": "has_members"}

    @staticmethod
    def statement(n: list):
        """Return statement."""
        return {"statement": n}

    def subject(self, n):
        """Return subject."""
        return {"subject": self._format_sub_obj(n[0])}

    def nested_subject(self, n):
        """Return nested subject."""
        return {"nested_subject": self._format_sub_obj(n[0])}

    def nested_object(self, n):
        """Return nested subject."""
        return {"nested_object": self._format_sub_obj(n[0])}

    @staticmethod
    def sets(n):
        """Return sets."""
        return {"sets": n}

    @staticmethod
    def evidence(n):
        """Return support.

        support formily known as evidence, supprtingText
        """
        return {"evidence": n[0].value}

    def citation(self, n):
        """Return citation."""
        tv_dict = {x.type: x.value for x in n if isinstance(x, Token)}
        c_title, c_pubdate, c_author_list, c_comment = "", "", "", ""
        c_type = tv_dict["C_TYPE"]

        if "ONLY_2_PARAMETERS" in tv_dict:
            c_ref = tv_dict["C_PARAM2"]
        else:
            c_title = tv_dict["C_PARAM2"]
            c_ref = tv_dict["C_PARAM3"]
            c_pubdate = tv_dict["C_PUBDATE"] if "C_PUBDATE" in tv_dict else ""
            c_author_list = tv_dict["C_AUTHORLIST"] if "C_AUTHORLIST" in tv_dict else ""
            c_comment = tv_dict["C_COMMENT"] if "C_COMMENT" in tv_dict else ""

        nt = self.nt_citation(
            type=c_type,
            title=c_title,
            ref=c_ref,
            pub_date=c_pubdate,
            author_list=c_author_list,
            comment=c_comment,
        )

        self.citations.append({"citation_type": c_type, "citation_id": c_ref})

        return {"citation": nt._asdict()}

    def statement_group(self, n):
        """Return statement group."""
        return {"statement_group": self._get_value(n, "GROUP_NAME")}

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
            self.cache.set_annotation_entry(annotation=annotation_key, entry=entry.value, token=entry)

        keyword = self._get_value(n, "KEYWORD")
        entries = self._get_all_values_by_name(n, "ANNO_SET_ENTRY")
        return {"set": {keyword: entries}}

    def unset(self, n):
        """Return unsets."""
        keywords = self._get_all_values_by_name(n, "ANNO_KEYWORD")
        return {"unset": keywords}

    def object(self, n):
        """Return object."""
        return {"object": self._format_sub_obj(n[0])}

    def molec_process(self, n):
        """Return molecular process."""
        return self.object(n)

    def act_or_abundance(self, n):
        """Return activity or abundance."""
        return {"act_or_abundance": self._format_sub_obj(n[0])}

    def transformation(self, n):
        """Return transformation."""
        return {"transformation": self._format_sub_obj(n[0])}

    def pat(self, n):
        """Return object."""
        return self.subject(n)

    def transc_subject(self, n):
        return self.subject(n)

    def transc_object(self, n):
        return self.object(n)

    def transl_subject(self, n):
        return self.subject(n)

    def transl_object(self, n):
        return self.object(n)

    def ortho_subject(self, n):
        """Return orthologous gene subject."""
        return self.subject(n)

    def ortho_object(self, n):
        """Return orthologous gene object."""
        return self.object(n)

    def surf(self, n):
        return [self.nt_type("transformation", "cell_surface_expression"), n]

    def bp(self, n):
        """Return biological process."""
        return [self.nt_type("process", "biological_process"), [n[0]]]

    def path(self, n):
        """Return path."""
        return [self.nt_type("process", "pathology"), [n[0]]]

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

    @staticmethod
    def statement_comment(n):
        return {"statement_comment": " ".join([x.value for x in n]).strip()}

    @staticmethod
    def changes(n):
        """Create dict of abundance changes."""
        return [list((x[0], [x[1]])) for x in sorted(list(set(n)))]

    @staticmethod
    def gene_changes(n):
        """Return gene abundance changes; Only valid in BEL 2.1."""
        return [list((x[0], [x[1]])) for x in sorted(list(set(n)))]

    def gmod(self, n):
        """Return gmod; Only valid in BEL 2.1."""
        nn = [x for x in n if x.__class__.__name__ == "nn"]
        namespace = "TestNS"
        name = "TestName"

        if nn:
            namespace = nn[0].namespace
            name = nn[0].name
        nt = self.nt_gmod(namespace=namespace, name=name)

        return self.nt_type("modifier", "gmod"), nt

    def ma(self, n):
        """Transform tokens to dict(function_name: namedtuple)."""
        namespace, name, default = (None,) * 3
        if type(n[0]).__name__ == "nn":
            nt = n[0]
            namespace = nt.namespace
            name = nt.name

        elif n[0].data == "ma_default":
            default = n[0].children[0].data

        return self.nt_ma(namespace=namespace, name=name, default=default)

    def frag(self, n) -> tuple:
        """Transform frag tokens to nametuple."""
        frag_range, frag_descriptor = self._get_values(n, ("F_RANGE", "F_DESCRIPTOR"))
        nt = self.nt_frag(range=frag_range, descriptor=frag_descriptor)

        return self.nt_type("modifier", "fragment"), nt

    def loc(self, n) -> tuple:
        """Transform tokens to dict(function_name: namedtuple)."""
        return self.nt_type("modifier", "location"), n[0]

    def var(self, n) -> tuple:
        """Transform tokens to dict(function_name: namedtuple)."""
        return self.nt_type("modifier", "variant"), self.nt_var(n[0].value)

    def nn(self, n):
        """Transform tokens to dict(function_name: namedtuple)."""
        token_names = ("NAMESPACE_KEYWORD", ("NAME_WITHOUT_QUOTES", "STRING_SIMPLE"))
        namespace, name = self._get_values(n, token_names)

        token_dict = {x.type: x for x in n}
        name_with_quotes = token_dict.get("NAME_WITHOUT_QUOTES")
        simple_string = token_dict.get("STRING_SIMPLE")
        entry_token = name_with_quotes or simple_string

        self.cache.set_namespace_entry(namespace=namespace, entry=name, token=entry_token)

        return self.nt_nn(namespace=namespace, name=name)

    def pmod(self, n) -> dict:
        """Transform tokens to dict(function_name: namedtuple)."""
        namespace, name = "", ""

        pos_value = self._get_value(n, "POSITION")
        position = int(pos_value) if pos_value else 0

        nn = [x for x in n if x.__class__.__name__ == "nn"]
        if nn:
            namespace = nn[0].namespace
            name = nn[0].name

        aa = self._get_dict_value(n, "amino_acid")
        amino_acid = aa if aa else ""

        ptype = self._get_dict_value(n, "pmod_type")
        type_ = ptype if ptype else ""

        nt = self.nt_pmod(
            namespace=namespace,
            name=name,
            type=type_,
            amino_acid=amino_acid,
            position=position,
        )

        return self.nt_type("modifier", "pmod"), nt

    @staticmethod
    def amino_acid(n):
        """Return amino acid."""
        return {"amino_acid": n[0].data.split("_")[1].upper()}

    @staticmethod
    def pmod_type(n):
        """Return pmod_type."""
        return {"pmod_type": n[0].data}

    def from_loc(self, n):
        """Return tloc."""
        return [self.nt_type("translocation", "from_location"), n]

    def to_loc(self, n):
        """Return tloc."""
        return [self.nt_type("translocation", "to_location"), n]

    def rxn(self, n):
        """Return reaction."""
        return [self.nt_type("transformation", "reaction"), n]

    def reactants(self, n):
        """Return reactants."""
        return [self.nt_type("reaction_partner", "reactants"), sorted(n)]

    def products(self, n):
        """Return products."""
        return [self.nt_type("reaction_partner", "products"), sorted(n)]

    @staticmethod
    def fusion(n):
        """Return fusion."""
        return n[0]

    def _fusion_range(self, n):
        """Return fusion."""
        range_types = ("GENE_FUSION_RANGE", "RNA_FUSION_RANGE", "PROTEIN_FUSION_RANGE")
        fusion_range = self._get_value(n, range_types)
        return OrderedDict([("fusion_range", fusion_range)])

    def gene_fusion(self, n):
        """Return  gene fusion."""
        return [self.nt_type("other", "fusion_gene"), n]

    def gene_fusion_range(self, n):
        """Return fusion range."""
        return self._fusion_range(n)

    @staticmethod
    def fus_gene1(n):
        return ["gene1", n]

    @staticmethod
    def fus_gene2(n):
        return ["gene2", n]

    @staticmethod
    def fus_rna1(n):
        return ["rna1", n]

    @staticmethod
    def fus_rna2(n):
        return ["rna2", n]

    @staticmethod
    def fus_protein1(n):
        return ["protein1", n]

    @staticmethod
    def fus_protein2(n):
        return ["protein2", n]

    def rna_fusion(self, n):
        """Return rna fusion."""
        return [self.nt_type("other", "fusion_rna"), n]

    def rna_fusion_range(self, n):
        """Return fusion range."""
        return self._fusion_range(n)

    def protein_fusion(self, n):
        """Return protein fusion."""
        return [self.nt_type("other", "fusion_protein"), n]

    def protein_fusion_range(self, n):
        """Return fusion range."""
        return self._fusion_range(n)

    @staticmethod
    def _get_dict_value(n, key_name):
        """Return value of key_name for first dict with key_name."""
        for e in n:
            if isinstance(e, dict) and key_name in e:
                return e[key_name]

    @staticmethod
    def __get_token_dict(tokens: typing.List[Token]) -> dict:
        """Get dictionary of tokens with typs as key."""
        return {t.type: t.value for t in tokens if isinstance(t, Token)}

    @staticmethod
    def _get_value(tokens, token_name):
        """Get first Token value of list with token_name.

        If token_name is a list method checks aginst list.
        """
        token_names = (token_name,) if isinstance(token_name, str) else token_name
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
                ret_lst.append(t_dict.get(t_name, ""))

            elif isinstance(t_name, typing.Iterable):
                value = ""
                for name in t_name:
                    value = t_dict.get(name)
                    if value:
                        break
                ret_lst.append(value)

        return ret_lst

    @staticmethod
    def _get_tree(n: list, tree_name):
        """Return first lark.Tree, namedtuple or dict linked to tree_name."""
        for e in n:
            if isinstance(e, Tree) and e.data == tree_name:
                return e
            elif isinstance(e, dict) and len(e.keys()) == 1:
                return e[tree_name]

        raise "Type not supported or empty list"

    @staticmethod
    def _get_all_values_by_name(tree_or_tokens, token_name):
        n = tree_or_tokens
        if isinstance(tree_or_tokens, Tree):
            n = tree_or_tokens.children

        return sorted([x.value for x in n if isinstance(x, Token) and x.type == token_name])

    @staticmethod
    def _first_tree(n: list) -> Tree:
        """Return first tree in list."""
        for e in n:
            if isinstance(e, Tree):
                return e


class _BelScript:
    """Cache the content of the BEL script and methods to find errors and warnings."""

    def __init__(self, force_new_db):
        """Init."""
        # setup database
        engine = BelRdb().engine

        self.force_new_db = force_new_db
        reset_tables(engine, self.force_new_db)

        self._namespaces = Namespaces()  # entries Namespace objects
        self._annotations = Annotations()  # entries Annotation objects

        self.__namespace_in_db_updated = False
        self.__annotations_in_db_updated = False

        self._namespace_entries = NamespaceEntries()
        self._annotation_entries = AnnotationEntries()

        self.notDownloadedFromUrls = []

        self.namespace_manager = NamespaceManager(
            model=NamespaceModel,
            entries_model=NamespaceEntry,
            grammar_start=GRAMMAR_START_NS,
        )

        self.annotation_manager = AnnotationManager(
            model=AnnotationModel,
            entries_model=AnnotationEntry,
            grammar_start=GRAMMAR_START_ANNO,
        )

    def set_namespace_definition(self, as_type, keyword, value):
        """Set an annotation definition with type, keyword and value value could be 'file', 'url' or 'list'.

        :param str as_type: 'file', 'url' or 'list'
        :param str keyword: namespace keyword
        :param str value: URL, file path or list
        """
        if as_type in ALLOWED_TYPES:
            self._namespaces.add(as_type, keyword, value)
            return True
        else:
            logger.error("{} is not a allowed type of {}".format(as_type, ALLOWED_TYPES))
            return False

    def set_annotation_definition(self, as_type, keyword, value):
        """Set an annotation definition with type, keyword and value could be 'file', 'url' or 'list'.

        :param str as_type: 'file', 'url' or 'list'
        :param str keyword: namespace keyword
        :param str value: URL, file path or list
        """
        if as_type in ALLOWED_TYPES:
            self._annotations.add(as_type, keyword, value)
            return True
        else:
            logger.error("{} is not an allowed type of {}".format(as_type, ALLOWED_TYPES))
            return False

    def set_annotation_entry(self, annotation: str, entry: str, token: Token):
        """Set annotation, entry and lark.lexer.Token token.

        :param str annotation: annotation
        :param str entry: entry
        :param lark.lexer.Token token:
        """
        self._annotation_entries.set_annotation_entry(keyword=annotation, entry=entry, token=token)

    def set_namespace_entry(self, namespace: str, entry: str, token: Token):
        """Set namespace, entry and lark.lexer.Token token.

        :param str namespace:
        :param str entry:
        :param lark.lexer.Token token:
        """
        if not isinstance(token, Token):
            raise Exception("expecting Token in cache.set_namespace_entry")

        self._namespace_entries.set_namespace_entry(keyword=namespace, entry=entry, token=token)

    @property
    def errors(self) -> List[_Error]:
        """Execute all methods to find errors and warnings."""
        self.update_database()

        # all errors are children from errors._Error instances
        return (
            self.notDownloadedFromUrls
            + self.entries_without_namespace
            + self.entries_without_annotation
            + self.entries_not_in_namespace_url
            + self.entries_not_in_annotation_url
            + self.entries_not_in_namespace_list
            + self.entries_not_in_annotation_list
            + self.entries_not_in_namespace_pattern
            + self.entries_not_in_annotation_pattern
        )

    @property
    def warnings(self) -> List[_Warning]:
        """Execute all methods to find warnings."""
        if not (self.__namespace_in_db_updated and self.__annotations_in_db_updated):
            self.update_database()

        # all warnings are children from warnings._Warning instances
        return self.entries_also_in_other_namespace

    @property
    def entries_also_in_other_namespace(self) -> List[AlsoUsedInOtherNamespace]:
        """Return WithoutDefinedNamespace list."""
        ret = []
        # extract all entries used in BEL statements and create a dict of lower entries with all keywords
        entry_keyword_dict = defaultdict(set)
        for keyword1, entries in self._namespace_entries.entries.items():
            for entry in entries:
                entry_keyword_dict[entry.lower()] |= {keyword1}
        # identify all ambiguous entries (in more than 1 namespace)
        ambiguous_entries = {entry: keywords for entry, keywords in entry_keyword_dict.items() if len(keywords) > 1}

        # ToDo: iterate all lower entries an check for permutation
        #        for lower_entry in entry_keyword_dict:
        #            if lower_entry.count(",") == 1:
        #                reverse_without_comma = " ".join([x.strip() for x in lower_entry.split(",")][::-1])
        #                if reverse_without_comma in entry_keyword_dict:
        #                    print(lower_entry,
        #                    "%s exists in %s" % (reverse_without_comma,
        #                    entry_keyword_dict[reverse_without_comma]))
        #                    ret.append(AlsoUsedInOtherNamespace(keyword=keyword2,
        #                                                        entry=entry,
        #                                                        line_number=token.line,
        #                                                        column=token.column,
        #                                                        hint=hint))

        # iterate all tokens with namespace entries and check if they are also exists in ambiguous entries
        for keyword2, entries_tokens in self._namespace_entries.tokens.items():
            for entry, tokens in entries_tokens.items():
                if entry.lower() in ambiguous_entries:
                    ambiguous_tokens = self._namespace_entries.tokens[keyword2][entry]
                    for token in ambiguous_tokens:
                        hint = "%s exists also in %s" % (
                            entry,
                            ambiguous_entries[entry.lower()] - {keyword2},
                        )
                        ret.append(
                            AlsoUsedInOtherNamespace(
                                keyword=keyword2,
                                entry=entry,
                                line_number=token.line,
                                column=token.column,
                                hint=hint,
                            )
                        )
        return ret

    @property
    def entries_not_in_namespace_pattern(self) -> List[NotInNamespacePattern]:
        """Return a list of entries not fitting a given namespace pattern."""
        ret = []

        ns_pattern_kwds = self.used_namespace_keywords & self._namespaces.keywords_by_type(PATTERN)

        for kwd in ns_pattern_kwds:
            regex = self._namespaces.keyword_dict[kwd].value
            pattern = re.compile("^" + regex + "$")
            elcs = self._namespace_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if not pattern.search(entry):
                    ret.append(NotInNamespacePattern(keyword=kwd, entry=entry, line_number=line, column=column))
        return ret

    @property
    def entries_not_in_annotation_pattern(self) -> List[NotInAnnotationPattern]:
        """Return a list of entries not fitting a given annotation pattern."""
        ret = []

        anno_pattern_kwds = self.used_annotation_keywords & self._annotations.keywords_by_type(PATTERN)

        for kwd in anno_pattern_kwds:
            regex = self._annotations.keyword_dict[kwd].value
            pattern = re.compile("^" + regex + "$")
            elcs = self._annotation_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if not pattern.search(entry):
                    ret.append(NotInAnnotationPattern(keyword=kwd, entry=entry, line_number=line, column=column))
        return ret

    @property
    def entries_not_in_annotation_list(self) -> List[NotInAnnotationList]:
        """Return a list of entries not in a given annotations."""
        ret = []

        anno_kwd_used_and_as_list = self.used_annotation_keywords & self._annotations.keywords_by_type(LIST)

        for kwd in anno_kwd_used_and_as_list:
            elcs = self._annotation_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if entry not in self._annotations.keyword_dict[kwd].value:
                    ret.append(NotInAnnotationList(keyword=kwd, entry=entry, line_number=line, column=column))
        return ret

    @property
    def entries_not_in_namespace_list(self) -> List[NotInNamespaceList]:
        """Return a list of entries not in a given namespace."""
        ret = []

        ns_kwd_used_and_as_list = self.used_namespace_keywords & self._namespaces.keywords_by_type(LIST)

        for kwd in ns_kwd_used_and_as_list:
            elcs = self._namespace_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if entry not in self._namespaces.keyword_dict[kwd].value:
                    ret.append(NotInNamespaceList(keyword=kwd, entry=entry, line_number=line, column=column))
        return ret

    @property
    def entries_without_namespace(self) -> List[WithoutDefinedNamespace]:
        """Return WithoutDefinedNamespace list."""
        ret = []
        for namespace_keyword in self.namespaces_without_definition:
            elcs = self._namespace_entries.get_entry_line_column_list_by_keyword(namespace_keyword)
            for entry, line, column in elcs:
                ret.append(
                    WithoutDefinedNamespace(
                        keyword=namespace_keyword,
                        entry=entry,
                        line_number=line,
                        column=column,
                    )
                )
        return ret

    @property
    def entries_without_annotation(self) -> List[WithoutDefinedAnnotation]:
        """Return WithoutDefinedNamespace list."""
        ret = []
        for annotation_keyword in self.annotations_without_definition:
            elcs = self._annotation_entries.get_entry_line_column_list_by_keyword(annotation_keyword)
            for entry, line, column in elcs:
                ret.append(
                    WithoutDefinedAnnotation(
                        keyword=annotation_keyword,
                        entry=entry,
                        line_number=line,
                        column=column,
                    )
                )
        return ret

    def update_database(self) -> None:
        """Update namespace and annotation entries in database if not exists by url and keyword."""
        if not (self.__namespace_in_db_updated and self.__annotations_in_db_updated):
            self.__namespace_in_db_updated = self.update_namespaces_in_db()
            self.__annotations_in_db_updated = self.update_annotations_in_db()

    def set_entry_not_in_namespace_list_errors(self):
        pass

    def set_entry_not_in_annotation_list_errors(self):
        pass

    @property
    def entries_not_in_namespace_url(self) -> List[NotInNamespaceUrl]:
        """Return a list of entries not exists in namespaces referenced as URL.

        Returns
        -------
        List[NotInNamespaceUrl]
            Description of returned object.
        """
        entries_not_in_namespace = []

        for keyword in self.used_namespace_keywords:
            namespace = self._namespaces.keyword_dict[keyword]

            if namespace.as_type == URL:
                url = namespace.value
                elc_list = self._namespace_entries.get_entry_line_column_list_by_keyword(keyword)

                names_not_exists = self.namespace_manager.get_entries_not_exists(
                    keyword=keyword,
                    url=url,
                    entry_line_column_list=elc_list,
                )

                for entry, line, column, hint in names_not_exists:
                    error = NotInNamespaceUrl(
                        keyword=keyword,
                        url_or_path=url,
                        entry=entry,
                        line_number=line,
                        column=column,
                        hint=hint,
                    )
                    entries_not_in_namespace.append(error)

        return entries_not_in_namespace

    @property
    def entries_not_in_annotation_url(self) -> List[_Error]:
        """Return a list of entries not in the annotation URL."""
        entries_not_in_annotation = []

        for keyword in self.used_annotation_keywords:
            annotation = self._annotations.keyword_dict[keyword]

            if annotation.as_type == URL:
                url = annotation.value
                elc_list = self._annotation_entries.get_entry_line_column_list_by_keyword(keyword)

                names_not_exists = self.annotation_manager.get_entries_not_exists(
                    keyword=keyword, url=url, entry_line_column_list=elc_list
                )

                for entry, line, column, hint in names_not_exists:
                    error = NotInAnnotationUrl(
                        keyword=keyword,
                        url_or_path=url,
                        entry=entry,
                        line_number=line,
                        column=column,
                        hint=hint,
                    )
                    entries_not_in_annotation.append(error)
        return entries_not_in_annotation

    def update_annotations_in_db(self) -> bool:
        """Update annotation in database if URL and keyword not exists."""
        import_success = True
        for anno in self._annotations.to_update:
            if anno.keyword in self.used_annotation_keywords:
                if not self.annotation_manager.keyword_url_exists(keyword=anno.keyword, url=anno.value):
                    if anno.as_type == URL:
                        logger.info(f"Update db with annotation {anno.keyword}: download from {anno.value}")

                        (
                            successful,
                            error,
                        ) = self.annotation_manager.save_from_url_or_path(
                            keyword=anno.keyword,
                            url_or_path=anno.value,
                            doc_type=anno.as_type,
                        )

                        if not successful:
                            import_success = False
                            error_args = error.args[0].split("\n")
                            string_error = error_args[2] if len(error_args) > 1 else error_args[0]
                            logger.error(
                                f"Annotation {anno.keyword} failed to be added from {anno.value}",
                                exc_info=False,
                            )

                            if "column" in dir(error):  # Indicates it's a Lark error
                                download_error = NotDownloadedFromUrl(
                                    keyword=anno.keyword,
                                    url_or_path=anno.value,
                                    column=error.column,
                                    line=error.line,
                                    hint=f'{error.allowed} error in "{string_error}"',
                                )

                            else:  # It's an HTTPError of some kind
                                download_error = NotDownloadedFromUrl(
                                    keyword=anno.keyword,
                                    url_or_path=anno.value,
                                    column=0,
                                    line=0,
                                    hint=f"{string_error}",
                                )
                            self.notDownloadedFromUrls.append(download_error)

        return import_success

    def update_namespaces_in_db(self) -> bool:
        """Update namespaces in database if URL and keyword does not exist."""
        import_success = True
        for ns in self._namespaces.to_update:
            if ns.keyword in self.used_namespace_keywords:
                if not self.namespace_manager.keyword_url_exists(keyword=ns.keyword, url=ns.value):
                    if ns.as_type == URL:
                        logger.info(f"Update db with namespace {ns.keyword}: download from {ns.value}")

                        (
                            successful,
                            error,
                        ) = self.namespace_manager.save_from_url_or_path(
                            keyword=ns.keyword,
                            url_or_path=ns.value,
                            doc_type=ns.as_type,
                        )

                        if not successful:
                            import_success = False
                            error_args = error.args[0].split("\n")
                            string_error = error_args[2] if len(error_args) > 1 else error_args[0]
                            logger.error(
                                f"Namespace {ns.keyword} failed to be added from {ns.value}",
                                exc_info=False,
                            )

                            if "column" in dir(error):  # Indicates it's a Lark error
                                download_error = NotDownloadedFromUrl(
                                    keyword=ns.keyword,
                                    url_or_path=ns.value,
                                    column=error.column,
                                    line=error.line,
                                    hint=f'{error.allowed} error in "{string_error}"',
                                )

                            else:  # It's an HTTPError of some kind
                                download_error = NotDownloadedFromUrl(
                                    keyword=ns.keyword,
                                    url_or_path=ns.value,
                                    column=0,
                                    line=0,
                                    hint=f"{string_error}",
                                )

                            self.notDownloadedFromUrls.append(download_error)

        return import_success

    @property
    def namespaces_with_multiple_definitions(self):
        """Return all Namespace objects with several definitions.

        This is returned as a dictionary (key:keyword, value: list of Namespace objects).
        """
        ret = defaultdict(list)
        multiple_keyword = [k for k, v in Counter(self._namespaces.keywords).items() if v > 1]
        for ns in self._namespaces:
            if ns.keyword in multiple_keyword:
                ret[ns.keyword].append(ns)
        return dict(ret)

    @property
    def annotations_with_multiple_definitions(self):
        """Return all Annotation objects with several definitions.

        This is returned as a dictionary (key:keyword, value: list of Annotation objects).
        """
        ret = defaultdict(list)
        multiple_keyword = [k for k, v in Counter(self._annotations.keywords).items() if v > 1]
        for anno in self._annotations:
            if anno.keyword in multiple_keyword:
                ret[anno.keyword].append(anno)
        return dict(ret)

    @property
    def namespaces_without_definition(self):
        """Return set of namespace keywords used in statements but not defined with a reference.

        :return set: set of str
        """
        return set(self._namespace_entries.keywords) - set(self._namespaces.keywords)

    @property
    def annotations_without_definition(self):
        """Return a set of annotation keywords not defined with a reference.

        :return set: set of str
        """
        return set(self._annotation_entries.keywords) - set(self._annotations.keywords)

    @property
    def used_namespace_keywords(self) -> Set[str]:
        """Return set of used namespace keywords (with reference and used in statements)."""
        return set(self._namespace_entries.keywords) & set(self._namespaces.keywords)

    @property
    def used_annotation_keywords(self) -> Set[str]:
        """Return set of used namespace keywords."""
        return set(self._annotation_entries.keywords) & set(self._annotations.keywords)

    @property
    def namespace_keywords_in_statements(self):
        """Return all unique namespace keywords used in statements."""
        return self._namespace_entries.keywords

    @property
    def annotation_keywords_in_statements(self):
        """Return all unique annotation keywords used in statements."""
        return self._namespace_entries.keywords

    def get_entries_by_namespace_keyword(self, keyword):
        """Get all entries by namespace keyword.

        :param keyword: namespace keyword
        :return set: all entries in the namespace
        """
        return self._namespace_entries.get_entries_by_keyword(keyword)

    def get_entries_by_annotation_keyword(self, keyword):
        """Get all entries by namespace keyword.

        :param keyword: namespace keyword
        :return set: all entries in the namespace
        """
        return self._annotation_entries.get_entries_by_keyword(keyword)


class Entries:
    """Abstract class representing namespaces and annotations."""

    tokens = defaultdict(dict)
    entries = defaultdict(set)

    def get_entry_line_column_list_by_keyword(self, keyword: str) -> Generator[str, int, int]:
        """Get generator of tuple(entry, line, column) by keyword.

        Parameters
        ----------
        keyword: str
            Description of parameter `keyword: str`.

        Returns
        -------
        Generator
            Generator of tuple(entry: str, line: int, column: int).
        """
        for entry, tokens in self.tokens[keyword].items():
            for token in tokens:
                yield entry, token.line, token.column

    @property
    def keywords(self):
        """Return a list of unique keywords used in SETs."""
        return self.entries.keys()

    def get_entries_by_keyword(self, keyword: str) -> Set:
        """Get entries by keyword.

        :param str keyword: keyword to retrieve from dict
        """
        return self.entries.get(keyword, set())

    def get_tokens_by_keyword(self, keyword: str) -> Dict:
        """Get tokens by keyword.

        :param str keyword: keyword to retrieve from dict
        """
        return self.entries.get(keyword, set())

    def __str__(self):
        """String representation of object."""
        return str(dict(self.tokens))


class NamespaceEntries(Entries):
    """Namespace subclass of Entries."""

    def __init__(self):
        """Init."""
        self.entries = defaultdict(set)
        self.tokens = defaultdict(dict)

    def set_namespace_entry(self, keyword, entry, token):
        """Set namespace,  entry and lark.lexer.Token.

        :param str keyword: namespace
        :param str entry: entry
        :param lark.lexer.Token token: Token object from lark library
        """
        if isinstance(token, Token):
            self.entries[keyword] |= {entry}
            if keyword in self.tokens and entry in self.tokens[keyword]:
                self.tokens[keyword][entry].append(token)
            else:
                self.tokens[keyword][entry] = [token]
        else:
            raise "Argument token is type {} not {}".format(type(token), "lark.lexer.Token")


class AnnotationEntries(Entries):
    """Annotation subclass of Entries."""

    def __init__(self):
        """Init."""
        self.entries = defaultdict(set)
        self.tokens = defaultdict(dict)

    def set_annotation_entry(self, keyword: str, entry, token):
        """Set annotation,  entry and lark.lexer.Token.

        :param str keyword: annotation
        :param entry: entry
        :param lark.lexer.Token token: Token object from lark library
        """
        if isinstance(token, Token):
            self.entries[keyword] |= {entry}
            if keyword in self.tokens and entry in self.tokens[keyword]:
                self.tokens[keyword][entry].append(token)
            else:
                self.tokens[keyword][entry] = [token]
        else:
            raise "argument token is type {} not {}".format(type(token), "lark.lexer.Token")


class NsAnsBase:
    """Parent class for class Namespace and Annotation."""

    def __init__(self, obj_class):
        """Init."""
        self.__objs = []
        self.class_ = obj_class

    def add(self, as_type: str, keyword: str, value: str):
        """Add obj to list of objs.

        :param str as_type: allowed keywords 'file', 'url' or 'list'
        :param str keyword: keyword used in object
        :param str value: value of object
        :return:
        """
        obj = self.class_(as_type, keyword, value)
        self.__objs.append(obj)

    @property
    def type_dict(self) -> DefaultDict:
        """Convert to list of dictionaries."""
        ret = defaultdict(list)
        [ret[obj.as_type].append(obj) for obj in self]
        return ret

    def by_type(self, as_type: str):
        """Return list of Namespace objects by 'list', 'url' or 'file'."""
        if as_type not in ALLOWED_TYPES:
            raise "{} not in allowed types {}".format(as_type, ALLOWED_TYPES)
        return [obj for obj in self if obj.as_type == as_type]

    def keywords_by_type(self, as_type: str) -> Set[str]:
        """Return a set of keywords by Namespace type 'list', 'url' or 'file'."""
        if as_type not in ALLOWED_TYPES:
            raise "{} not in allowed types {}".format(as_type, ALLOWED_TYPES)
        return set([obj.keyword for obj in self if obj.as_type == as_type])

    @property
    def keyword_dict(self) -> Dict:
        """Return a dictionary of key=keyword, value: Namespace or Annotation object."""
        ret = dict()
        for obj in self:
            ret[obj.keyword] = obj
        return ret

    @property
    def keywords(self) -> List[str]:
        """Return all keywords."""
        return [obj.keyword for obj in self.__objs]

    @property
    def to_update(self) -> List:
        """Return a list of all Namespace or Annotation (NS_or_Anno) objects with URL or file path.

        :return list: list of all Namespace or Annotation (NS_or_Anno) objects with URL or file path
        """
        return self.type_dict[URL]

    def __iter__(self):
        """Return a generator of objects (Namespace or Annotation)."""
        for obj in self.__objs:
            yield obj


class Namespaces(NsAnsBase):
    """Namespace child class."""

    def __init__(self):
        """init."""
        super(Namespaces, self).__init__(obj_class=Namespace)


class Annotations(NsAnsBase):
    """Annotation child class."""

    def __init__(self):
        """init."""
        super(Annotations, self).__init__(obj_class=Annotation)


class Namespace:
    """Namespace class to represent BEL statement namespaces."""

    def __init__(self, as_type, keyword, value):
        """Namespace init."""
        self.as_type = as_type
        self.keyword = keyword
        self.value = value

    def to_dict(self):
        """Convert class values to dictionary."""
        return {"as_type": self.as_type, "keyword": self.keyword, "value": self.value}

    def __unicode__(self):
        return "Namespace:" + str(self.to_dict())

    def __str__(self):
        return self.__unicode__()


class Annotation:
    """Annotation class to represent BEL statement annotations."""

    def __init__(self, as_type, keyword, value):
        """Annotation init."""
        self.as_type = as_type
        self.keyword = keyword
        self.value = value

    def to_dict(self):
        """Convert class values to dictionary."""
        return {"as_type": self.as_type, "keyword": self.keyword, "value": self.value}

    def __unicode__(self):
        return "Annotation" + str(self.to_dict())

    def __str__(self):
        return self.__unicode__()
