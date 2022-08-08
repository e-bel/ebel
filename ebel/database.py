"""Methods for interfacing with the RDBMS."""
import logging
import sys
import getpass
from typing import Optional, Union

import pymysql
from pyorientdb import OrientDB
from pyorientdb.exceptions import PyOrientCommandException, PyOrientConnectionException, \
    PyOrientSecurityAccessException

from ebel.defaults import CONN_STR_DEFAULT
from ebel.config import write_to_config
from ebel.constants import TerminalFormatting as TF

logger = logging.getLogger(__name__)


def orientdb_connection_works(server: str, port: int, name: str, user: str, password: str) -> bool:
    """Check if the connection to OrientDB works."""
    try:
        client = OrientDB(server, port)
        client.set_session_token(True)
        client.db_open(name, user, password)
        works = True

    except Exception as inst:
        print(type(inst))
        works = False

    return works


def get_orientdb_client(server: str, port: int, name: str, user: str, password: str,
                        root_password: Optional[str] = None, user_reader: Optional[str] = None,
                        user_reader_password: Optional[str] = None) -> OrientDB:
    """Attempts to connect to the OrientDB client. This is currently done by using session tokens."""
    # TODO PyOrientStorageException occurs with newer ODB versions
    client = OrientDB(server, port)

    # First try connect as admin user if this fails connect root_user from config,
    # if this fails ask for root password and create user with admin in database
    try:
        client.set_session_token(True)
        client.db_open(name, user, password)

    except (PyOrientCommandException, PyOrientConnectionException, PyOrientSecurityAccessException):
        client.set_session_token(True)
        root_passwd_correct = False
        while not root_passwd_correct:
            odb_root_question = f"{TF.QUESTION}OrientDB root password (to create database and users): {TF.RESET}"
            root_password = root_password or getpass.getpass(odb_root_question)
            try:
                client.connect('root', root_password)
                root_passwd_correct = True
            except (PyOrientConnectionException, PyOrientSecurityAccessException):
                logger.error(f'Connection problem to OrientDB server {server}:{port}')
                print(f"Please make sure the OrientDB server is running, port ({port}), "
                      f"as well server ({server}) and root password are correct")
                sys.exit()

        if not client.db_exists(name):
            client.db_create(name)
            logger.info(f"Create database '{name}'")
            client.db_open(name, 'root', root_password)
            # create user with admin rights
            client.command(
                f"CREATE USER {user} IDENTIFIED BY {password} ROLE admin")
            # create a reader
            if user_reader and user_reader_password:
                client.command(
                    f"CREATE USER {user_reader} IDENTIFIED BY {user_reader_password} ROLE reader")
            client.close()
            # reopen with new user and password
            client = OrientDB(server, int(port))
            client.set_session_token(True)
            client.db_open(name, user, password)
        else:
            client.db_open(name, 'root', root_password)
            # admin
            admin_user_exists_sql = "Select true as admin_user_exists from OUser " \
                                    f"where name = '{user}' and status='ACTIVE' and 'admin' in roles.name"
            admin_user_exists = client.command(admin_user_exists_sql)
            if admin_user_exists:
                print("Update password for OrientDB admin")
                client.command(
                    f"UPDATE OUser SET password = '{password}' WHERE name = '{user}'")
            else:
                print("Create password for OrientDB reader")
                client.command(
                    f"CREATE USER {user} IDENTIFIED BY {password} ROLE admin")

            # reader
            if user_reader and user_reader_password:
                reader_user_exists_sql = "Select true as admin_user_exists from OUser " \
                                         f"where name = '{user_reader}' and status='ACTIVE' and 'reader' in roles.name"
                reader_user_exists = client.command(reader_user_exists_sql)
                if reader_user_exists:
                    client.command(
                        f"UPDATE OUser SET password = '{user_reader_password}' WHERE name = '{user_reader}'")
                else:
                    client.command(
                        f"CREATE USER {user_reader} IDENTIFIED BY {user_reader_password} ROLE admin")

    return client


def set_mysql_interactive() -> tuple:
    """Interactive mode to setup MySQL database."""
    print("Interactive mode\n \
          ================\n \
          1st setup of db and user with root:\n")
    host = input("host[localhost]:") or 'localhost'
    user = input("ebel user[ebel]:") or 'ebel'
    password = getpass.getpass(prompt="ebel password[ebel]:") or 'ebel'
    db = input("database name[ebel]") or 'ebel'
    print("If you want to setup the database automatically,\n \
          then type in the root password, otherwise nothing")
    root_pwd = getpass.getpass(prompt='root password (only for 1st setup):')

    if root_pwd:
        root_host = getpass.getpass(prompt='IP or name mysql server [localhost]:') or 'localhost'
        conn = pymysql.connect(host=root_host, user='root', password=root_pwd)
        c = conn.cursor()
        db_exists = c.execute(f"show databases like '{db}'")

        if not db_exists:
            c.execute(f"CREATE DATABASE {db} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        else:
            logger.warning(f"Database '{db}' already exists!")

        user_exists = c.execute(f"Select 1 from mysql.user where User='{user}'")

        if not user_exists:
            sql = "CREATE USER '{}'@'{}' IDENTIFIED BY '{}'".format(
                user,
                host,
                password,
            )
            c.execute(sql)
        else:
            logger.warning(f"Database '{db}' already exists!")

        privileges_exists = c.execute(f"Select 1 from mysql.db where User='{user}' and Db='{db}'")
        if not privileges_exists:
            c.execute(f"GRANT ALL PRIVILEGES ON {db}.* TO '{user}'@'%'  IDENTIFIED BY '{password}'")
        else:
            logger.warning(f"User already has privileges for database '{db}'")

        c.execute("FLUSH PRIVILEGES")

    return host, user, password, db


def set_mysql_connection(host: str = 'localhost',
                         user: str = 'ebel_user',
                         password: str = 'ebel_passwd',
                         db: str = 'ebel',
                         port: Union[str, int] = '3306',
                         charset: str = 'utf8mb4'):
    """Set the connection using MySQL Parameters.

    Parameters
    ----------
    host : str
        MySQL database host.
    user : str
        MySQL database user.
    password : str
        MySQL database password.
    db : str
        MySQL database name.
    port : Union[str,int]
        The port of the MySQL database.
    charset : str
        MySQL database charset.

    Returns
    -------
    str
        SQLAlchemy MySQL connection string.

    """
    connection_string = f'mysql+pymysql://{user}:{password}@{host}/{db}:{port}?charset={charset}'
    set_connection(connection_string)

    return connection_string


def set_always_create_new_db(always_create_new_db: bool = True) -> None:
    """Set in configuration option `always_create_new_db`.

    Parameters
    ----------
    always_create_new_db : bool
        Option `always_create_new_db` in section `database` in config file.

    """
    write_to_config('database', 'always_create_new', str(always_create_new_db))


def set_connection(connection: str = CONN_STR_DEFAULT) -> None:
    """Set the connection string for SQLAlchemy.

    Parameters
    ----------
    connection: str
        SQLAlchemy connection string.

    """
    write_to_config('DATABASE', 'sqlalchemy_connection_string', connection)
