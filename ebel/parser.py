"""This module allows to parse BEL scripts."""

import re
import json
import codecs
import logging

from copy import copy
from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from pandas import DataFrame
from typing import List, Any, Iterable
from collections import defaultdict, OrderedDict
from lark.exceptions import UnexpectedInput, UnexpectedToken

from ebel.transformers import _BelTransformer
from ebel.errors import BelSyntaxError

from ebel.constants import GRAMMAR_START_LINE, GRAMMAR_BEL_PATH

# TODO: check all strings if they can be stored in constants

# Following trees (rules in grammar) have one 1 value. This list is use in creation of json file
trees_with_one_value = ("document_name", "document_version", "document_description", "document_copyright",
                        "document_authors", "document_licences", "document_contact_info", "keyword", "anno_keyword",
                        "c_type", "c_title", "c_ref", "evidence", "frag_range", "frag_descriptor", "hgvs",
                        "gene_fusion_range", "rna_fusion_range", "protein_fusion_range", "document_keywords")


# Exclude this token types if json of created
exclude_token_types = ('OB', 'CB', 'QM', 'COLON', 'COMMA', 'OCB', 'CCB')

logger = logging.getLogger(__name__)


def load_grammar(grammar_path):
    """Return eBNF grammar in lark style.

    Parameters
    ----------
    grammar_path : str
        path to eBNF grammar in lark style.

    Returns
    -------
    string
        eBNF grammar in lark style.

    """
    # FIXME: something to do here
    logger.info("load grammar {}".format(grammar_path))
    with codecs.open(grammar_path, 'r', encoding="utf-8") as fd_grammar:
        grammar = fd_grammar.read()
    fd_grammar.close()
    return grammar


def first_token_value(tree: Tree, subtree_name: str) -> str:
    """Get the first token value of Lark tree with subtree name.

    Parameters
    ----------
    tree : type
        Description of parameter `tree`.
    subtree_name : type
        Description of parameter `subtree_name`.

    Returns
    -------
    type
        Description of returned object.

    """
    # TODO: Get rid of this method by using a Transformer? Is this possible?

    for subtree in tree.iter_subtrees():
        if subtree.data == subtree_name:
            return [node.value for node in subtree.children if isinstance(node, Token)][0]


def first_real_token_value(tokens: List[Token], purge: bool) -> str:
    """Return value of first token not excluded by `exclude_token_types`.

    Parameters
    ----------
    tokens: List[Token]
        list of lark.lexer.Token
    purge: bool
        set if value will be purged.

    Returns
    -------
    str
        String value from first 'real' token.
    """
    t = [token for token in tokens if token.type not in exclude_token_types][0]
    if purge:
        t.value = re.sub(r"\s{2,}", " ", t.value.replace("\\\n", "").strip())
    return t.value


def camel_case(name: str) -> str:
    """Camel case a string."""
    first, *rest = name.split('_')
    return first + ''.join(word.capitalize() for word in rest)


def tupleit(lst: list) -> tuple:
    """Cast all lists in nested list to tuple."""
    return tuple(map(tupleit, lst)) if isinstance(lst, list) else lst


def to_tuple(py_obj: Any) -> tuple:
    """Create from nested python object a nested tuple where all obj are casted to tuples."""
    lst = []

    # check if instance is dict, str, Iterable or something different
    if isinstance(py_obj, dict):

        for k, v in py_obj.items():
            lst.append((k, to_tuple(v)))

    elif not isinstance(py_obj, str) and isinstance(py_obj, Iterable):
        lst.append(tuple(to_tuple(x) for x in py_obj))

    else:
        return py_obj

    return tuple(lst)


def get_values(childs: list, num_expected_values=0) -> list:
    """Get values from token list and exclude exclude_token_types.

    Parameters
    ----------
    childs : list
        token list.
    num_expected_values : type
        Number of expeted values.

    Returns
    -------
    list
        List of token values.

    """
    values = [x.value for x in childs if x.type not in exclude_token_types]
    if num_expected_values:
        values = values + [''] * (num_expected_values - len(values))
    return values


