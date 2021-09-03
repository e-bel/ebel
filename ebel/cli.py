"""Command line interface to e(BE:L)."""

import difflib
import logging
import re
import sys
from textwrap import fill

import click

import ebel.database
from ebel import Bel, web
from ebel.manager.orientdb.constants import DRUGBANK
from ebel.manager.orientdb.odb_meta import Graph
from ebel.validate import validate_bel_file

logger = logging.getLogger(__name__)


@click.group(help="BEL test framework Command Line Utilities on {}".format(sys.executable))
@click.version_option()
def main():
    """Entry method."""
    pass


# TODO(@ceb): Implement by default "keep database" and new database as option #prio1
# TODO(@ceb): SQLAlchemy connection string #prio1
@main.command()
@click.argument('bel_script_path')
@click.option('-f', '--force_new_db', is_flag=True, default=False, help='force recreation of new database')
@click.option('-l', '--line_by_line', is_flag=True, default=False, help='check script line by line')
@click.option('-r', '--reports', default=None,
              help='path(s) to report file(s) seperated by comma with suffix (.md, .txt, .csv, .tsv, .json, .html)')
@click.option('-v', '--bel_version', default="2_1", help='stores a report in a file')
@click.option('-t', '--tree', is_flag=True, default=False, help='shows tree')
# TODO: Implement new Cytoscape export file
# @click.option('-c', '--cytoscape', is_flag=True, default=False, help='creates cytoscape file')
@click.option('-s', '--sqlalchemy_connection_str', default=None, help="SQLAlchmy connection string")
@click.option('-j', '--json_file', is_flag=True, help="Create json file")
def validate(bel_script_path: str, force_new_db: bool, line_by_line: bool, reports: str,
             bel_version: str, tree: bool, sqlalchemy_connection_str: str,
             json_file: bool):
    """Validate a BEL file using the defined grammar."""
    validate_bel_file(bel_script_path=bel_script_path, force_new_db=force_new_db, line_by_line=line_by_line,
                      reports=reports, bel_version=bel_version, tree=tree,
                      sqlalchemy_connection_str=sqlalchemy_connection_str, json_file=json_file)


@main.command()
@click.argument('bel_script_path')
@click.option('-n', '--new_file_path', default=None,
              help='path to file, if you want create a new file instead of overwrite')
