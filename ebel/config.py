"""Methods for handling the configuration file."""
import configparser
import logging
import random
import re
import os
import string
from collections import namedtuple
from configparser import RawConfigParser
from getpass import getpass
from typing import Union, Optional
from urllib.parse import quote

import pymysql

from ebel import defaults
from ebel.constants import DEFAULT_ODB, TerminalFormatting as TF
from ebel.defaults import CONN_STR_DEFAULT, DATABASE_LOCATION


def set_configuration(name: str = None,
                      user: str = None,
                      password: str = None,
                      server: str = None,
                      port: Union[str, int] = None,
                      user_reader: str = None,
                      user_reader_password: str = None,
                      root_password: str = None,
                      kegg_species: str = None,
                      sqlalchemy_connection_string: str = None,
                      snp_related_traits: str = None,
                      drugbank_user: str = None,
                      drugbank_password: str = None) -> dict:
    """Set configuration values in the config file."""
    odb_class_attribs = {
        'name': name,
        'user': user,
        'password': password,
        'server': server,
        'port': port,
        'user_reader': user_reader,
        'user_reader_password': user_reader_password,
        'root_password': root_password
    }

    for param, value in odb_class_attribs.items():
        write_to_config(DEFAULT_ODB, param, value)

    if kegg_species:
        write_to_config('KEGG', 'species', kegg_species)

    if sqlalchemy_connection_string:
        write_to_config('DATABASE', 'sqlalchemy_connection_string', sqlalchemy_connection_string)

    if snp_related_traits:
        write_to_config('SNP_RELATED_TRAITS', 'keyword', snp_related_traits)

    if drugbank_user:
        write_to_config('DRUGBANK', 'user', drugbank_user)

    if drugbank_password:
        write_to_config('DRUGBANK', 'password', drugbank_password)

    return get_config_as_dict()


def write_to_config(section: str, option: str, value: str) -> None:
    """Write section, option and value to config file.

    Parameters
    ----------
    section : str
        Section name of configuration file.
    option : str
        Option name.
    value : str
        Option value.
    """
    if value:
        cfp = defaults.config_file_path
        config = RawConfigParser()

        if not os.path.exists(cfp):
            with open(cfp, 'w') as config_file:
                config[section] = {option: value}
                config.write(config_file)
                logging.info(f'Set in configuration file {cfp} in section {section} {option}={value}')
        else:
            config.read(cfp)
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, option, value)
            with open(cfp, 'w') as configfile:
                config.write(configfile)


def get_config_as_dict():
    """Get ebel configuration as dictionary if config file exists."""
    cfp = defaults.config_file_path
    if os.path.exists(cfp):
        config = RawConfigParser()
        config.read(cfp)
        return config._sections

    else:
        return user_config_setup(config_exists=False)


