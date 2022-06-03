"""Command line interface to e(BE:L)."""

import re
import sys
import logging
import random
import string

from collections import namedtuple
from getpass import getpass
from urllib.parse import quote

import click
import pymysql

import ebel.database
from ebel import Bel, web
from ebel.tools import get_config_as_dict
from ebel.manager.orientdb.odb_meta import Graph
from ebel.manager.orientdb.constants import DRUGBANK
from ebel.constants import TerminalFormatting as TF
from ebel.validate import validate_bel_file, repair_bel_file

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
@click.option('-l', '--line_by_line', is_flag=True, default=False, help='check script line by line')
@click.option('-r', '--reports', default=None,
              help='path(s) to report file(s) seperated by comma with suffix (.md, .txt, .csv, .tsv, .json, .html)')
@click.option('-v', '--bel_version', default="2_1", help='stores a report in a file')
@click.option('-t', '--tree', is_flag=True, default=False, help='shows tree')
# TODO: Implement new Cytoscape export file
# @click.option('-c', '--cytoscape', is_flag=True, default=False, help='creates cytoscape file')
@click.option('-s', '--sqlalchemy_connection_str', default=None, help="SQLAlchmy connection string")
@click.option('-j', '--json_file', is_flag=True, help="Create json file")
@click.option('-f', '--force_json', is_flag=True, default=False, help="Force the creation of a JSON file")
def validate(bel_script_path: str, line_by_line: bool, reports: str,
             bel_version: str, tree: bool, sqlalchemy_connection_str: str,
             json_file: bool, force_json: bool):
    """Validate a BEL file using the defined grammar."""
    validate_bel_file(bel_script_path=bel_script_path, line_by_line=line_by_line, reports=reports,
                      bel_version=bel_version, tree=tree, sqlalchemy_connection_str=sqlalchemy_connection_str,
                      json_file=json_file, force_json=force_json)


@main.command()
@click.argument('bel_script_path')
@click.option('-n', '--new_file_path', default=None,
              help='Path to write repaired file to. If none passed, will overwrite original file.')
def repair(bel_script_path: str, new_file_path: str):
    repair_bel_file(bel_script_path, new_file_path)


