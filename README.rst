*********************************
e(BE:L) |docs| |python_versions|
*********************************
e(BE:L) is a Python package built for both validating and modeling information extracted from publications using `Biological Expression Language (BEL) <https://language.bel.bio/>`_.
This software package serves a comprehensive tool for all of your BEL needs and serves to create enriched knowledge graphs
for developing and testing new theories and hypotheses.

Installation |pypi_version| |pypi_license|
==========================================
``ebel`` can be directly installed from PyPi with pip::

    $ pip install ebel

Installing pyorient
-------------------
The current `pyorient driver <https://github.com/orientechnologies/pyorient/>`_ must be installed directly from GitHub
at the moment since the PyPI package is in the process of being transferred. Therefore, to make sure e(BE:L) works, please
install this library directly using::

    $ pip install git+https://github.com/orientechnologies/pyorient/

or it can also be installed using the ``requirements.txt`` file if you cloned the repository::

    $ pip install -r requirements.txt

Package Requirements
====================

Installing OrientDB
-------------------
This software package is designed to work in conjunction with `OrientDB <https://www.orientdb.org/>`_, a NoSQL, multi-model database
that acts as both a graph and relational database. e(BE:L) uses OrientDB for generating the knowledge graph derived from BEL files. To get
started with e(BE:L), first `download OrientDB <https://www.orientdb.org/download/>`_ and get a server up and running.
The first time the server is ran, you will need to create a root password. Once it is up and running, you can get
start importing BEL files into it!

SQL Databases
--------------
This package is capable of enriching the compiled knowledge graphs with a lot of external information, however, this requires
a SQL databases for storage. While, a SQLite database can be used, this is not recommended as the amount of data and
complexity of queries will be quite slow. Additionally, SQLite will not be directly supported, the methods will be built
such that they should work with both SQLite and MySQL, but we will not address performance issues due to using SQLite.

Instead, we recommend setting up a `MySQL server <https://www.mysql.com/downloads/>`_ to use with e(BE:L). By default,
`PyMySQL <https://pypi.org/project/PyMySQL/>`_ is installed as a driver by e(BE:L), but others can also be used.

Package Components
==================

BEL Validation
--------------

BEL is a domain-specific language designed to capture biological relationships in a computer- and human-readable format.
The rules governing BEL statement generation can be quite complex and often mistakes are made during curation.
e(BE:L) includes a grammar and syntax checker that reads through given BEL files and validates whether each statement
satisfies the guidelines provided by `BEL.bio <https://language.bel.bio/>`_. Should any BEL statement within the file
not adhere to the rules, a report file is created by e(BE:L) explaining the error and offering suggested fixes.

You can use the following command to validate your BEL file::

    $ ebel validate /path/to/bel_file.bel

In a single command, you can validate your BEL file as well as generate error reports if there are errors and if there
are none, produce an importable JSON file::

    $ ebel validate /path/to/bel_file.bel -r error_report.xlsx -j

BEL documents should be properly formatted prior to validation. e(BE:L) contains a repair tool that will check the format
and it is highly recommended that this is used prior to validation. The repaired will overwrite the original if a new file
path is not specified. Here is an example::

    $ ebel repair /path/to/bel_file.bel -n /path/to/repaired_file.bel

Import Process
--------------

BEL Modeling - OrientDB
^^^^^^^^^^^^^^^^^^^^^^^

BEL files that have passed the validation process can be imported into the
database individually or *en masse*. During the import process, e(BE:L) automatically creates all of the relevant nodes and edges
as described in the BEL files. Additionally, e(BE:L) also automatically adds in missing nodes and edges that are known to exist
e.g. protein nodes with a respective RNA or gene node with have these automatically added to the graph with the appropriate ``translatedTo`` and
``transcribedTo`` edges.


Model Enrichment - MySQL
^^^^^^^^^^^^^^^^^^^^^^^^

e(BE:L) goes one step farther when compiling your BEL statements into a knowledge graph by supplementing your new graph model with information derived from several
publicly available repositories. Data is automatically downloaded from several useful sites including `UniProt <https://www.uniprot.org/>`_,
`Ensembl <https://www.ensembl.org/index.html>`_, and `IntAct <https://www.ebi.ac.uk/intact/>`_ and added as generic tables in your newly built database.
Information from these popular repositories are then linked to the nodes and edges residing in your graph model, allowing for more complex and
useful queries to be made against your data. This data is automatically downloaded, parsed, and imported into a specified SQL database.

Importing - Getting Started
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Make sure you have downloaded OrientDB and have the server running. This can be configured as a service in both Windows and Unix systems.
Set your MySQL connection parameters in e(BE:L)::

    $ ebel set-mysql --host localhost --user root --password myPassWord --database ebel

Once you have made sure both OrientDB and MySQL are running, you can now import an e(BE:L) compiled JSON file::

    $ ebel import-json /path/to/checked_bel.json -u root -p orientdbPassword -d ebel -h localhost -p 2424

After you have successfully connected to the OrientDB database at least once, the login credentials will be written to the config file and no longer need to be passed (same with ``enrich`` command)::

    $ ebel import-json /path/to/checked_bel.json

You can also import all e(BE:L) compiled JSON files in a passed directory::

    $ ebel import-json /path/to/bel_json/dir/

If you do no wish to enrich the graph, or wish to disable the protein/RNA/gene extension step, you can toggle these with the following options::

    $ ebel import-json /path/to/checked_bel.json -e -g

You can run an enrichment step later using the ``enrich`` command::

    $ ebel enrich

This command can also be given a list of resources to either skip or include during enrichment::

    $ ebel enrich -i uniprot,hgnc

or::

    $ ebel enrich -s intact,kegg

API
---
Finally, this package comes equipped with a built-in RESTful API using Flask. Users that have a running and populated set of databases
can also create a running API server which contains several queries for retrieving information from both the network itself, as well
as the downloaded enrichment information stored in the SQL database.

This server can be activated using::

    $ ebel serve

You can also specify certain parameters as options::

    $ ebel serve -p 5000 --debug-mode

Disclaimer
==========
e(BE:L) is a scientific software that has been developed in an academic capacity, and thus comes with no warranty or guarantee of maintenance, support, or back-up of data.


.. |docs| image:: http://readthedocs.org/projects/ebel/badge/?version=latest
    :target: https://ebel.readthedocs.io/en/latest/
    :alt: Documentation Status

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/ebel.svg
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/ebel.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/ebel.svg
    :alt: Apache-2.0