def append_to_list(py_tree, rule_name, value):
    """Append value to py_tree.

    Append value to py_tree list entry if list entry is dict with rule_name;
    otherwise create a new dict entry with rule_name as key and value as avlue.

    Parameters
    ----------
    py_tree : list
        python object.
    rule_name : str
        rule name from grammar.
    value : any
        any type from Lark.Tree.

    """
    rule_name_index = -1
    rule_name_exists = False
    for i, x in enumerate(py_tree):
        if isinstance(x, dict) and list(x.keys()) == [rule_name]:
            rule_name_index = i
            rule_name_exists = True

    if rule_name_exists:
        if value not in py_tree[rule_name_index][rule_name]:
            py_tree[rule_name_index][rule_name] = sorted(py_tree[rule_name_index][rule_name] + [value])
    else:
        py_tree.append({rule_name: [value]})


def bel_to_json(tree) -> str:
    """Return BEL script as JSON string.

    Parameters
    ----------
    tree: OrderedDict
        Parsed BEL relations represented as a tree, output from Lark.

    Returns
    -------
    str
        BEL tree as a JSON string.
    """
    return json.dumps(tree, indent=1)


class Pattern:
    """Pattern in BEL scripts."""

    def __init__(self):
        """Initialize Pattern with dicttionaries for patterns and errors.

        Returns
        -------
        type
            Description of returned object.
        """
        self.__pattern = {}
        self.errors = defaultdict(list)

    def set_pattern(self, namespace, pattern):
        """Set namespace as regular expression pattern.

        Parameters
        ----------
        namespace : str
            `namespace` use in BEL script.
        pattern : str
            `pattern` as regular expression used in BEL statements.

        Returns
        -------
        type
            Description of returned object.
        """
        self.__pattern[namespace] = pattern

    def check_entry(self, namespace, entry, line, column):
        """Short summary.

        Parameters
        ----------
        namespace : str
            Description of parameter `namespace`.
        entry : str
            Description of parameter `entry`.
        line : int
            Description of parameter `line`.
        column : int
            Description of parameter `column`.

        Returns
        -------
        type
            Description of returned object.
        """
        # TODO: check if this follows error conventions > see Error classes
        if not re.search(self.__pattern[namespace], entry):
            self.errors[namespace].append((entry, line, column))

    @property
    def namespaces(self):
        """Return all namespace for patterns.

        Returns
        -------
        list
            return a list of namespace linked to patterns.
        """
        return self.__pattern.keys()