@main.command()
@click.argument('json_file_path')
@click.option('-e', '--extend', is_flag=True, default=True, help='Flag to disable "extension" during import')
@click.option('-g', '--p2g', is_flag=True, default=True, help='Flag to disable "protein2gene" during import')
@click.option('-s', '--skip_drugbank', is_flag=True, default=False, help='Flag to disable DrugBank')
@click.option('-i', '--include_subfolders', is_flag=True, default=False, help='Flag to enable directory walking')
@click.option('--drugbank_user', help='Valid username for DrugBank')
@click.option('--drugbank_password', help='Valid username for DrugBank')
@click.option('-n', '--odb_name', help='OrientDB database name')
@click.option('-u', '--odb_user', help='OrientDB user (with admin rights)')
@click.option('-p', '--odb_password', help='OrientDB user (with admin rights) password')
@click.option('-h', '--odb_server', help='OrientDB server name or URI')
@click.option('-o', '--odb_port', help='OrientDB server port')
@click.option('--odb_user_reader', help=' OrientDB user with only read rights')
@click.option('--odb_user_reader_password', help='OrientDB user with only read rights password')
@click.option('--odb_root_password', help='OrientDB root user password (only during database setup)')
@click.option('--kegg_species', help='KEGG species')
@click.option('--sqlalchemy_connection_string', help='schema is user:password@server/database')
@click.option('--snp_related_traits', help='key of SNP related traits in GWAS catalog')
@click.option('--drugbank_user', help='Drugbank user')
@click.option('--drugbank_password', help='DrugBank password')
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
                snp_related_traits: str):
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
                            drugbank_password=drugbank_password)

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
@click.option('--snp_related_traits', help='key of SNP related traits in GWAS catalog and ClinVar')
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
           snp_related_traits: str):
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
    odb_user: str
        OrientDB user (with admin rights)
    odb_password: str
        OrientDB user (with admin rights) password
    odb_server: str
        OrientDB server name or URI
    odb_port: int
        OrientDB server port
    odb_user_reader: str
        OrientDB user with only read rights
    odb_user_reader_password:
        OrientDB user with only read rights password
    odb_root_password: str
        OrientDB root user password (only first database setup needed)
    kegg_species: str
        KEGG species 3-4 letter code https://www.genome.jp/kegg/catalog/org_list4.html
    sqlalchemy_connection_string:
        SQL Alchemy connection string schema: user:passwd@server/database
    snp_related_traits: str
        SNP related traits
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
                            drugbank_password=drugbank_password)

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
def settings():
    """Interactive method to create a configuration file."""
    old_configs = get_config_as_dict()
    configs = {}
    allowed_passwd_chars = string.ascii_letters

    print(f"\n{TF.TITLE}e(BE:L) Configuration WIZARD{TF.RESET}")
    print("\nThe following questionnaire will set all configurations for you.\n")
    print("Before we start: Make sure\n\t1. OrientDB and\n\t2. MySQL/MariaDB\n are running and "
          "you have the root password for both,\n if databases and users not already exists.\n")
    print(f"Default {TF.DEFAULT_VALUE}[values]{TF.RESET} are written in square brackets and "
          f"can be confirmed by RETURN.\n")

    print(f"{TF.Format.UNDERLINED}Installation references{TF.RESET}")
    print(f"\t OrientDB: {TF.Fore.BLUE}https://orientdb.org/docs/3.1.x/fiveminute/java.html{TF.RESET}")
    print(f"\t MySQL: {TF.Fore.BLUE}"
          f"https://dev.mysql.com/doc/mysql-getting-started/en/#mysql-getting-started-installing{TF.RESET}")
    print(f"\t MariaDB: {TF.Fore.BLUE}https://mariadb.com/kb/en/getting-installing-and-upgrading-mariadb/{TF.RESET}")

    print(f"\n{TF.HEADER}Graph database (OrientDB) settings{TF.RESET}")

    Configuration = namedtuple('Configuration', ['name',
                                                 'question',
                                                 'default',
                                                 'validation_regex',
                                                 'is_password',
                                                 'required'])

    old_configs_odb = old_configs.get('DEFAULT_ODB', {})
    orientdb_configs = {
        'name': (f"OrientDB database name (created if not exists)",
                 old_configs_odb.get('name', 'ebel'), r'^[A-Za-z]\w{2,}$', False, True),
        'user': ("OrientDB user (admin) name (created if not exists)",
                 old_configs_odb.get('user', 'ebel_user'), r'^[A-Za-z]\w{2,}$', False, True),
        'password': ("OrientDB user (admin) password (created if not exists)",
                     ''.join(random.sample(allowed_passwd_chars, 12)), None, True, True),
        'server': ("OrientDB server",
                   old_configs_odb.get('server', 'localhost'), None, False, True),
        'port': ("OrientDB port",
                 old_configs_odb.get('port', '2424'), r'^\d+$', False, True),
        'user_reader': ("OrientDB user (reader) name (created if not exists).",
                        old_configs_odb.get('user_reader', 'ebel_reader'), r'^[A-Za-z]\w{2,}$', False, False),
        'user_reader_password': ("OrientDB user (reader) password (created if not exists).",
                                 ''.join(random.sample(allowed_passwd_chars, 12)), None, True, True),
    }

    for param_name, options in orientdb_configs.items():
        conf = Configuration(param_name, *options)
        input_method = getpass if conf.is_password else input
        invalid_value = True
        while invalid_value:
            if conf.default:
                question = f"{TF.QUESTION}{conf.question}{TF.RESET} {TF.DEFAULT_VALUE}[{conf.default}]{TF.RESET}"
                configs[conf.name] = input_method(f"\n{question} ?\n").strip() or conf.default
            else:
                configs[conf.name] = input_method(f"\n{TF.QUESTION}{conf.question}{TF.RESET}\n").strip()
            if conf.validation_regex and conf.required:
                invalid_value = not bool(re.search(conf.validation_regex, configs[conf.name]))
                if invalid_value:
                    print("!!!>>> WARNING <<<!!!\nThe value you type in is not valid. Please type in again.")
            else:
                invalid_value = False

    ebel.database.get_orientdb_client(
        server=configs['server'],
        port=int(configs['port']),
        name=configs['name'],
        user=configs['user'],
        password=configs['password'],
        root_password=None,
        user_reader=configs['user_reader'],
        user_reader_password=configs['user_reader_password']
    )

    print(f"\n{TF.HEADER}KEGG settings{TF.RESET}")

    kegg_question = f"{TF.QUESTION}KEGG species as 3-4 letter code comma separated.{TF.RESET}\n" \
                    "(see here for the letter code: " \
                    f"{TF.Fore.BLUE}https://www.genome.jp/kegg/catalog/org_list4.html{TF.RESET} )\n" \
                    f"{TF.DEFAULT_VALUE}[hsa,rno,mmu]{TF.RESET}\n"
    configs['kegg_species'] = input(kegg_question).strip() or 'hsa,rno,mmu'

    print(f"\n{TF.HEADER}MySQL/MariaDB settings{TF.RESET}")

    old_mysql = {}
    old_sa_con_str = old_configs.get('sqlalchemy_connection_string', '').strip()
    if old_sa_con_str:
        regex_con_str = r"^mysql\+pymysql://(?P<mysql_user>.*?):" \
                        r"(?P<mysql_passwd>.*?)@(?P<mysql_host>.*?)/(?P<mysql_db>.*)$"
        found_old_mysql = re.search(regex_con_str, old_sa_con_str)
        if found_old_mysql:
            old_mysql = found_old_mysql.groupdict()

    default_mysql_host = old_mysql.get('mysql_host') or 'localhost'
    mysql_host_question = f"{TF.QUESTION}MySQL/MariaDB sever name{TF.RESET} " \
                          f"{TF.DEFAULT_VALUE}[{default_mysql_host}]{TF.RESET}\n"
    mysql_host = input(mysql_host_question) or default_mysql_host
    default_mysql_user = old_mysql.get('mysql_user') or 'ebel'
    mysql_user_question = f"{TF.QUESTION}MySQL/MariaDB ebel user{TF.RESET} " \
                          f"{TF.DEFAULT_VALUE}[{default_mysql_user}]{TF.RESET}\n"
    mysql_user = input(mysql_user_question).strip() or default_mysql_user
    mysql_random_password = ''.join(random.sample(allowed_passwd_chars, 12))
    mysql_passed_question = f"{TF.QUESTION}MySQL/MariaDB ebel database password{TF.RESET} " \
                            f"{TF.DEFAULT_VALUE}[{mysql_random_password}]{TF.RESET}\n"
    mysql_passwd = getpass(mysql_passed_question).strip() or mysql_random_password
    default_mysql_db = old_mysql.get('mysql_db') or 'ebel'
    mysql_db_question = f"{TF.QUESTION}MySQL ebel database name{TF.RESET} " \
                        f"{TF.DEFAULT_VALUE}[{default_mysql_db}]{TF.RESET}\n"
    mysql_db = input(mysql_db_question).strip() or default_mysql_db
    configs['sqlalchemy_connection_string'] = f"{mysql_user}:{quote(mysql_passwd)}@" \
                                              f"{mysql_host}/{mysql_db}?charset=utf8mb4"
    try:
        pymysql.connect(host=mysql_host, user=mysql_user, password=mysql_passwd, db=mysql_db)
    except pymysql.err.OperationalError:
        mysql_root_passwd = getpass(f"{TF.QUESTION}MySQL root password (will be not stored) "
                                    f"to create database and user{TF.RESET}\n")
        print(mysql_host, 'root', mysql_root_passwd)
        cursor = pymysql.connect(host=mysql_host, user='root', password=mysql_root_passwd).cursor()
        db_exists = cursor.execute(f"show databases like %s", mysql_db)
        if not db_exists:
            cursor.execute(f"CREATE DATABASE {mysql_db} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        else:
            print(f"Database {mysql_db} alreay exists.")

        user_exists = cursor.execute(f"Select 1 from mysql.user where User=%s", mysql_user)
        if user_exists:
            print("Recreate user, because already exists")
            cursor.execute(f"DROP USER '{mysql_user}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
        sql = f"CREATE USER '{mysql_user}'@'%' IDENTIFIED BY '{mysql_passwd}'"
        print(sql)
        cursor.execute(sql)
        cursor.execute("FLUSH PRIVILEGES")

        privileges_exists = cursor.execute("Select 1 from mysql.db where User=%s and Db=%s", (mysql_user, mysql_db))
        if not privileges_exists:
            sql = f"GRANT ALL PRIVILEGES ON `{mysql_db}`.*  TO '{mysql_user}'@'%'"
            print(sql)
            cursor.execute(sql)
            cursor.execute("FLUSH PRIVILEGES")
        else:
            print(f"MySQL user {mysql_user} have alreay the rights for {mysql_db}.")

    print(f"\n{TF.HEADER}SNP related traits settings{TF.RESET}")

    default_snp_related_traits = old_configs.get('snp_related_traits') or 'Alzheimer,Parkinson'
    snp_related_traits_question = f"{TF.QUESTION}SNPs related to (separated by comma){TF.RESET} " \
                                  f"{TF.DEFAULT_VALUE}[{default_snp_related_traits}]{TF.RESET}\n"
    snp_related_traits = input(snp_related_traits_question).strip()
    configs['snp_related_traits'] = snp_related_traits or default_snp_related_traits

    print(f"\n{TF.HEADER}DrugBank settings{TF.RESET}")
    print("\nIf you have a valid DrugBank account (otherwise leave it blank):\n")
    drugbank_user = input(f"{TF.QUESTION}DrugBank user?{TF.RESET}\n").strip()
    if drugbank_user:
        configs['drugbank_user'] = drugbank_user
        configs['drugbank_password'] = getpass(f"{TF.QUESTION}DrugBank password?{TF.RESET}\n")

    Graph.set_configuration(**configs)


@main.command()
@click.option('-h', '--host', default='0.0.0.0', help='Server or host name')
@click.option('-p', '--port', default='5000', help='server port [5000]')
@click.option('-d', '--debug_mode', is_flag=True, default=False, help='debug mode')
@click.option('-o', '--open_browser', is_flag=True, default=False, help='open browser')
def serve(host, port, debug_mode, open_browser):
    """Start the API RESTful server."""
    web.app.run(host=host, port=port, debug_mode=debug_mode, open_browser=open_browser)


if __name__ == '__main__':
    main()
