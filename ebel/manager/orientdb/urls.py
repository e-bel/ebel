"""URLs to download files."""

# HGNC #
HGNC_JSON = "ftp://ftp.ebi.ac.uk/pub/databases/genenames/new/json/hgnc_complete_set.json"
HGNC_TSV = "ftp://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt"
HCOP_GZIP = 'ftp://ftp.ebi.ac.uk/pub/databases/genenames/hcop/human_all_hcop_sixteen_column.txt.gz'

# UniProt #
UNIPROT_SPROT = "ftp://ftp.uniprot.org/pub/databases/uniprot/" \
                "current_release/knowledgebase/complete/uniprot_sprot.xml.gz"
UNIPROT_HGNC = "https://www.genenames.org/cgi-bin/download/custom?col=gd_hgnc_id&col=gd_app_sym&col=md_prot_id&" \
               "status=Approved&status=Entry%20Withdrawn&hgnc_dbtag=on&order_by=gd_app_sym_sort&" \
               "format=text&submit=submit"
UNIPROT_MGI = "http://www.informatics.jax.org/downloads/reports/MRK_SwissProt.rpt"
UNIPROT_RGD = "https://download.rgd.mcw.edu/data_release/GENES_RAT.txt"
UNIPROT_FLYBASE = "ftp://ftp.flybase.org/releases/current/precomputed_files/genes/fbgn_NAseq_Uniprot_fb_2020_04.tsv.gz"

# Clinical Trials #
CLINICAL_TRIALS_GOV = "https://clinicaltrials.gov/AllPublicXML.zip"

# Genetic Variant DBs #
CLINVAR = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
# MIRTARBASE = "http://mirtarbase.cuhk.edu.cn/cache/download/8.0/miRTarBase_MTI.xlsx"
MIRTARBASE = "https://mirtarbase.cuhk.edu.cn/~miRTarBase/miRTarBase_2022/cache/download/9.0/miRTarBase_MTI.xlsx"
GWAS_CATALOG = "https://www.ebi.ac.uk/gwas/api/search/downloads/full"

# PPIs #
BIND = "https://www.bindingdb.org/bind/downloads/BindingDB_All_2018m7.tsv.zip"
BIOGRID = "https://downloads.thebiogrid.org/Download/BioGRID/Release-Archive/\
BIOGRID-4.4.211/BIOGRID-ALL-4.4.211.tab3.zip"
INTACT = "ftp://ftp.ebi.ac.uk/pub/databases/intact/current/psimitab/intact.zip"
STITCH = "http://stitch.embl.de/download/protein_chemical.links.transfer.v5.0.tsv.gz"

# String #
STRING_INTS = "https://stringdb-static.org/download/protein.links.full.v11.0/9606.protein.links.full.v11.5.txt.gz"
STRING_ACTIONS = "https://stringdb-static.org/download/protein.actions.v11.0/9606.protein.actions.v11.5.txt.gz"
STRING_NAMES = "https://stringdb-static.org/download/protein.info.v11.0/9606.protein.info.v11.5.txt.gz"

# Pathway DBs #
KEGG_PATH_LIST = "http://rest.kegg.jp/list/pathway/hsa"
PATHWAY_COMMONS = "https://www.pathwaycommons.org/archives/PC2/v12/PathwayCommons12.Detailed.hgnc.txt.gz"
REACTOME = "https://reactome.org/download/current/UniProt2Reactome.txt"
# TODO: Import from Reactome MySQL
# REACTOME MySQL has a strange database structure and no controlled vocabulary, reactions are not classified
# For that reason I will work later on that
# https://reactome.org/content/schema/DatabaseObject
# REACTOME_MYSQL = "https://reactome.org/download/current/databases/gk_current.sql.gz"
WIKIPATHWAYS = "http://data.wikipathways.org/20180710/gpml/wikipathways-20180710-gpml-Homo_sapiens.zip"

# Ensembl #
ENSEMBL_FASTA_PEP = "ftp://ftp.ensembl.org/pub/release-94/fasta/homo_sapiens/pep/Homo_sapiens.GRCh38.pep.all.fa.gz"
ENSEMBL_CDS = "ftp://ftp.ensembl.org/pub/release-96/fasta/homo_sapiens/cds/Homo_sapiens.GRCh38.cds.all.fa.gz"

# SIDER #
SIDER_ATC = "http://sideeffects.embl.de/media/download/drug_atc.tsv"
SIDER_SE = "http://sideeffects.embl.de/media/download/meddra_all_se.tsv.gz"

# Expression Atlas #
EXPRESSION_ATLAS_BASE = "ftp://ftp.ebi.ac.uk/pub/databases/microarray/data/atlas/experiments/"
EXPRESSION_ATLAS_EXPERIMENTS = EXPRESSION_ATLAS_BASE + "atlas-latest-data.tar.gz"

