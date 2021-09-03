"""Methods for interfacing with the RDBMS."""
import getpass

import pymysql

from ebel.cache import logger
from ebel.tools import write_to_config
from ebel.defaults import CONN_STR_DEFAULT


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
        conn = pymysql.connect(root_host, 'root', root_pwd)
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
    charset : str
        MySQL database charset.

    Returns
    -------
    str
        SQLAlchemy MySQL connection string.

    """
    connection_string = f'mysql+pymysql://{user}:{password}@{host}/{db}?charset={charset}'
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
