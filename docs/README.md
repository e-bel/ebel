## e(BE:L) |docs| |python_versions|
e(BE:L) is a Python package built for both validating and modeling information extracted from publications using `Biological Expression Language (BEL) <https://language.bel.bio/>`_.
This software package serves a comprehensive tool for all of your BEL needs and serves to create enriched knowledge graphs
for developing and testing new theories and hypotheses.

*e(BE:L)* have implemented several other knowledge bases to extend the BEL knowledge graph or map identifiers.

* [BioGrid](https://thebiogrid.org/)
* [ChEBI](https://www.ebi.ac.uk/chebi/)
* [ClinicalTrials.gov](https://clinicaltrials.gov/)
* [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)
* [DisGeNET](https://www.disgenet.org/)
* [DrugBank](https://go.drugbank.com/)
* [Ensembl]()
* [Expression Atlas](https://www.ebi.ac.uk/gxa/home)
* [GWAS Catalog](https://www.ebi.ac.uk/gxa/home)
* [HGNC](https://www.genenames.org/)
* [IntAct]()
* [Guide to PHARMACOLOGY](https://www.guidetopharmacology.org/)
* [KEGG](https://www.genome.jp/kegg/)
* [MirTarBase](https://mirtarbase.cuhk.edu.cn/~miRTarBase/miRTarBase_2022/php/index.php)
* [Different resources from NCBI](https://www.ncbi.nlm.nih.gov/)
* [OffSides](http://tatonettilab.org/offsides/)
* [Pathway Commons](https://www.pathwaycommons.org/)
* [The Human Protein Atlas](https://www.proteinatlas.org/)
* [Reactome](https://reactome.org/)
* [STRING](https://string-db.org/)
* [UniProt]()

## Installation |pypi_version| |pypi_license|

The easiest way to install ebel is to use `docker-compose`. See below instructions to use the docker installation.


`ebel` can be directly installed from PyPi with pip
```bash
pip install ebel
```

But we want to encourage you to use the latest development version which can be installed with::
```bash
pip install git+https://github.com/e-bel/ebel
```

## Package Requirements

### Installing OrientDB

This software package is designed to work in conjunction with OrientDB, a NoSQL, multi-model database
that acts as both a graph and relational database. e(BE:L) uses OrientDB for generating the knowledge graph derived from BEL files. To get
started with e(BE:L), first download OrientDB and get a server up and running.
The first time the server is started, you will need to create a root password. Once it is up and running, you can get
start importing BEL files into it!

On Linux you can use following commands
```bash
wget https://repo1.maven.org/maven2/com/orientechnologies/orientdb-community/3.2.2/orientdb-community-3.2.2.tar.gz
tar -xvzf orientdb-community-3.2.2.tar.gz
cd orientdb-community-3.2.2/bin
./server.sh
```

### SQL Databases

This package is capable of enriching the compiled knowledge graphs with a lot of external information, however, this requires
a SQL databases for storage. While, a SQLite database can be used, this is not recommended as the amount of data and
complexity of queries will be quite slow. Additionally, SQLite will not be directly supported, the methods will be built
such that they should work with both SQLite and MySQL, but we will not address performance issues due to using SQLite.

Instead, we recommend setting up a [MySQL server](https://www.mysql.com/downloads/) or 
MariaDB to use with e(BE:L). By default, [PyMySQL](https://pypi.org/project/PyMySQL/)
is installed as a driver by e(BE:L), but others can also be used.

On Linux Ubuntu you can use following command
```bash
sudo apt install mysql-server -y
```
or
```bash
sudo apt install mariadb-server -y
```


### Configuration

Before you start working with e(BE:L), a simple to use wizard helps you to setup all configurations. Make sure OrientDB 
and MySQL (or MariaDB) are running. Then start the configuration wizard with

```bash
ebel settings
```

The wizard will create the needed databases and users in OrientDB and MySQL/MariaDB.

### Package Components

To test the different components you find [here](https://github.com/e-bel/covid19_knowledge_graph/) several BEL and 
already compiled JSON files.

## BEL Validation

BEL is a domain-specific language designed to capture biological relationships in a computer- and human-readable format.
The rules governing BEL statement generation can be quite complex and often mistakes are made during curation.
e(BE:L) includes a grammar and syntax checker that reads through given BEL files and validates whether each statement
satisfies the guidelines provided by [BEL.bio](https://language.bel.bio). Should any BEL statement within the file
not adhere to the rules, a report file is created by e(BE:L) explaining the error and offering suggested fixes.

You can use the following command to validate your BEL file

```bash
ebel validate /path/to/bel_file.bel
```

In a single command, you can validate your BEL file as well as generate error reports if there are errors and if there
are none, produce an importable JSON file::

```bash
ebel validate /path/to/bel_file.bel -r error_report.xlsx -j
```

BEL documents should be properly formatted prior to validation. e(BE:L) contains a repair tool that will check the format
and it is highly recommended that this is used prior to validation. The repaired will overwrite the original if a new file
path is not specified. Here is an example::

```bash
ebel repair /path/to/bel_file.bel -n /path/to/repaired_file.bel
```

## Import Process

### BEL Modeling - OrientDB

BEL files that have passed the validation process can be imported into the
database individually or *en masse*. During the import process, e(BE:L) automatically creates all the relevant nodes and edges
as described in the BEL files. Additionally, e(BE:L) also automatically adds in missing nodes and edges that are known to exist
e.g. protein nodes with a respective RNA or gene node with have these automatically added to the graph with the appropriate `translatedTo` and
`transcribedTo` edges.


Model Enrichment - MySQL
------------------------

e(BE:L) goes one step farther when compiling your BEL statements into a knowledge graph by supplementing your new graph model with information derived from several
publicly available repositories. Data is automatically downloaded from several useful sites including `UniProt` ,
`Ensembl`, and `IntAct` and added as generic tables in your newly built database.
Information from these popular repositories are then linked to the nodes and edges residing in your graph model, allowing for more complex and
useful queries to be made against your data. This data is automatically downloaded, parsed, and imported into a specified SQL database.

Importing - Getting Started
---------------------------

e(BE:L) supports OrientDB as graph database and [MySQL](https://www.mysql.com) and MariaDB as [RDBMS](https://en.wikipedia.org/wiki/Relational_database)

Make sure you have downloaded/installed and running

1. `OrientDB`
2. MySQL or MariaDB
3. Relational Database  
   * MySQL  
     - [Windows](https://dev.mysql.com/doc/refman/8.0/en/windows-installation.html>)  
     - [MacOS](https://dev.mysql.com/doc/refman/8.0/en/macos-installation.html>)  
     - Linux  
         * [Ubuntu, Debian, Linux Mint, ...](https://dev.mysql.com/doc/mysql-apt-repo-quick-guide/en/)  
         - [RedHat, Fedora, CentOS, OpenSUSE, Scientific Linux, ...](https://dev.mysql.com/doc/refman/8.0/en/linux-installation-yum-repo.html>)  
   * MariaDB
     - [Windows](https://mariadb.com/kb/en/installing-mariadb-msi-packages-on-windows/)  
     - [MacOS PKG](https://mariadb.com/kb/en/installing-mariadb-server-pkg-packages-on-macos/)
       - [Homebrew](https://mariadb.com/kb/en/installing-mariadb-on-macos-using-homebrew/)
     - Linux
         - [Ubuntu, Debian, Linux Mint, ...](https://mariadb.com/kb/en/yum/)
         - [RedHat, Fedora, CentOS, OpenSUSE, Scientific Linux, ...](https://mariadb.com/kb/en/installing-mariadb-deb-files/)

This can be configured as a service in both Windows and Unix systems.

Set your MySQL connection parameters in e(BE:L)

```bash
ebel set-mysql --host localhost --user root --password myPassWord --database ebel
```

Once you have made sure both OrientDB and MySQL are running, you can now import an e(BE:L) compiled JSON file

```bash
ebel import-json /path/to/checked_bel.json -u root -p orientdbPassword -d ebel -h localhost -p 2424
```

After you have successfully connected to the OrientDB database at least once, the login credentials will be written to the config file and no longer need to be passed (same with ``enrich`` command)

```bash
ebel import-json /path/to/checked_bel.json
```

You can also import all e(BE:L) compiled JSON files in a passed directory

```bash
ebel import-json /path/to/bel_json/dir/
```

If you do no wish to enrich the graph, or wish to disable the protein/RNA/gene extension step, you can toggle these with the following options

```bash
ebel import-json /path/to/checked_bel.json -e -g
```

You can run an enrichment step later using the ``enrich`` command

```bash
ebel enrich
```

This command can also be given a list of resources to either skip or include during enrichment

```bash
ebel enrich -i uniprot,hgnc
```

or

```bash
ebel enrich -s intact,kegg
```
