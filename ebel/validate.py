"""Collect of methods used for validating a BEL file."""
import os
import re
import csv
import difflib
import logging

from typing import Iterable, Union, Optional
from textwrap import fill
from pathlib import Path

import numpy as np
import pandas as pd

import ebel.database
from ebel.errors import BelSyntaxError
from ebel.parser import check_bel_script_line_by_line, check_bel_script, bel_to_json


logger = logging.getLogger(__name__)


def validate_bel_file(bel_script_path: Union[str, Path],
                      force_new_db: bool = False,
                      line_by_line: bool = False,
                      reports: Union[Iterable[str], str] = None,
                      bel_version: str = '2_1',
                      tree: bool = False,
                      sqlalchemy_connection_str: str = None,
                      json_file: bool = True,
                      force_json: bool = False,):
    """Validate BEL script for correct syntax following eBNF grammar.

    Parameters
    ----------
    bel_script_path: str
        Path to BEL file or directory contaiing BEL files.
    force_new_db: bool
        Delete current database of namespaces/values and generate a new one. Defaults to False.
    line_by_line: bool
        TODO: Write this.
    reports: Iterable[str] or str
        List of file paths to write reports to. Multiple formats of the report can be generated at once. Acceptable
        formats include: CSV, TSV, TXT, XLS, XLSX, JSON, HTML, MD
    bel_version: {'1', '2', '2_1'}
        Which BEL grammar version should be used for validating the BEL file. Current available are 1.0, 2.0, and 2.1.
        Defaults to the most recent version.
    tree: bool
        Generates a tree of relationships derived from the BEL file. Defaults to False.
    sqlalchemy_connection_str: str
        Path to SQLLite database to be used for storing/looking up used namespaces and values. If None given, it uses
        the generated e(BE:L) database (default).
    json_file: bool
        If True, generates a JSON file that can be used for importing BEL relationships into an e(BE:L) generated
        OrientDB database. Only creates the JSON file when there are no grammar or syntax errors. Defaults to True.
    force_json: bool
        If True, will create an importable JSON file even if there are namespace/value errors. Defaults to False.

    Returns
    -------
    dict
        Dictionary of file paths and results for each BEL file processed.

    Examples
    --------
    Task: Validate BEL script `my.bel` for BEL syntax 2.0, create error
    reports in Markdown and JSON format. In case of no errors create a JSON file
    for the import of BEL network into Cytoscape:

    > ebel validate my.bel -v 2 -r error_report.md,error_report.json

    """
    validation_results = dict()

    if line_by_line:
        # TODO: This is perhaps not working
        result = check_bel_script_line_by_line(bel_script_path,
                                               error_report_file_path=reports,
                                               bel_version=bel_version)

        if reports:
            logger.info("Wrote report to %s\n" % reports)
        else:
            logger.info("\n".join([x.to_string() for x in result]) + "\n")

    else:
        if sqlalchemy_connection_str:
            ebel.database.set_connection(sqlalchemy_connection_str)

        bel_files = _create_list_bel_files(bel_path=bel_script_path)
        validation_results['bel_files_checked'] = bel_files

        for bel_file in bel_files:
            # Create dict to be filled for individual BEL files.
            validation_results[bel_file] = dict()

            logger.info(f"Processing {bel_file}")
            result = check_bel_script(
                bel_script_path=bel_file,
                force_new_db=force_new_db,
                bel_version=bel_version,
            )

            if json_file:
                if result["errors"]:
                    if force_json:  # Check for syntax errors
                        bel_syntax_error_present = result['errors'] and any(
                            [type(error_type) == BelSyntaxError for error_type in result["errors"]]
                        )
                        if bel_syntax_error_present:
                            logger.error("Cannot force JSON file due to syntax errors. Please check the BEL file.")

                        else:
                            json_file = _write_odb_json(bel_path=bel_file, results=result, bel_version=bel_version)
                            validation_results[bel_file]['json'] = json_file

                    else:
                        logger.error("Unable to create JSON file due to grammar/syntax errors in BEL file")

                else:  # No errors so everything is fine
                    json_file = _write_odb_json(bel_path=bel_file, results=result, bel_version=bel_version)
                    validation_results[bel_file]['json'] = json_file

            if tree:
                if result['errors']:
                    logger.error("Tree can not be printed because errors still exists\n")

                else:
                    logger.debug(result['tree'])
                    validation_results[bel_file]['tree'] = result['tree']

                if result['warnings'] and reports:
                    report_paths = _write_report(reports, result, report_type='warnings')
                    validation_results[bel_file]['reports'] = report_paths

            elif result['errors']:

                if not reports:
                    logger.info('\n'.join([x.to_string() for x in result['errors']]) + "\n")

                else:
                    _write_report(reports, result, report_type='errors')


