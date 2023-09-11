"""Collection of methods for handling information caching."""
import getpass
import logging

import pymysql

from ebel import defaults
from ebel.config import write_to_config

# TODO: Decide whether to use these methods or those from database

logger = logging.getLogger(__name__)


def set_mysql_interactive() -> tuple:
    """Interactive mode to setup MySQL database."""
    print(
        "Interactive mode\n \
          ================\n \
          1st setup of db and user with root:\n"
    )
    host = input("host[localhost]:") or "localhost"
    user = input("ebel user[ebel]:") or "ebel"
    password = getpass.getpass(prompt="ebel password[ebel]:") or "ebel"
    db = input("database name[ebel]") or "ebel"
    print(
        "If you want to setup the database automatically,\n \
          then type in the root password, otherwise nothing"
    )
    root_pwd = getpass.getpass(prompt="root password (only for 1st setup):")

    if root_pwd:
        root_host = getpass.getpass(prompt="IP or name mysql server [localhost]:") or "localhost"
        conn = pymysql.connect(host=root_host, user="root", password=root_pwd)
        c = conn.cursor()
        db_exists = c.execute("show databases like '{}'".format(db))

        if not db_exists:
            c.execute("CREATE DATABASE {} CHARACTER SET utf8".format(db))

        else:
            logger.warning(f"Database '{db}' already exists!")

        user_exists = c.execute("Select 1 from mysql.user where User='{}'".format(user))

        if not user_exists:
            sql = "CREATE USER '{}'@'{}' IDENTIFIED BY '{}'".format(
                user,
                host,
                password,
            )
            c.execute(sql)
        else:
            logger.warning(f"Database '{db}' already exists!")

        privileges_exists = c.execute("Select 1 from mysql.db where User='{}' and Db='{}'".format(user, db))
        if not privileges_exists:
            c.execute("GRANT ALL PRIVILEGES ON {}.* TO '{}'@'%'  IDENTIFIED BY '{}'".format(db, user, password))
        else:
            logger.warning(f"User already has privileges for database '{db}'")

        c.execute("FLUSH PRIVILEGES")

    return host, user, password, db


def set_mysql_connection(
    host: str = "localhost",
    user: str = "ebel_user",
    password: str = "ebel_passwd",
    db: str = "ebel",
    charset: str = "utf8mb4",
):
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
    connection_string = "mysql+pymysql://{user}:{passwd}@{host}/{db}?charset={charset}".format(
        host=host, user=user, passwd=password, db=db, charset=charset
    )
    set_connection(connection_string)

    return connection_string


def set_always_create_new_db(always_create_new_db: bool = True) -> None:
    """Set in configuration option `always_create_new_db`.

    Parameters
    ----------
    always_create_new_db : bool
        Option `always_create_new_db` in section `database` in config file.

    """
    write_to_config("database", "always_create_new", str(always_create_new_db))


def set_connection(connection: str = defaults.CONN_STR_DEFAULT) -> None:
    """Set the connection string for SQLAlchemy.

    Parameters
    ----------
    connection: str
        SQLAlchemy connection string.

    """
    write_to_config("database", "sqlalchemy_connection_string", connection)