def user_config_setup(config_exists: bool = True) -> dict:
    """Set up the configuration file."""
    old_configs = get_config_as_dict() if config_exists else {}
    configs = {}

    print(f"\n{TF.TITLE}e(BE:L) Configuration WIZARD{TF.RESET}")
    print("\nThe following questionnaire will guide you through the configuration process.\n")
    print("Before we start: Make sure\n\t1. OrientDB and\n\t2. MySQL/MariaDB (optional)\n are running and "
          "you have the root password for both, if databases and users do not already exist.\n")
    print(f"Default {TF.DEFAULT_VALUE}[values]{TF.RESET} are written in square brackets and "
          f"can be confirmed by RETURN.\n")

    print(f"{TF.Format.UNDERLINED}Installation references{TF.RESET}")
    print(f"\t OrientDB: {TF.Fore.BLUE}https://orientdb.org/docs/3.1.x/fiveminute/java.html{TF.RESET}")
    print(f"\t MySQL: {TF.Fore.BLUE}"
          f"https://dev.mysql.com/doc/mysql-getting-started/en/#mysql-getting-started-installing{TF.RESET}")
    print(f"\t MariaDB: {TF.Fore.BLUE}https://mariadb.com/kb/en/getting-installing-and-upgrading-mariadb/{TF.RESET}\n")

    # RDBMS setup
    old_sa_con_str = old_configs.get('sqlalchemy_connection_string', '').strip()
    configs['sqlalchemy_connection_string'] = __user_rdbms_setup(old_sa_con_str)

    # OrientDB Setup
    print(f"\n{TF.HEADER}Graph database (OrientDB) settings{TF.RESET}")

    Configuration = namedtuple('Configuration', ['name',
                                                 'question',
                                                 'default',
                                                 'validation_regex',
                                                 'is_password',
                                                 'required'])

    old_configs_odb = old_configs.get(DEFAULT_ODB, {})
    orientdb_configs = {
        'name': ("OrientDB database name (created if not exists)",
                 old_configs_odb.get('name', 'ebel'), r'^[A-Za-z]\w{2,}$', False, True),
        'user': ("OrientDB user (admin) name (created if not exists)",
                 old_configs_odb.get('user', 'ebel_user'), r'^[A-Za-z]\w{2,}$', False, True),
        'password': ("OrientDB user (admin) password (created if not exists)",
                     ''.join(random.sample(string.ascii_letters, 12)), None, True, True),
        'server': ("OrientDB server",
                   old_configs_odb.get('server', 'localhost'), None, False, True),
        'port': ("OrientDB port",
                 old_configs_odb.get('port', '2424'), r'^\d+$', False, True),
        'user_reader': ("OrientDB user (reader) name (created if not exists).",
                        old_configs_odb.get('user_reader', 'ebel_reader'), r'^[A-Za-z]\w{2,}$', False, False),
        'user_reader_password': ("OrientDB user (reader) password (created if not exists).",
                                 ''.join(random.sample(string.ascii_letters, 12)), None, True, True),
    }

    for param_name, options in orientdb_configs.items():
        conf = Configuration(param_name, *options)
        input_method = getpass if conf.is_password else input
        invalid_value = True
        while invalid_value:
            if conf.default:
                question = f"{TF.QUESTION}{conf.question}{TF.RESET} {TF.DEFAULT_VALUE}[{conf.default}]{TF.RESET}"
                configs[conf.name] = input_method(f"{question}: ").strip() or conf.default

            else:
                configs[conf.name] = input_method(f"{TF.QUESTION}{conf.question}{TF.RESET}").strip()

            if conf.validation_regex and conf.required:
                invalid_value = not bool(re.search(conf.validation_regex, configs[conf.name]))
                if invalid_value:
                    print("!!!>>> WARNING <<<!!!\nInvalid entry. Please select a valid option")

            else:
                invalid_value = False

    # KEGG
    print(f"\n{TF.HEADER}KEGG settings{TF.RESET}")

    kegg_question = f"{TF.QUESTION}KEGG species as 3-4 letter code comma separated.{TF.RESET} " \
                    "(see here for the KEGG organism letter codes: " \
                    f"{TF.Fore.BLUE}https://www.genome.jp/kegg/catalog/org_list4.html{TF.RESET} ) " \
                    f"{TF.DEFAULT_VALUE}[hsa,rno,mmu]: {TF.RESET}"
    configs['kegg_species'] = input(kegg_question).strip() or 'hsa,rno,mmu'

    print(f"\n{TF.HEADER}SNP related traits settings{TF.RESET}")

    # SNP
    default_snp_related_traits = old_configs.get('snp_related_traits') or 'Alzheimer,Parkinson'
    snp_related_traits_question = f"{TF.QUESTION}SNPs related to (separated by comma){TF.RESET} " \
                                  f"{TF.DEFAULT_VALUE}[{default_snp_related_traits}]: {TF.RESET}"
    snp_related_traits = input(snp_related_traits_question).strip()
    configs['snp_related_traits'] = snp_related_traits or default_snp_related_traits

    # DrugBank
    print(f"\n{TF.HEADER}DrugBank settings{TF.RESET}")
    print("If you have a valid DrugBank account (otherwise leave it blank): ")
    drugbank_user = input(f"{TF.QUESTION}DrugBank user: {TF.RESET}").strip()

    if drugbank_user:
        configs['drugbank_user'] = drugbank_user
        configs['drugbank_password'] = getpass(f"{TF.QUESTION}DrugBank password: {TF.RESET}")

    current_config = set_configuration(**configs)

    return current_config


def __user_orientdb_setup():
    """Set up ODB params."""
    pass


def __user_rdbms_setup(prev_conn: str) -> str:
    """The initial setup process for the RDBMS."""
    db_choice = input("""e(BE:L) requires some basic information in order to begin importing data and building a
Knowledge Graph. The nodes and edges compiled from BEL statements are imported into OrientDB while the information
parsed from external repositories is stored in a more traditional relational database and uses either SQLite or MySQL.

While SQLite is easier to set up and does not require installing additional software, MySQL is the recommended
option due to the amount of information that will be imported.

MySQL/SQLite [MySQL]: """) or "mysql"

    while db_choice.lower() not in ("sqlite", "mysql"):
        db_choice = input("Bad input, please enter either 'MySQL' or 'SQLite': ")

    if db_choice.lower() == "sqlite":
        db_conn = CONN_STR_DEFAULT
        print(f"SQLite DB can be found at {DATABASE_LOCATION}")

    else:  # MySQL
        db_conn = __mysql_setup(prev_conn)

    print("Database set. Connection string can be changed using `ebel set_connection` or `ebel set_mysql`")
    return db_conn