def repair(bel_script_path, new_file_path):
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
    with open(bel_script_path, "r") as belfile:
        content = belfile.read()

    new_content = content

    for regex_pattern in re.findall(r'\n((SET\s+(DOCUMENT\s+Description|Evidence|SupportingText)'
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


@main.command()
@click.argument('json_file_path')
@click.option('-e', '--extend', is_flag=True, default=True, help='Flag to disable "extension" during import')
@click.option('-g', '--p2g', is_flag=True, default=True, help='Flag to disable "protein2gene" during import')
@click.option('-s', '--skip_drugbank', is_flag=True, default=False, help='Flag to disable DrugBank')
@click.option('-i', '--include_subfolders', is_flag=True, default=False, help='Flag to enable directory walking')
@click.option('--drugbank_user', default=None, help='Valid username for DrugBank')
@click.option('--drugbank_password', default=None, help='Valid username for DrugBank')
@click.option('-n', '--odb_name', default=None, help='OrientDB database name')
@click.option('-u', '--odb_user', default=None, help='OrientDB user (with admin rights)')
@click.option('-p', '--odb_password', default=None, help='OrientDB user (with admin rights) password')
@click.option('-h', '--odb_server', default=None, help='OrientDB server name or URI')
@click.option('-o', '--odb_port', default=None, help='OrientDB server port')
@click.option('--odb_user_reader', default=None, help=' OrientDB user with only read rights')
@click.option('--odb_user_reader_password', default=None, help='OrientDB user with only read rights password')
@click.option('--odb_root_password', default=None, help='OrientDB root user password (only during database setup)')
@click.option('--kegg_species', default='hsa,rno,mmu', help='KEGG species')
@click.option('--sqlalchemy_connection_string', help='schema is user:password@server/database')
@click.option('--snp_related_traits', help='key of SNP related traits in GWAS catalog')
@click.option('--drugbank_user', help='Drugbank user')
@click.option('--drugbank_password', help='DrugBank password')
@click.option('--gwas_catalog_disease_keyword', help='one or several keywords seperated by comma for GWAS '
                                                     'catalog diseases')
def import_json(json_file_path: str,
                extend: bool,
                p2g: bool,
                skip_drugbank: bool,
                drugbank_user: str,
                drugbank_password: str,
                include_subfolders: bool,
                odb_name: str,
                odb_user: str,
                odb_password: str,
                odb_server: str,
                odb_port: str,
                odb_user_reader: str,
                odb_user_reader_password: str,
                odb_root_password: str,
                kegg_species: str,
                sqlalchemy_connection_string: str,
                snp_related_traits: str,
                gwas_catalog_disease_keyword: str):
    """Import JSON into OrientDB.

    Parameters
    ----------
    json_file_path : str
        Path to a BEL JSON file, list of BEL JSON files (separated by ","), or a directory containing BEL JSON files.
    extend : bool
        Boolean flag to disable network extension by e(BE:L)
    p2g : bool
        Boolean flag to disable adding genes and RNA to proteins in network
    skip_drugbank : bool
        Boolean flag to disable DrugBank enrichment. Useful if you do not have valid DrugBank credentials
    drugbank_user: str (optional)
        DrugBank user name.
    drugbank_password: str (optional)
        DrugBank password.
    include_subfolders: bool (optional)
        Boolean flag to enable walking through subdirectories during import.
    odb_name: str
        OrientDB database name
    odb_user:
        OrientDB user (with admin rights)
    odb_password:
        OrientDB user (with admin rights) password
    odb_server:
        OrientDB server name or URI
    odb_port:
        OrientDB server port
    odb_user_reader:
        OrientDB user with only read rights
    odb_user_reader_password:
        OrientDB user with only read rights password
    odb_root_password:
        OrientDB root user password (only first database setup needed)
    kegg_species:
        KEGG species 3-4 letter code https://www.genome.jp/kegg/catalog/org_list4.html
    sqlalchemy_connection_string:
        SQL Alchemy connection string schema: user:passwd@server/database
    snp_related_traits:
        SNP related traits
    gwas_catalog_disease_keyword:
        GWAS Catalog disease keyword(s)

    Returns
    -------
    type
        returns True if imported.
    """
    # if one of the parameters is not None it will overwrite the default values from the configfile
    Graph.set_configuration(name=odb_name,
                            user=odb_user,
                            password=odb_password,
                            server=odb_server,
                            port=odb_port,
                            user_reader=odb_user_reader,
                            user_reader_password=odb_user_reader_password,
                            root_password=odb_root_password,
                            kegg_species=kegg_species,
                            sqlalchemy_connection_string=sqlalchemy_connection_string,
                            snp_related_traits=snp_related_traits,
                            drugbank_user=drugbank_user,
                            drugbank_password=drugbank_password,
                            gwas_catalog_disease_keyword=gwas_catalog_disease_keyword)

    bel = Bel()
    if "," in json_file_path:
        json_file_path = json_file_path.split()

    bel.import_json(input_path=json_file_path,
                    extend_graph=extend,
                    update_from_protein2gene=p2g,
                    skip_drugbank=skip_drugbank,
                    drugbank_user=drugbank_user,
                    drugbank_password=drugbank_password,
                    include_subfolders=include_subfolders)


@main.command()
@click.option('-s', '--skip', default=[], help='Comma-separated list of databases to skip during enrichment')
@click.option('-i', '--include', default=[], help='Comma-separated list of databases to include during enrichment')
@click.option('--skip_drugbank', is_flag=True, default=False, help='Flag to disable DrugBank')
@click.option('--drugbank_user', default=None, help='Valid username for DrugBank')
@click.option('--drugbank_password', default=None, help='Valid username for DrugBank')
@click.option('-n', '--odb_name', default=None, help='OrientDB database name')
@click.option('-u', '--odb_user', default=None, help='OrientDB user (with admin rights)')
@click.option('-p', '--odb_password', default=None, help='OrientDB user (with admin rights) password')
@click.option('-h', '--odb_server', default=None, help='OrientDB server name or URI')
@click.option('-o', '--odb_port', default=None, help='OrientDB server port')
@click.option('--odb_user_reader', default=None, help=' OrientDB user with only read rights')
@click.option('--odb_user_reader_password', default=None, help='OrientDB user with only read rights password')
@click.option('--odb_root_password', default=None, help='OrientDB root user password (only during database setup)')
@click.option('--kegg_species', default='hsa,rno,mmu', help='KEGG species')
@click.option('--sqlalchemy_connection_string', help='schema is user:password@server/database')
@click.option('--snp_related_traits', help='key of SNP related traits in GWAS catalog')
@click.option('--gwas_catalog_disease_keyword', help='one or several keywords seperated by comma for GWAS '
                                                     'catalog diseases')
def enrich(skip: str,
           include: str,
           skip_drugbank: bool,
           drugbank_user: str,
           drugbank_password: str,
           odb_name: str,
           odb_user: str,
           odb_password: str,
           odb_server: str,
           odb_port: str,
           odb_user_reader: str,
           odb_user_reader_password: str,
           odb_root_password: str,
           kegg_species: str,
           sqlalchemy_connection_string: str,
           snp_related_traits: str,
           gwas_catalog_disease_keyword: str):
    """Trigger the enrichment step for a database.

    Parameters
    ----------
    skip : str
        Comma-separated list of databases to skip during enrichment.
    include : str
        Comma-separated list of databases to include during enrichment.
    skip_drugbank : bool
        Boolean flag to disable DrugBank enrichment. Useful if you do not have valid DrugBank credentials
    drugbank_user: str (optional)
        DrugBank user name.
    drugbank_password: str (optional)
        DrugBank password.
    odb_name: str
        OrientDB database name
    odb_user:
        OrientDB user (with admin rights)
    odb_password:
        OrientDB user (with admin rights) password
    odb_server:
        OrientDB server name or URI
    odb_port:
        OrientDB server port
    odb_user_reader:
        OrientDB user with only read rights
    odb_user_reader_password:
        OrientDB user with only read rights password
    odb_root_password:
        OrientDB root user password (only first database setup needed)
    kegg_species:
        KEGG species 3-4 letter code https://www.genome.jp/kegg/catalog/org_list4.html
    sqlalchemy_connection_string:
        SQL Alchemy connection string schema: user:passwd@server/database
    snp_related_traits:
        SNP related traits
    gwas_catalog_disease_keyword:
        GWAS Catalog disease keyword(s)
    """
    Graph.set_configuration(name=odb_name,
                            user=odb_user,
                            password=odb_password,
                            server=odb_server,
                            port=odb_port,
                            user_reader=odb_user_reader,
                            user_reader_password=odb_user_reader_password,
                            root_password=odb_root_password,
                            kegg_species=kegg_species,
                            sqlalchemy_connection_string=sqlalchemy_connection_string,
                            snp_related_traits=snp_related_traits,
                            drugbank_user=drugbank_user,
                            drugbank_password=drugbank_password,
                            gwas_catalog_disease_keyword=gwas_catalog_disease_keyword)

    bel = Bel()

    if not skip_drugbank:
        bel.drugbank.get_user_passwd(drugbank_user=drugbank_user, drugbank_password=drugbank_password)

    skip = skip.split(",") if isinstance(skip, str) else skip
    include = include.split(",") if isinstance(include, str) else include

    if skip_drugbank and DRUGBANK not in skip:
        skip.append(DRUGBANK)

    bel.enrich_network(skip=skip, include=include)


@main.command()
@click.argument('connection')
def set_connection(connection):
    """Set the SQLAlchemy connection string.

    :param connection: An existing RDBMS connection.
    """
    ebel.database.set_connection(connection)


@main.command()
@click.option('-h', '--host', default='localhost', help="MySQL server")
@click.option('-u', '--user', default='ebel_user', help="MySQL username")
@click.option('-p', '--password', default='ebel_passwd', help="MySQL password")
@click.option('-d', '--database', default='ebel', help="MySQL database name")
@click.option('-i', '--interactive', is_flag=True, default=False, help="Enable interactive mode")
def set_mysql(host: str, user: str, password: str, database: str, interactive: bool):
    """Set the SQLAlchemy connection string with MySQL settings."""
    if interactive:
        host, user, password, db = ebel.database.set_mysql_interactive()

    ebel.database.set_mysql_connection(
        host=host,
        user=user,
        password=password,
        db=database
    )


@main.command()
@click.option('-p', '--port', default='5000', help='server port [5000]')
@click.option('-d', '--debug_mode', is_flag=True, default=False, help='debug mode')
@click.option('-o', '--open_browser', is_flag=True, default=False, help='open browser')
def serve(port, debug_mode, open_browser):
    """Start the API RESTful server."""
    web.app.run(port, debug_mode, open_browser)


if __name__ == '__main__':
    main()