# DisGeNet #
DISGENET_BASE = "https://www.disgenet.org/static/disgenet_ap1/files/downloads/"
DISGENET_GDP_ASSOC = DISGENET_BASE + "all_gene_disease_pmid_associations.tsv.gz"
DISGENET_VDP_ASSOC = DISGENET_BASE + "all_variant_disease_pmid_associations.tsv.gz"

# Drugs and Side Effects #
OFFSIDES = "http://tatonettilab.org/resources/nsides/OFFSIDES.csv.xz"
ONSIDES = "https://github.com/tatonetti-lab/onsides/releases/download/v01/onsides_v01_20220430.tar.gz"
# DrugBank
DRUGBANK_VERSION = "https://go.drugbank.ca/releases/latest#full"
DRUGBANK_DATA = "https://go.drugbank.com/releases/{}/downloads/all-full-database"
# IUPHAR
IUPHAR_INT = "https://www.guidetopharmacology.org/DATA/interactions.csv"
IUPHAR_LIGANDS = "https://www.guidetopharmacology.org/DATA/ligands.csv"

# CHEBI #
CHEBI_BASE = "ftp://ftp.ebi.ac.uk/pub/databases/chebi/Flat_file_tab_delimited/"
CHEBI_CHEMICALDATA = f"{CHEBI_BASE}chemical_data.tsv"
CHEBI_COMMENT = f"{CHEBI_BASE}comments.tsv"
CHEBI_COMPOUND = f"{CHEBI_BASE}compounds.tsv.gz"
CHEBI_DATABASEACCESSION = f"{CHEBI_BASE}database_accession.tsv"
CHEBI_NAME = f"{CHEBI_BASE}names.tsv.gz"
CHEBI_REFERENCE = f"{CHEBI_BASE}reference.tsv.gz"
CHEBI_RELATION = f"{CHEBI_BASE}relation.tsv"
CHEBI_STRUCTURE = f"{CHEBI_BASE}structures.csv.gz"
CHEBI_INCHI = f"{CHEBI_BASE}chebiId_inchi.tsv"
# CHEBI_COMPOUNDORIGIN = f"{CHEBI_BASE}compound_origins.tsv"

# NCBI #
NCBI_PMID = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=ebel&" \
            "ids={}&idtype=pmid&versions=no&format=json"
NCBI_MESH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id="
# NCBI Gene
NCBI_GENE_INFO = "https://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"
NCBI_GENE_2ACCESSION = "https://ftp.ncbi.nih.gov/gene/DATA/gene2accession.gz"
NCBI_GENE_2ENSEMBL = "https://ftp.ncbi.nih.gov/gene/DATA/gene2ensembl.gz"
NCBI_GENE_2GO = "https://ftp.ncbi.nih.gov/gene/DATA/gene2go.gz"
NCBI_GENE_2MIM = "https://ftp.ncbi.nih.gov/gene/DATA/mim2gene_medgen"
NCBI_GENE_2PUBMED = "https://ftp.ncbi.nih.gov/gene/DATA/gene2pubmed.gz"
NCBI_GENE_ORTHOLOG = "https://ftp.ncbi.nih.gov/gene/DATA/gene_orthologs.gz"
NCBI_GENE_NEIGHBORS = "https://ftp.ncbi.nih.gov/gene/DATA/gene_neighbors.gz"
# NCBI MedGen
NCBI_GENE_MEDGEN_PUBMED = "https://ftp.ncbi.nlm.nih.gov/pub/medgen/medgen_pubmed_lnk.txt.gz"
NCBI_GENE_MEDGEN_NAMES = "https://ftp.ncbi.nlm.nih.gov/pub/medgen/NAMES.RRF.gz"

# Protein Atlas #
# https://www.proteinatlas.org/about/download
PROTEIN_ATLAS = "https://www.proteinatlas.org/download/"
PROTEIN_ATLAS_NORMAL_TISSUE = PROTEIN_ATLAS + "normal_tissue.tsv.zip"
PROTEIN_ATLAS_NORMAL_PATHOLOGY = PROTEIN_ATLAS + "pathology.tsv.zip"
PROTEIN_ATLAS_SUBCELLULAR_LOCATIO = PROTEIN_ATLAS + "subcellular_location.tsv.zip"
PROTEIN_ATLAS_RNA_CONSENSUS = PROTEIN_ATLAS + "rna_tissue_consensus.tsv.zip"
PROTEIN_ATLAS_RNA_GTEX_BRAIN = PROTEIN_ATLAS + "rna_brain_gtex.tsv.zip"
PROTEIN_ATLAS_RNA_FANTOM_BRAIN = PROTEIN_ATLAS + "rna_brain_fantom.tsv.zip"
PROTEIN_ATLAS_RNA_SINGLE = PROTEIN_ATLAS + "rna_single_cell_type.tsv.zip"
PROTEIN_ATLAS_RNA_MOUSE_BRAIN_ALLEN = PROTEIN_ATLAS + "rna_mouse_brain_allen.tsv.zip"