def __mysql_setup(old_sa_con_str: str) -> str:
    """Set up the MySQL/MariaDB connection and return the conenction string."""
    print(f"\n{TF.HEADER}MySQL/MariaDB settings{TF.RESET}")

    old_mysql = {}

    if old_sa_con_str:
        regex_con_str = r"^mysql\+pymysql://(?P<mysql_user>.*?):" \
                        r"(?P<mysql_passwd>.*?)@(?P<mysql_host>.*?)/(?P<mysql_db>.*)$"
        found_old_mysql = re.search(regex_con_str, old_sa_con_str)
        if found_old_mysql:
            old_mysql = found_old_mysql.groupdict()

    default_mysql_host = old_mysql.get('mysql_host') or 'localhost'
    mysql_host_question = f"{TF.QUESTION}MySQL/MariaDB server name{TF.RESET} " \
                          f"{TF.DEFAULT_VALUE}[{default_mysql_host}]: {TF.RESET}"
    mysql_host = input(mysql_host_question) or default_mysql_host

    default_mysql_port = old_mysql.get('mysql_db') or '3306'
    mysql_port_question = f"{TF.QUESTION}MySQL/MariaDB port{TF.RESET} " \
                          f"{TF.DEFAULT_VALUE}[{default_mysql_port}]: {TF.RESET}"
    mysql_port = input(mysql_port_question).strip() or default_mysql_port

    default_mysql_user = old_mysql.get('mysql_user') or 'ebel'
    mysql_user_question = f"{TF.QUESTION}MySQL/MariaDB (non-root) user{TF.RESET} " \
                          f"{TF.DEFAULT_VALUE}[{default_mysql_user}]: {TF.RESET}"
    mysql_user = input(mysql_user_question).strip() or default_mysql_user

    mysql_random_password = ''.join(random.sample(string.ascii_letters, 12))
    mysql_passed_question = f"{TF.QUESTION}MySQL/MariaDB password for user{TF.RESET} " \
                            f"{TF.DEFAULT_VALUE}[{mysql_random_password}]: {TF.RESET}"
    mysql_pwd = getpass(mysql_passed_question).strip() or mysql_random_password

    default_mysql_db = old_mysql.get('mysql_db') or 'ebel'
    mysql_db_question = f"{TF.QUESTION}MySQL/MariaDB database name{TF.RESET} " \
                        f"{TF.DEFAULT_VALUE}[{default_mysql_db}]: {TF.RESET}"
    mysql_db = input(mysql_db_question).strip() or default_mysql_db

    db_conn = f"mysql+pymysql://{mysql_user}:{quote(mysql_pwd)}@{mysql_host}:{mysql_port}/{mysql_db}?charset=utf8mb4"

    try:
        pymysql.connect(host=mysql_host, user=mysql_user, password=mysql_pwd, db=mysql_db)

    except pymysql.err.OperationalError:
        mysql_root_passwd = getpass(f"{TF.QUESTION}MySQL root password (will be not stored) "
                                    f"to create database and user: {TF.RESET}")
        print(mysql_host, 'root', mysql_root_passwd)
        cursor = pymysql.connect(host=mysql_host, user='root', password=mysql_root_passwd).cursor()
        db_exists = cursor.execute("show databases like %s", mysql_db)
        if not db_exists:
            cursor.execute(f"CREATE DATABASE {mysql_db} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        else:
            print(f"Database {mysql_db} already exists.")

        user_exists = cursor.execute("Select 1 from mysql.user where User=%s", mysql_user)

        if user_exists:
            print("USer already exists, will be recreated")
            cursor.execute(f"DROP USER '{mysql_user}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
        sql = f"CREATE USER '{mysql_user}'@'%' IDENTIFIED BY '{mysql_pwd}'"
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
            print(f"MySQL user {mysql_user} already has sufficient rights to {mysql_db}")

    return db_conn


def get_config_value(section, option, value=None) -> Optional[str]:
    """Retrieve value from a given section and option from the config file if it exists.

    Parameters
    ----------
    section (str): Configuration section header
    option (str): Option value within the section
    value (str): (optional) value to set the option equal to if option doesn't exist

    Returns
    -------
    config_value: The value of the specified section and option
    """
    cfg = configparser.ConfigParser()

    if os.path.isfile(defaults.config_file_path):
        cfg.read(defaults.config_file_path)

        if cfg.has_section(section) and cfg.has_option(section=section, option=option):
            config_value = cfg[section][option]

        elif value is not None:
            write_to_config(section, option, value)
            config_value = value

        else:
            return None

    else:
        write_to_config(section, option, value)
        config_value = value

    return config_value