def repair_bel_file(bel_script_path: str, new_file_path: Optional[str] = None):
    """Repair a BEL document.

    Parameters
    ----------
    bel_script_path : str
        Path to the BEL file.
    new_file_path : str (optional)
        Export repaired version of file to new path.
    """
    # if evidence:
    # regular expression for missing continuous line (\ at the end of line)
    with open(bel_script_path, "r", encoding="utf-8") as belfile:
        content = belfile.read()

    new_content = content

    for regex_pattern in re.findall(r'\n((SET\s+(DOCUMENT\s+Description|Evidence|SupportingText|Support)'
                                    r'\s*=\s*)"(((?<=\\)"|[^"])+)"\s*\n*)',
                                    content):
        if regex_pattern[2].startswith("DOCUMENT"):
            new_prefix = "SET DOCUMENT Description = "
        else:
            new_prefix = "SET Support = "

        new_evidence_text = re.sub(r"(\\?[\r\n]+)|\\ ", " ", regex_pattern[3].strip())
        new_evidence_text = re.sub(r"\s{2,}", " ", new_evidence_text)
        new_evidence_text = re.sub(r'(\\)(\w)', r'\g<2>', new_evidence_text)
        new_evidence_text = fill(new_evidence_text, break_long_words=False).replace("\n", " \\\n")
        new_evidence = new_prefix + '"' + new_evidence_text + '"\n\n'

        new_content = new_content.replace(regex_pattern[0], new_evidence)

    if content != new_content:
        if new_file_path:
            with open(new_file_path + ".diff2repaired", "w") as new_file:
                new_file.write('\n'.join(list(difflib.ndiff(content.split("\n"), new_content.split("\n")))))

        else:
            with open(bel_script_path, "w") as output_file:
                output_file.write(new_content)


def _write_odb_json(bel_path: str, results: dict, bel_version: str) -> str:
    json_path = bel_path + ".json"
    if int(bel_version[0]) > 1:
        json_tree = bel_to_json(results['tree'])
        open(json_path, "w").write(json_tree)

    return json_path


def _create_list_bel_files(bel_path: str) -> list:
    """Export all BEL files in directory as list. If single file is passed, returns a list with that path."""
    if os.path.isdir(bel_path):
        bel_files = []
        for file in os.listdir(bel_path):
            if file.endswith(".bel"):
                bel_file_path = os.path.join(bel_path, file)
                bel_files.append(bel_file_path)

    else:
        bel_files = [bel_path]

    return bel_files


def _write_report(reports: Union[Iterable[str], str], result: dict, report_type: str) -> list:
    """Write report in different types depending on the file name suffix in reports.

    Parameters
    ----------
    reports : Iterable[str] or str
        List of report formats or comma separated list of report file names.
    result : dict
        return value of check_bel_script methode.
    report_type : str
        `report_type` could be 'warnings' or 'errors'.

    Returns
    -------
    list
        List of file paths for the reports written.

    """
    # TODO: report_type options should be constants
    errors_or_warns_as_list_of_dicts = [x.to_dict() for x in result[report_type]]

    columns = [report_type[:-1] + "_class", "url", "keyword", "entry", "line_number", "column", "hint"]
    df = pd.DataFrame(data=errors_or_warns_as_list_of_dicts, columns=columns)
    df.index += 1

    if isinstance(reports, str):
        reports = reports.split(",")

    for report in reports:
        try:
            if report.endswith('.csv'):
                df.to_csv(report, index=False)

            if report.endswith('.xls'):
                try:
                    df.to_excel(report, index=False)

                except ValueError:
                    logger.warning("Max Excel sheet size exceeded. Writing to CSV instead.")
                    df.to_csv(report, index=False)

            if report.endswith('.xlsx'):
                try:
                    df.to_excel(report, engine='xlsxwriter', index=False)

                except ValueError:
                    logger.warning("Max Excel sheet size exceeded. Writing to CSV instead.")
                    df.to_csv(report, index=False)

            if report.endswith('.tsv'):
                df.to_csv(report, sep='\t', index=False)

            if report.endswith('.json'):
                df.to_json(report, index=False)

            if report.endswith('.txt'):
                open(report, "w").write(df.to_string(index=False))

            if report.endswith('.html'):
                df.to_html(report, index=False)

            if report.endswith('.md'):
                cols = df.columns
                df2 = pd.DataFrame([['---', ] * len(cols)], columns=cols)

                if df.hint.dtype == np.str:
                    df.hint = df.hint.str.replace(r'\|', '&#124;')

                if df.entry.dtype == np.str:
                    df.entry = df.entry.str.replace(r'\|', '&#124;')

                df.url = [("[url](" + str(x) + ")" if not pd.isna(x) else '') for x in df.url]
                url_template = "[%s](" + report.split(".bel.")[0] + ".bel?expanded=true&viewer=simple#L%s)"
                df.line_number = [url_template % (x, x) for x in df.line_number]
                df3 = pd.concat([df2, df])
                df3.to_csv(report, sep="|", index=False, quoting=csv.QUOTE_NONE, escapechar="\\")

        except PermissionError:
            logger.error("Previous version of error report is still open and cannot be overwritten. Unable to update.")

    return reports