class _BELParser:
    """class manage the parsing with python lib lark-parser."""

    @staticmethod
    def check_bel_script_line_by_line(bel_script_path: str, bel_version: str) -> List[str]:
        """Check BEL script line by line.

        Parameters
        ----------
        bel_script_path : str
            Path to BEL file.
        bel_version : str
            BEL grammar version.

        Returns
        -------
        List[str]
            List of errors found in BEL script.
        """
        logger.info("Start syntax check for {} line by line with grammar BEL {}".format(
            bel_script_path, bel_version))
        errors = []

        grammar = load_grammar(GRAMMAR_BEL_PATH[str(bel_version)])

        parser = Lark(grammar,
                      start=GRAMMAR_START_LINE,
                      parser='lalr',
                      lexer="contextual")

        cached_line = ""
        with codecs.open(bel_script_path, 'r', encoding="utf-8") as fd:

            lines = fd.readlines()
            if not re.search('(\n|\r|\r\n)$', lines[-1]):
                lines[-1] += "\n"

            num_and_lines = OrderedDict(enumerate(lines, 1))

            for line_num, line in copy(num_and_lines).items():

                if re.search(r'\\\s*(\n|\r|\r\n)$', line):

                    num_and_lines[line_num + 1] = num_and_lines[line_num].strip()[:-1] + " " + \
                        num_and_lines[line_num + 1]
                    del num_and_lines[line_num]

            for line_number, line in num_and_lines.items():
                try:
                    if line.endswith("\\n"):
                        cached_line = line
                        continue

                    elif cached_line:

                        if not line.endswith("\\n"):
                            try:
                                cached_line += line
                                parser.parse(cached_line)

                            except (UnexpectedInput, UnexpectedToken) as exc1:
                                errors.append(BelSyntaxError(exc1, line_number, cached_line.strip()))

                            cached_line = ""
                            continue

                        else:
                            # TODO: check if last line will be parsed?
                            cached_line += line
                            continue

                    parser.parse(line)

                except (UnexpectedInput, UnexpectedToken) as exc2:
                    errors.append(BelSyntaxError(exc2, line_number, line))

        return errors

    def check_bel_script(self, bel_script_path: str,
                         bel_version: str,
                         force_new_db: bool = False) -> dict:
        """Check file with BEL script for syntax correctness.

        Parameters
        ----------
        bel_script_path : str
            Path to BEL script.
        bel_version : str
            BEL version 1 or 2.
        force_new_db : bool
            Force to create a new database if already exists.

        Returns
        -------
        dict
            Dictionary with results.
        """
        grammar = load_grammar(GRAMMAR_BEL_PATH[bel_version])

        if bel_version.startswith("2"):  # TODO change this hardcoded value
            transformer = _BelTransformer()
        else:
            logger.error(f"Transformer for version {bel_version} not implemented", exc_info=True)
            raise

        parser = Lark(
            grammar,
            start='script',
            parser='lalr',
            lexer="contextual",
            transformer=transformer
        )

        with codecs.open(bel_script_path, 'r', encoding="utf-8") as fd:
            bel_content = fd.read() + "\n"
        fd.close()

        tree = None
        warnings = None

        try:
            tree = parser.parse(bel_content)
            errors = transformer.cache.errors
            warnings = transformer.cache.warnings

        except UnexpectedInput as exc:
            logger.info("UnexpectedInput exception in check_bel_script: %s" % exc)
            errors = self.check_bel_script_line_by_line(bel_script_path, bel_version)

        return {'errors': errors,
                'tree': tree,
                'warnings': warnings}


def write_error_report(data_frame: DataFrame, file_path: str) -> None:
    """Short summary.

    Parameters
    ----------
    data_frame : type
        Description of parameter `data_frame`.
    file_path : str
        Description of parameter `file_path`.

    Returns
    -------
    type
        Description of returned object.
    """
    if file_path.endswith('.xlsx'):
        data_frame.to_excel(file_path)
    else:
        data_frame.to_csv(file_path)


def write_warning_report(data_frame: DataFrame, file_path: str) -> None:
    """Short summary.

    Parameters
    ----------
    data_frame : DataFrame
        DataFrame with validation results.
    file_path : str
        file path to error report.

    """
    if file_path.endswith('.xlsx'):
        data_frame.to_excel(file_path)
    else:
        data_frame.to_csv(file_path)


def check_bel_script_line_by_line(bel_script_path, error_report_file_path, bel_version):
    """Check statements in file or string for correct.

    result['trees'][line_number] = {'statement': statement, 'tree': tree}
    result['errors'][line_number] = {'statement': statement, 'error': ex}

    # can be used as comments
    empty lines will be skipped
    every statement should be in a new line

    :param str bel_script_path: path to BEL script
    :param str error_report_file_path: path to report
    :param str bel_version: BEL version
    :return: dict
    """
    parser = _BELParser()
    data_frame = parser.check_bel_script_line_by_line(bel_script_path, bel_version)
    if error_report_file_path:
        write_error_report(data_frame=data_frame, file_path=error_report_file_path)
    else:
        return data_frame


def check_bel_script(bel_script_path,
                     bel_version,
                     force_new_db=False) -> dict:
    """Check BEL script.

    Parameters
    ----------
    bel_script_path : str
        Description of parameter `bel_script_path`.
    bel_version : str
        BEL syntax version.
    force_new_db : bool
        if true, force to create new database

    Returns
    -------
    type
        Description of returned object.
    """
    bel_parser = _BELParser()
    result = bel_parser.check_bel_script(
        bel_script_path=bel_script_path,
        force_new_db=force_new_db,
        bel_version=bel_version
    )

    return result
